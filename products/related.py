"""
TechZone — Module 5: Related Products Algorithm
================================================
Implements a scored, multi-signal recommendation engine:

Signal                       Weight
─────────────────────────────────────
Same brand + same category     50
Same category + price ±30%     30
Same category (any price)      20
Same brand (any category)      15
Frequently viewed together     40  (per shared pair-count point)
Popular in category            10  (per 100 views above average)
User browsing history          25  (appeared in same session)

All signals are additive. Products are sorted by total score descending.
Ties are broken by views_count.
"""

from django.db.models import Q, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Product, FrequentlyViewedTogether, ProductViewLog


# ─── public API ───────────────────────────────────────────────────────────────

def get_related_products(product, session_key=None, limit=8):
    """
    Return up to `limit` related Product objects, scored by multiple signals.
    """
    candidates = _build_candidate_pool(product)
    if not candidates:
        return []

    scores     = _score_candidates(candidates, product, session_key)
    sorted_pks = sorted(scores, key=lambda pk: (-scores[pk], ), )

    # Preserve DB ordering within each score bucket
    pk_list    = sorted_pks[:limit]
    obj_map    = {str(p.pk): p for p in candidates if str(p.pk) in pk_list}
    return [obj_map[pk] for pk in pk_list if pk in obj_map]


def get_frequently_viewed_together(product, limit=4):
    """
    Return products frequently viewed in the same session as `product`.
    """
    pairs_a = (FrequentlyViewedTogether.objects
               .filter(product_a=product)
               .select_related('product_b__brand')
               .prefetch_related('product_b__images')
               .order_by('-view_count')[:limit])
    pairs_b = (FrequentlyViewedTogether.objects
               .filter(product_b=product)
               .select_related('product_a__brand')
               .prefetch_related('product_a__images')
               .order_by('-view_count')[:limit])

    results, seen = [], {product.pk}
    for pair in list(pairs_a) + list(pairs_b):
        p = pair.product_b if pair.product_a_id == product.pk else pair.product_a
        if p.pk not in seen and p.is_active:
            results.append((p, pair.view_count))
            seen.add(p.pk)

    results.sort(key=lambda x: -x[1])
    return [p for p, _ in results[:limit]]


def get_popular_in_category(product, limit=4):
    """
    Return top products in the same category by views, excluding the current product.
    """
    return (Product.objects
            .filter(category=product.category, is_active=True)
            .exclude(pk=product.pk)
            .select_related('brand')
            .prefetch_related('images')
            .order_by('-views_count')[:limit])


def get_same_brand(product, limit=4):
    """Return other products from the same brand."""
    if not product.brand:
        return []
    return (Product.objects
            .filter(brand=product.brand, is_active=True)
            .exclude(pk=product.pk)
            .select_related('brand')
            .prefetch_related('images')
            .order_by('-is_featured', '-views_count')[:limit])


def record_view(product, request):
    """
    Log this product view and update FrequentlyViewedTogether pairs
    for other products seen in the same session in the last 30 minutes.
    """
    session_key = _get_or_create_session_key(request)
    if not session_key:
        return

    user = request.user if request.user.is_authenticated else None

    # Log the view (deduplicate within 5 minutes to avoid refresh spam)
    recent_cutoff = timezone.now() - timedelta(minutes=5)
    already_logged = ProductViewLog.objects.filter(
        product=product,
        session_key=session_key,
        viewed_at__gte=recent_cutoff
    ).exists()

    if not already_logged:
        ProductViewLog.objects.create(
            product=product,
            session_key=session_key,
            user=user
        )

    # Pair with other products viewed in this session in last 30 minutes
    session_cutoff = timezone.now() - timedelta(minutes=30)
    recent_pks = (ProductViewLog.objects
                  .filter(session_key=session_key, viewed_at__gte=session_cutoff)
                  .exclude(product=product)
                  .values_list('product_id', flat=True)
                  .distinct()[:10])

    for other_pk in recent_pks:
        try:
            other = Product.objects.get(pk=other_pk, is_active=True)
            FrequentlyViewedTogether.record(product, other)
        except Product.DoesNotExist:
            pass


# ─── internal helpers ─────────────────────────────────────────────────────────

def _build_candidate_pool(product):
    """
    Gather a diverse pool of candidate products from all signal sources.
    """
    ep  = float(product.effective_price) if product.effective_price else 0
    lo  = ep * 0.70
    hi  = ep * 1.40
    excluded = [product.pk]

    qs_same_cat  = (Product.objects.filter(category=product.category, is_active=True)
                    .exclude(pk__in=excluded).select_related('brand').prefetch_related('images')[:30])
    excluded += [p.pk for p in qs_same_cat]

    qs_price_match = []
    if ep:
        qs_price_match = (Product.objects
                          .filter(is_active=True, price__gte=lo, price__lte=hi)
                          .exclude(pk__in=excluded)
                          .select_related('brand').prefetch_related('images')[:20])
        excluded += [p.pk for p in qs_price_match]

    qs_same_brand = []
    if product.brand:
        qs_same_brand = (Product.objects.filter(brand=product.brand, is_active=True)
                         .exclude(pk__in=excluded).select_related('brand').prefetch_related('images')[:10])
        excluded += [p.pk for p in qs_same_brand]

    # Frequently viewed together
    fvt_pks = list(FrequentlyViewedTogether.objects
                   .filter(Q(product_a=product) | Q(product_b=product))
                   .values_list('product_a_id', 'product_b_id', 'view_count'))
    fvt_product_pks = []
    for a, b, _ in fvt_pks:
        pk = b if a == product.pk else a
        if pk not in excluded:
            fvt_product_pks.append(pk)
    qs_fvt = (Product.objects.filter(pk__in=fvt_product_pks, is_active=True)
              .select_related('brand').prefetch_related('images'))

    # Combine all pools
    seen, combined = set(), []
    for qs in [qs_same_cat, list(qs_price_match), list(qs_same_brand), list(qs_fvt)]:
        for p in qs:
            if p.pk not in seen:
                combined.append(p); seen.add(p.pk)

    return combined


def _score_candidates(candidates, product, session_key):
    """
    Assign a score to each candidate based on all signals.
    Returns dict {str(pk): score}.
    """
    ep            = float(product.effective_price) if product.effective_price else 0
    price_lo      = ep * 0.70
    price_hi      = ep * 1.40

    # Average views in same category (for popularity signal)
    avg_views     = (Product.objects
                     .filter(category=product.category, is_active=True)
                     .aggregate(avg=Avg('views_count'))['avg'] or 1)

    # Frequently viewed together counts
    fvt_counts    = {}
    for row in FrequentlyViewedTogether.objects.filter(
            Q(product_a=product) | Q(product_b=product)):
        pk = str(row.product_b_id) if row.product_a_id == product.pk else str(row.product_a_id)
        fvt_counts[pk] = row.view_count

    # Products viewed in same user session (recent 60 min)
    session_viewed_pks = set()
    if session_key:
        cutoff = timezone.now() - timedelta(minutes=60)
        session_viewed_pks = set(
            str(pk) for pk in
            ProductViewLog.objects
            .filter(session_key=session_key, viewed_at__gte=cutoff)
            .values_list('product_id', flat=True)
        )

    scores = {}
    for candidate in candidates:
        pk    = str(candidate.pk)
        score = 0

        # ── Signal 1: Same brand + same category (highest intent) ──
        if (product.brand and candidate.brand_id == product.brand_id
                and candidate.category_id == product.category_id):
            score += 50

        # ── Signal 2: Same category + similar price ──
        elif candidate.category_id == product.category_id:
            cep = float(candidate.effective_price) if candidate.effective_price else 0
            if ep and price_lo <= cep <= price_hi:
                score += 30
            else:
                score += 20

        # ── Signal 3: Same brand, different category ──
        elif product.brand and candidate.brand_id == product.brand_id:
            score += 15

        # ── Signal 4: Frequently viewed together ──
        if pk in fvt_counts:
            score += min(fvt_counts[pk] * 4, 40)   # cap at 40

        # ── Signal 5: Popularity within category ──
        if candidate.category_id == product.category_id and avg_views:
            popularity_bonus = (candidate.views_count / avg_views - 1) * 10
            score += max(0, min(popularity_bonus, 20))

        # ── Signal 6: Appeared in user's browsing session ──
        if pk in session_viewed_pks:
            score += 25

        # ── Signal 7: Featured / trending boost ──
        if candidate.is_featured:  score += 5
        if candidate.is_trending:  score += 5

        scores[pk] = round(score, 2)

    return scores


def _get_or_create_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

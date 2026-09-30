from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Min, Max
from django.urls import reverse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Product, Category, Review, ProductInquiry
from .forms import ReviewForm, ProductInquiryForm
from .compare import MAX_COMPARE, build_comparison, parse_ids
from .related import (
    get_related_products,
    get_frequently_viewed_together,
    get_popular_in_category,
    get_same_brand,
    record_view,
)
from core.models import Brand
from core.branding import get_site_name
from core.notifications import notify_staff
from core.ratelimit import protect_form


# ─── filter helpers ───────────────────────────────────────────────────────────
# Infinite scroll: the page opens with FIRST_BATCH products, and every time the
# visitor scrolls to the end of the grid, product-filters.js asks ajax_filter for
# the next NEXT_BATCH, starting at `offset`.
FIRST_BATCH = 12
NEXT_BATCH  = 8


def _batch(qs, params):
    """Slice one infinite-scroll batch out of `qs`.

    Returns (products, total, next_offset); next_offset is None when nothing is left.
    """
    try:
        offset = max(int(params.get('offset', 0)), 0)
    except (TypeError, ValueError):
        offset = 0
    size     = FIRST_BATCH if offset == 0 else NEXT_BATCH
    total    = qs.count()
    products = list(qs[offset:offset + size])
    end      = offset + len(products)
    return products, total, (end if end < total else None)


def _apply_filters(qs, params):
    q         = params.get('q', '').strip()
    # `scope_cat` is the category a page is locked to (the category route);
    # `category` is the narrowing the visitor picked inside the filter panel.
    # Falling back here is what lets one AJAX endpoint serve both routes.
    cat_slug  = params.get('category', '').strip() or params.get('scope_cat', '').strip()
    brand_ids = params.getlist('brand')
    min_price = params.get('min_price', '')
    max_price = params.get('max_price', '')
    in_stock  = params.get('in_stock', '')
    on_sale   = params.get('on_sale', '')
    condition = params.get('condition', '')
    new_arr   = params.get('new_arrival', '')
    colors    = params.getlist('color')
    min_rat   = params.get('min_rating', '')
    min_disc  = params.get('min_discount', '')
    sort      = params.get('sort', '-created_at')

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(short_description__icontains=q) |
                       Q(brand__name__icontains=q) | Q(sku__icontains=q) |
                       Q(category__name__icontains=q))
    if cat_slug:
        cat = Category.objects.filter(slug=cat_slug, is_active=True).first()
        if cat:
            ids = [cat.pk] + [c.pk for c in cat.get_all_descendants()]
            qs  = qs.filter(category_id__in=ids)
    if brand_ids: qs = qs.filter(brand_id__in=brand_ids)
    if min_price:
        try: qs = qs.filter(price__gte=float(min_price))
        except ValueError: pass
    if max_price:
        try: qs = qs.filter(price__lte=float(max_price))
        except ValueError: pass
    if in_stock:   qs = qs.filter(stock__gt=0)
    if on_sale:    qs = qs.filter(sale_price__isnull=False)
    if condition:  qs = qs.filter(condition=condition)
    if new_arr:    qs = qs.filter(is_new_arrival=True)
    if colors:     qs = qs.filter(color__in=colors)
    if min_rat:
        try:
            rated = [p.pk for p in qs if p.average_rating >= float(min_rat)]
            qs = qs.filter(pk__in=rated)
        except ValueError: pass
    if min_disc:
        try:
            pct   = float(min_disc)
            valid = [p.pk for p in qs.filter(sale_price__isnull=False) if p.discount_percent >= pct]
            qs    = qs.filter(pk__in=valid)
        except ValueError: pass

    valid = {'-created_at', 'price', '-price', 'name', '-name', '-views_count'}
    return qs.order_by(sort if sort in valid else '-created_at'), sort


def _color_labels(base_qs):
    """Normalized, deduplicated colour labels (trimmed, case-insensitive)."""
    labels, seen = [], set()
    for c in base_qs.exclude(color='').values_list('color', flat=True):
        norm = (c or '').strip().lower()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        labels.append(c.strip())
    return labels


def _sidebar_context(base_qs, params, brands_qs=None):
    """Facet data the shared filter panel renders, scoped to `base_qs`.

    `brands_qs` lets the category route narrow the brand list to brands that
    actually appear in that category; the all-products route passes nothing.
    """
    if brands_qs is None:
        brands_qs = Brand.objects.filter(is_active=True).order_by('name')
    return dict(
        price_range     = base_qs.aggregate(min_price=Min('price'), max_price=Max('price')),
        sidebar_brands  = brands_qs,
        in_stock_count  = base_qs.filter(stock__gt=0).count(),
        on_sale_count   = base_qs.filter(sale_price__isnull=False).count(),
        new_count       = base_qs.filter(is_new_arrival=True).count(),
        color_list      = _color_labels(base_qs),
        selected_brands = params.getlist('brand'),
        selected_colors = params.getlist('color'),
    )


def _filter_config(params, category=None):
    """Route-specific configuration for products/partials/filter_panel.html.

    Pass `category` on the category route: the panel then pins every request to
    that category with a hidden `scope_cat` field and offers its sub-categories
    for drilling down, instead of the whole category tree.
    """
    if category is not None:
        subs = category.children.filter(is_active=True).prefetch_related('children')
        cfg  = dict(
            scope_cat     = category.slug,
            show_category = subs.exists(),
            cat_all_label = f'All {category.name}',
            cat_options   = subs,
            clear_url     = category.get_absolute_url(),
        )
    else:
        cfg = dict(
            scope_cat     = '',
            show_category = True,
            cat_all_label = 'All Categories',
            cat_options   = Category.objects.filter(is_active=True, parent=None).prefetch_related('children'),
            clear_url     = reverse('products:list'),
        )
    cfg['current_category'] = params.get('category', '').strip()
    return cfg


def _active_chips(params, brands_qs):
    chips = []
    if params.get('q'):            chips.append({'label': f'Search: {params["q"]}',            'key': 'q',           'val': ''})
    if params.get('in_stock'):     chips.append({'label': 'In Stock',                           'key': 'in_stock',    'val': ''})
    if params.get('on_sale'):      chips.append({'label': 'On Sale',                            'key': 'on_sale',     'val': ''})
    if params.get('new_arrival'):  chips.append({'label': 'New Arrivals',                       'key': 'new_arrival', 'val': ''})
    if params.get('condition'):
        lbl = {'new': 'New', 'refurbished': 'Refurbished', 'open_box': 'Open Box'}.get(params['condition'], params['condition'])
        chips.append({'label': f'Condition: {lbl}', 'key': 'condition', 'val': ''})
    if params.get('min_price') or params.get('max_price'):
        mn = params.get('min_price', ''); mx = params.get('max_price', '')
        chips.append({'label': f'Price: ₹{mn or "0"}–₹{mx or "∞"}', 'key': 'price_range', 'val': ''})
    if params.get('min_rating'):   chips.append({'label': f'{params["min_rating"]}★ & above',  'key': 'min_rating',  'val': ''})
    if params.get('min_discount'): chips.append({'label': f'{params["min_discount"]}%+ Discount', 'key': 'min_discount', 'val': ''})
    if params.get('category'):
        cat = Category.objects.filter(slug=params['category']).first()
        if cat: chips.append({'label': f'Category: {cat.name}', 'key': 'category', 'val': ''})
    for bid in params.getlist('brand'):
        b = brands_qs.filter(pk=bid).first()
        if b: chips.append({'label': f'Brand: {b.name}', 'key': 'brand', 'val': bid})
    for color in params.getlist('color'):
        chips.append({'label': f'Color: {color}', 'key': 'color', 'val': color})
    return chips


# ─── product list ─────────────────────────────────────────────────────────────
def product_list(request):
    base_qs  = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images', 'reviews')
    qs, sort = _apply_filters(base_qs, request.GET)
    ctx      = _sidebar_context(base_qs, request.GET)
    config   = _filter_config(request.GET)
    chips    = _active_chips(request.GET, ctx['sidebar_brands'])
    products, total, next_offset = _batch(qs, {})       # a full page load always starts at the top
    ctx.update(products=products, sort=sort, q=request.GET.get('q', ''),
               total_count=total, next_offset=next_offset, next_batch=NEXT_BATCH, active_chips=chips,
               page_title='All Products',
               filter_config=config, clear_url=config['clear_url'],
               meta_description=f'Browse premium electronics at {get_site_name()}.')
    return render(request, 'products/list.html', ctx)


# ─── AJAX filter ──────────────────────────────────────────────────────────────
def ajax_filter(request):
    """Serves every route that embeds the shared filter panel.

    The panel sends `scope_cat` when the page is pinned to a category, so no
    per-route endpoint is needed: _apply_filters resolves the scope, and the
    chips / "Clear all" link follow the same scope.

    offset=0 (a filter change) returns the whole grid plus chips; offset>0
    (infinite scroll) returns only the next batch of cards, to be appended.
    """
    base_qs  = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images', 'reviews')
    qs, _    = _apply_filters(base_qs, request.GET)
    products, total, next_offset = _batch(qs, request.GET)

    if request.GET.get('offset', '0') not in ('', '0'):
        cards_html = ''.join(render_to_string('products/partials/product_card.html', {'product': p}, request=request)
                             for p in products)
        return JsonResponse({'html': cards_html, 'append': True, 'count': total, 'next_offset': next_offset})

    scope_slug = request.GET.get('scope_cat', '').strip()
    scope_cat  = Category.objects.filter(slug=scope_slug, is_active=True).first() if scope_slug else None
    clear_url  = scope_cat.get_absolute_url() if scope_cat else reverse('products:list')

    chips = _active_chips(request.GET, Brand.objects.filter(is_active=True))

    grid_html  = render_to_string('products/partials/product_grid.html',
                                  {'products': products, 'clear_url': clear_url, 'active_chips': chips,
                                   'category': scope_cat}, request=request)
    more_html  = render_to_string('products/partials/load_more.html',
                                  {'next_offset': next_offset, 'next_batch': NEXT_BATCH, 'total_count': total}, request=request)
    chips_html = render_to_string('products/partials/filter_chips.html',
                                 {'active_chips': chips, 'clear_url': clear_url}, request=request)
    return JsonResponse({'html': grid_html, 'load_more': more_html, 'chips': chips_html,
                         'count': total, 'next_offset': next_offset})


# ─── quick view ───────────────────────────────────────────────────────────────
def quick_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'products/partials/quick_view.html', {'product': product})


# ─── wishlist ─────────────────────────────────────────────────────────────────
# Saved in the visitor's browser (localStorage 'tzWishlist', see product-card.js),
# so it works without an account. This page renders whatever ids the browser sends.
def wishlist_page(request):
    ids = parse_ids(request.GET.getlist('ids'), limit=60)
    found = {p.pk: p for p in (Product.objects.filter(pk__in=ids, is_active=True)
                               .select_related('category', 'brand').prefetch_related('images', 'reviews'))}
    products = [found[pk] for pk in ids if pk in found]      # keep the order they were saved in
    return render(request, 'products/wishlist.html', {
        'products': products,
        'has_ids': bool(request.GET.getlist('ids')),
        'page_title': 'My Wishlist',
    })


# ─── compare ──────────────────────────────────────────────────────────────────
def compare_products(request):
    comparison = build_comparison(parse_ids(request.GET.getlist('ids'), limit=MAX_COMPARE))
    products   = comparison['products']
    return render(request, 'products/compare.html', {
        **comparison,
        'can_add_more': len(products) < MAX_COMPARE,
        # Lets compare.js resync localStorage with what's actually shown.
        'compare_items': [{'id': str(p.pk), 'name': p.name} for p in products],
        'page_title': 'Compare Products',
    })


# ─── category detail ──────────────────────────────────────────────────────────
def category_detail(request, slug):
    category  = get_object_or_404(Category, slug=slug, is_active=True)
    all_ids   = [category.pk] + [c.pk for c in category.get_all_descendants()]
    base_qs   = (Product.objects.filter(category_id__in=all_ids, is_active=True)
                 .select_related('category', 'brand').prefetch_related('images', 'reviews'))
    qs, sort  = _apply_filters(base_qs, request.GET)
    brands    = Brand.objects.filter(products__category_id__in=all_ids, is_active=True).distinct().order_by('name')

    ctx    = _sidebar_context(base_qs, request.GET, brands_qs=brands)
    config = _filter_config(request.GET, category=category)
    products, total, next_offset = _batch(qs, {})

    ctx.update({
        'category': category,
        'products': products,
        'subcategories': category.children.filter(is_active=True),
        'siblings': category.get_siblings(),
        'breadcrumbs': category.get_breadcrumbs(),
        'brands': brands,
        'sort': sort,
        'total_count': total,
        'next_offset': next_offset,
        'next_batch': NEXT_BATCH,
        'active_chips': _active_chips(request.GET, brands),
        'filter_config': config,
        'clear_url': config['clear_url'],
        'page_title': category.name,
        'meta_description': category.meta_description or category.description,
    })
    return render(request, 'products/category.html', ctx)


# ─── categories overview ──────────────────────────────────────────────────────
def categories_overview(request):
    return render(request, 'products/categories.html', {
        'root_categories': Category.objects.filter(is_active=True, parent=None).prefetch_related('children').order_by('order', 'name'),
        'page_title': 'All Categories',
    })


# ══════════════════════════════════════════════════════════════════
# MODULE 4 + 5 — PRODUCT DETAIL
# ══════════════════════════════════════════════════════════════════
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)

    # Increment views count
    Product.objects.filter(pk=product.pk).update(views_count=product.views_count + 1)

    # ── Module 5: record view + update FVT pairs ──────────────────
    record_view(product, request)

    # ── Module 5: multi-signal related products ───────────────────
    session_key      = request.session.session_key
    related_products = get_related_products(product, session_key=session_key, limit=8)
    fvt_products     = get_frequently_viewed_together(product, limit=4)
    popular_products = list(get_popular_in_category(product, limit=4))
    same_brand_products = list(get_same_brand(product, limit=4))

    # ── Reviews + rating distribution ────────────────────────────
    reviews    = product.reviews.filter(is_approved=True).prefetch_related('images')
    rating_dist = product.get_rating_distribution()

    # ── Forms ─────────────────────────────────────────────────────
    review_form  = ReviewForm()
    inquiry_form = ProductInquiryForm()

    # ── Breadcrumbs ───────────────────────────────────────────────
    breadcrumbs = product.category.get_breadcrumbs() + [(product.name, None)]

    # ── Session-based recently viewed ────────────────────────────
    rv     = request.session.get('recently_viewed', [])
    str_pk = str(product.pk)
    if str_pk in rv: rv.remove(str_pk)
    rv.insert(0, str_pk)
    request.session['recently_viewed'] = rv[:10]
    recently_viewed = (Product.objects.filter(pk__in=rv[:6], is_active=True)
                       .exclude(pk=product.pk)
                       .select_related('brand').prefetch_related('images'))

    return render(request, 'products/detail.html', {
        'product':              product,
        'related_products':     related_products,
        'fvt_products':         fvt_products,
        'popular_products':     popular_products,
        'same_brand_products':  same_brand_products,
        'reviews':              reviews,
        'rating_dist':          rating_dist,
        'review_form':          review_form,
        'inquiry_form':         inquiry_form,
        'breadcrumbs':          breadcrumbs,
        'recently_viewed':      recently_viewed,
        'page_title':           product.meta_title or product.name,
        'meta_description':     product.meta_description or product.short_description,
        'meta_keywords':        product.meta_keywords,
    })


# ─── submit review ────────────────────────────────────────────────────────────
@require_POST
@protect_form('review')
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    form    = ReviewForm(request.POST)
    if form.is_valid():
        review         = form.save(commit=False)
        review.product = product
        if request.user.is_authenticated:
            review.user = request.user
        review.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Thank you! Your review is pending approval.'})
        messages.success(request, 'Review submitted — pending approval.')
        return __import__('django.shortcuts', fromlist=['redirect']).redirect(product.get_absolute_url() + '#reviews')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors, 'message': 'Please fix the errors below.'})
    return __import__('django.shortcuts', fromlist=['redirect']).redirect(product.get_absolute_url() + '#reviews')


def notify_product_inquiry(inquiry, request):
    """Email the shop about a new product enquiry (best-effort). Also used by the API."""
    product = inquiry.product
    notify_staff(
        subject=f'[{get_site_name()}] Product enquiry: {product.name}',
        message=(f'{inquiry.name} ({inquiry.email}, {inquiry.phone}) asked about '
                 f'{product.name} ({request.build_absolute_uri(product.get_absolute_url())}):\n\n'
                 f'{inquiry.message}\n\nManage it in the admin: Products -> Product inquiries.'),
        reply_to=inquiry.email,
    )


# ─── submit inquiry ───────────────────────────────────────────────────────────
@require_POST
@protect_form('product-inquiry')
def submit_inquiry(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    form    = ProductInquiryForm(request.POST)
    if form.is_valid():
        inquiry         = form.save(commit=False)
        inquiry.product = product
        inquiry.save()
        notify_product_inquiry(inquiry, request)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Enquiry sent! We will respond within 24 hours.'})
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors, 'message': 'Please fix the errors below.'})
    from django.shortcuts import redirect
    return redirect(product.get_absolute_url())


# ─── mark review helpful ──────────────────────────────────────────────────────
@require_POST
@protect_form('helpful', rate='30/10m')
def mark_helpful(request, review_id):
    review = get_object_or_404(Review, pk=review_id, is_approved=True)
    key    = f'helpful_{review_id}'
    if not request.session.get(key):
        review.helpful_count += 1
        review.save(update_fields=['helpful_count'])
        request.session[key] = True
    return JsonResponse({'helpful_count': review.helpful_count})


# ─── AJAX: related products for a product (used by detail page JS) ────────────
def ajax_related(request, slug):
    product          = get_object_or_404(Product, slug=slug, is_active=True)
    session_key      = request.session.session_key
    related_products = get_related_products(product, session_key=session_key, limit=8)
    html = render_to_string('products/partials/related_row.html', {'products': related_products}, request=request)
    return JsonResponse({'html': html, 'count': len(related_products)})

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Product, Category, Review, Wishlist, ProductInquiry
from .forms import ReviewForm, ProductInquiryForm
from .related import (
    get_related_products,
    get_frequently_viewed_together,
    get_popular_in_category,
    get_same_brand,
    record_view,
)
from core.models import Brand
import json


# ─── filter helpers ───────────────────────────────────────────────────────────
def _apply_filters(qs, params):
    q         = params.get('q', '').strip()
    cat_slug  = params.get('category', '')
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


def _sidebar_context(base_qs, params):
    # Build a normalized, deduplicated list of color labels (trimmed, case-insensitive)
    raw_colors = base_qs.exclude(color='').values_list('color', flat=True)
    color_list = []
    _seen = set()
    for c in raw_colors:
        if not c:
            continue
        norm = c.strip().lower()
        if not norm or norm in _seen:
            continue
        _seen.add(norm)
        color_list.append(c.strip())

    return dict(
        price_range     = base_qs.aggregate(min_price=Min('price'), max_price=Max('price')),
        sidebar_brands  = Brand.objects.filter(is_active=True).order_by('name'),
        root_cats       = Category.objects.filter(is_active=True, parent=None).prefetch_related('children'),
        in_stock_count  = base_qs.filter(stock__gt=0).count(),
        on_sale_count   = base_qs.filter(sale_price__isnull=False).count(),
        new_count       = base_qs.filter(is_new_arrival=True).count(),
        color_list      = color_list,
        selected_brands = params.getlist('brand'),
        selected_colors = params.getlist('color'),
    )


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
    per_page = int(request.GET.get('per_page', 12))
    per_page = per_page if per_page in (12, 24, 48) else 12
    base_qs  = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images', 'reviews')
    qs, sort = _apply_filters(base_qs, request.GET)
    ctx      = _sidebar_context(base_qs, request.GET)
    chips    = _active_chips(request.GET, ctx['sidebar_brands'])
    paginator = Paginator(qs, per_page)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    ctx.update(products=page_obj, sort=sort, q=request.GET.get('q', ''),
               total_count=paginator.count, active_chips=chips, per_page=per_page,
               view_mode=request.GET.get('view', 'grid'), page_title='All Products',
               meta_description='Browse premium electronics at TechZone.')
    return render(request, 'products/list.html', ctx)


# ─── AJAX filter ──────────────────────────────────────────────────────────────
def ajax_filter(request):
    per_page = int(request.GET.get('per_page', 12))
    per_page = per_page if per_page in (12, 24, 48) else 12
    base_qs  = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images', 'reviews')
    qs, _    = _apply_filters(base_qs, request.GET)
    paginator = Paginator(qs, per_page)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    view_mode = request.GET.get('view', 'grid')
    grid_html = render_to_string('products/partials/product_grid.html', {'products': page_obj, 'view_mode': view_mode}, request=request)
    pag_html  = render_to_string('products/partials/pagination.html',   {'products': page_obj, 'request': request}, request=request)
    return JsonResponse({'html': grid_html, 'pagination': pag_html, 'count': paginator.count, 'num_pages': paginator.num_pages, 'page': page_obj.number})


# ─── quick view ───────────────────────────────────────────────────────────────
def quick_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'products/partials/quick_view.html', {'product': product})


# ─── wishlist ─────────────────────────────────────────────────────────────────
@login_required
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        return JsonResponse({'status': 'removed', 'message': 'Removed from wishlist'})
    return JsonResponse({'status': 'added', 'message': 'Added to wishlist'})


# ─── compare ──────────────────────────────────────────────────────────────────
def compare_products(request):
    ids      = request.GET.getlist('ids')[:3]
    products = list(Product.objects.filter(pk__in=ids, is_active=True).prefetch_related('images', 'attributes__attribute'))
    all_attrs = sorted({av.attribute.name for p in products for av in p.attributes.all()})
    matrix    = {attr: {str(p.pk): (p.attributes.filter(attribute__name=attr).first().value
                 if p.attributes.filter(attribute__name=attr).exists() else '—') for p in products} for attr in all_attrs}
    return render(request, 'products/compare.html', {
        'products': products, 'matrix': matrix,
        'all_attrs': all_attrs, 'matrix_json': json.dumps(matrix), 'page_title': 'Compare Products'
    })


# ─── category detail ──────────────────────────────────────────────────────────
def category_detail(request, slug):
    category  = get_object_or_404(Category, slug=slug, is_active=True)
    desc_ids  = [c.pk for c in category.get_all_descendants()]
    all_ids   = [category.pk] + desc_ids
    per_page  = int(request.GET.get('per_page', 12))
    per_page  = per_page if per_page in (12, 24, 48) else 12
    base_qs   = Product.objects.filter(category_id__in=all_ids, is_active=True).select_related('brand').prefetch_related('images', 'reviews')
    qs, sort  = _apply_filters(base_qs, request.GET)
    price_range   = base_qs.aggregate(min_price=Min('price'), max_price=Max('price'))
    brands        = Brand.objects.filter(products__category_id__in=all_ids, is_active=True).distinct()
    paginator     = Paginator(qs, per_page)
    page_obj      = paginator.get_page(request.GET.get('page', 1))
    chips         = _active_chips(request.GET, brands)
    # Deduplicate color labels for the sidebar (trim + case-insensitive)
    raw_colors = base_qs.exclude(color='').values_list('color', flat=True)
    colors = []
    _seen = set()
    for c in raw_colors:
        if not c:
            continue
        norm = c.strip().lower()
        if not norm or norm in _seen:
            continue
        _seen.add(norm)
        colors.append(c.strip())

    return render(request, 'products/category.html', {
        'category': category, 
        'products': page_obj,
        'subcategories': category.children.filter(is_active=True),
        'siblings': category.get_siblings(), 'breadcrumbs': category.get_breadcrumbs(),
        'brands': brands, 'sidebar_brands': brands, 'price_range': price_range,
        'sort': sort, 'total_count': paginator.count,
        'in_stock_count': base_qs.filter(stock__gt=0).count(),
        'on_sale_count':  base_qs.filter(sale_price__isnull=False).count(),
        'active_chips': chips, 'per_page': per_page,
        'view_mode': request.GET.get('view', 'grid'),
        'color_list': colors,
        'selected_brands': request.GET.getlist('brand'),
        'selected_colors': request.GET.getlist('color'),
        'root_cats': Category.objects.filter(is_active=True, parent=None).prefetch_related('children'),
        'page_title': category.name,
        'meta_description': category.meta_description or category.description,
    })


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

    # ── Wishlist state ────────────────────────────────────────────
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

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
        'in_wishlist':          in_wishlist,
        'page_title':           product.meta_title or product.name,
        'meta_description':     product.meta_description or product.short_description,
        'meta_keywords':        product.meta_keywords,
    })


# ─── submit review ────────────────────────────────────────────────────────────
@require_POST
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


# ─── submit inquiry ───────────────────────────────────────────────────────────
@require_POST
def submit_inquiry(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    form    = ProductInquiryForm(request.POST)
    if form.is_valid():
        inquiry         = form.save(commit=False)
        inquiry.product = product
        inquiry.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Enquiry sent! We will respond within 24 hours.'})
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Please fill all required fields.'})
    from django.shortcuts import redirect
    return redirect(product.get_absolute_url())


# ─── mark review helpful ──────────────────────────────────────────────────────
@require_POST
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

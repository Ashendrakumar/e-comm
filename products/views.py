from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max, Avg, Count
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from .models import (Product, Category, Review, Wishlist, ProductAttributeValue,
                     ProductInquiry, StockAlert)
from core.models import Brand
import json


# ─── shared helpers ───────────────────────────────────────────────────────────

def _apply_filters(qs, params):
    q          = params.get('q', '').strip()
    cat_slug   = params.get('category', '')
    brand_ids  = params.getlist('brand')
    min_price  = params.get('min_price', '')
    max_price  = params.get('max_price', '')
    in_stock   = params.get('in_stock', '')
    on_sale    = params.get('on_sale', '')
    condition  = params.get('condition', '')
    new_arr    = params.get('new_arrival', '')
    colors     = params.getlist('color')
    min_rating = params.get('min_rating', '')
    min_disc   = params.get('min_discount', '')
    sort       = params.get('sort', '-created_at')

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(short_description__icontains=q) |
            Q(brand__name__icontains=q) |
            Q(sku__icontains=q) |
            Q(category__name__icontains=q)
        )
    if cat_slug:
        cat = Category.objects.filter(slug=cat_slug, is_active=True).first()
        if cat:
            ids = [cat.pk] + [c.pk for c in cat.get_all_descendants()]
            qs  = qs.filter(category_id__in=ids)
    if brand_ids:
        qs = qs.filter(brand_id__in=brand_ids)
    if min_price:
        try: qs = qs.filter(price__gte=float(min_price))
        except ValueError: pass
    if max_price:
        try: qs = qs.filter(price__lte=float(max_price))
        except ValueError: pass
    if in_stock:
        qs = qs.filter(stock__gt=0)
    if on_sale:
        qs = qs.filter(sale_price__isnull=False)
    if condition:
        qs = qs.filter(condition=condition)
    if new_arr:
        qs = qs.filter(is_new_arrival=True)
    if colors:
        qs = qs.filter(color__in=colors)
    if min_rating:
        try:
            # Filter products whose avg review rating >= min_rating
            rated_pks = [
                p.pk for p in qs
                if p.average_rating >= float(min_rating)
            ]
            qs = qs.filter(pk__in=rated_pks)
        except ValueError:
            pass
    if min_disc:
        try:
            pct = float(min_disc)
            # discount_percent computed from price/sale_price
            valid_pks = []
            for p in qs.filter(sale_price__isnull=False):
                if p.discount_percent >= pct:
                    valid_pks.append(p.pk)
            qs = qs.filter(pk__in=valid_pks)
        except ValueError:
            pass

    valid = {'-created_at', 'price', '-price', 'name', '-name', '-views_count'}
    qs = qs.order_by(sort if sort in valid else '-created_at')
    return qs, sort


def _sidebar_context(base_qs, params):
    price_range    = base_qs.aggregate(min_price=Min('price'), max_price=Max('price'))
    sidebar_brands = Brand.objects.filter(is_active=True).order_by('name')
    root_cats      = Category.objects.filter(is_active=True, parent=None).prefetch_related('children')
    in_stock_count = base_qs.filter(stock__gt=0).count()
    on_sale_count  = base_qs.filter(sale_price__isnull=False).count()
    new_count      = base_qs.filter(is_new_arrival=True).count()
    # Distinct colors from products
    color_list = (base_qs.exclude(color='').values_list('color', flat=True).distinct().order_by('color'))
    selected_brands = params.getlist('brand')
    selected_colors = params.getlist('color')
    return dict(
        price_range     = price_range,
        sidebar_brands  = sidebar_brands,
        root_cats       = root_cats,
        in_stock_count  = in_stock_count,
        on_sale_count   = on_sale_count,
        new_count       = new_count,
        color_list      = list(color_list),
        selected_brands = selected_brands,
        selected_colors = selected_colors,
    )


def _active_chips(params, brands_qs):
    chips = []
    if params.get('q'):
        chips.append({'label': f'Search: {params["q"]}', 'key': 'q', 'val': ''})
    if params.get('in_stock'):
        chips.append({'label': 'In Stock Only', 'key': 'in_stock', 'val': ''})
    if params.get('on_sale'):
        chips.append({'label': 'On Sale', 'key': 'on_sale', 'val': ''})
    if params.get('new_arrival'):
        chips.append({'label': 'New Arrivals', 'key': 'new_arrival', 'val': ''})
    if params.get('condition'):
        lbl = {'new': 'New', 'refurbished': 'Refurbished', 'open_box': 'Open Box'}.get(params['condition'], params['condition'])
        chips.append({'label': f'Condition: {lbl}', 'key': 'condition', 'val': ''})
    if params.get('min_price') or params.get('max_price'):
        mn = params.get('min_price', ''); mx = params.get('max_price', '')
        chips.append({'label': f'Price: ₹{mn or "0"}–₹{mx or "∞"}', 'key': 'price_range', 'val': ''})
    if params.get('min_rating'):
        chips.append({'label': f'{params["min_rating"]}★ & above', 'key': 'min_rating', 'val': ''})
    if params.get('min_discount'):
        chips.append({'label': f'{params["min_discount"]}%+ Discount', 'key': 'min_discount', 'val': ''})
    if params.get('category'):
        cat = Category.objects.filter(slug=params['category']).first()
        if cat:
            chips.append({'label': f'Category: {cat.name}', 'key': 'category', 'val': ''})
    for bid in params.getlist('brand'):
        b = brands_qs.filter(pk=bid).first()
        if b:
            chips.append({'label': f'Brand: {b.name}', 'key': 'brand', 'val': bid})
    for color in params.getlist('color'):
        chips.append({'label': f'Color: {color}', 'key': 'color', 'val': color})
    return chips


# ─── Product List ──────────────────────────────────────────────────────────────

def product_list(request):
    per_page = int(request.GET.get('per_page', 12))
    per_page = per_page if per_page in (12, 24, 48) else 12

    base_qs  = (Product.objects.filter(is_active=True)
                .select_related('category', 'brand')
                .prefetch_related('images', 'reviews'))
    qs, sort = _apply_filters(base_qs, request.GET)
    ctx      = _sidebar_context(base_qs, request.GET)
    chips    = _active_chips(request.GET, ctx['sidebar_brands'])

    paginator = Paginator(qs, per_page)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    ctx.update(dict(
        products         = page_obj,
        sort             = sort,
        q                = request.GET.get('q', ''),
        total_count      = paginator.count,
        active_chips     = chips,
        per_page         = per_page,
        view_mode        = request.GET.get('view', 'grid'),
        page_title       = 'All Products',
        meta_description = 'Browse premium electronics at TechZone.',
    ))
    return render(request, 'products/list.html', ctx)


# ─── AJAX Filter ──────────────────────────────────────────────────────────────

def ajax_filter(request):
    per_page = int(request.GET.get('per_page', 12))
    per_page = per_page if per_page in (12, 24, 48) else 12

    base_qs  = (Product.objects.filter(is_active=True)
                .select_related('category', 'brand')
                .prefetch_related('images', 'reviews'))
    qs, _    = _apply_filters(base_qs, request.GET)
    paginator = Paginator(qs, per_page)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    view_mode = request.GET.get('view', 'grid')

    grid_html = render_to_string(
        'products/partials/product_grid.html',
        {'products': page_obj, 'view_mode': view_mode},
        request=request,
    )
    pag_html = render_to_string(
        'products/partials/pagination.html',
        {'products': page_obj, 'request': request},
        request=request,
    )
    return JsonResponse({
        'html':       grid_html,
        'pagination': pag_html,
        'count':      paginator.count,
        'num_pages':  paginator.num_pages,
        'page':       page_obj.number,
    })


# ─── Quick View ────────────────────────────────────────────────────────────────

def quick_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'products/partials/quick_view.html', {'product': product})


# ─── Wishlist ──────────────────────────────────────────────────────────────────

@login_required
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        return JsonResponse({'status': 'removed', 'message': 'Removed from wishlist'})
    return JsonResponse({'status': 'added', 'message': 'Added to wishlist'})


# ─── Compare ──────────────────────────────────────────────────────────────────

def compare_products(request):
    ids      = request.GET.getlist('ids')[:3]
    products = list(
        Product.objects.filter(pk__in=ids, is_active=True)
        .prefetch_related('images', 'attributes__attribute')
    )
    all_attrs = sorted({
        av.attribute.name
        for p in products
        for av in p.attributes.all()
    })
    matrix = {}
    for attr in all_attrs:
        matrix[attr] = {}
        for p in products:
            av = p.attributes.filter(attribute__name=attr).first()
            matrix[attr][str(p.pk)] = av.value if av else '—'

    return render(request, 'products/compare.html', {
        'products':    products,
        'matrix':      matrix,
        'all_attrs':   all_attrs,
        'matrix_json': json.dumps(matrix),
        'page_title':  'Compare Products',
    })


# ─── Category Detail ──────────────────────────────────────────────────────────

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    desc_ids = [c.pk for c in category.get_all_descendants()]
    all_ids  = [category.pk] + desc_ids
    per_page = int(request.GET.get('per_page', 12))
    per_page = per_page if per_page in (12, 24, 48) else 12

    base_qs = (Product.objects.filter(category_id__in=all_ids, is_active=True)
               .select_related('brand').prefetch_related('images', 'reviews'))
    qs, sort = _apply_filters(base_qs, request.GET)

    price_range    = base_qs.aggregate(min_price=Min('price'), max_price=Max('price'))
    brands         = Brand.objects.filter(products__category_id__in=all_ids, is_active=True).distinct()
    subcategories  = category.children.filter(is_active=True)
    siblings       = category.get_siblings()
    breadcrumbs    = category.get_breadcrumbs()
    paginator      = Paginator(qs, per_page)
    page_obj       = paginator.get_page(request.GET.get('page', 1))
    in_stock_count = base_qs.filter(stock__gt=0).count()
    on_sale_count  = base_qs.filter(sale_price__isnull=False).count()
    color_list     = list(base_qs.exclude(color='').values_list('color', flat=True).distinct())
    chips          = _active_chips(request.GET, brands)

    return render(request, 'products/category.html', {
        'category': category, 'products': page_obj,
        'subcategories': subcategories, 'siblings': siblings,
        'breadcrumbs': breadcrumbs, 'brands': brands,
        'sidebar_brands': brands,
        'price_range': price_range, 'sort': sort,
        'total_count': paginator.count,
        'in_stock_count': in_stock_count, 'on_sale_count': on_sale_count,
        'active_chips': chips, 'per_page': per_page,
        'view_mode': request.GET.get('view', 'grid'),
        'color_list': color_list,
        'selected_brands': request.GET.getlist('brand'),
        'selected_colors': request.GET.getlist('color'),
        'root_cats': Category.objects.filter(is_active=True, parent=None).prefetch_related('children'),
        'page_title': category.name,
        'meta_description': category.meta_description or category.description,
    })


# ─── Product Detail ────────────────────────────────────────────────────────────

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    Product.objects.filter(pk=product.pk).update(views_count=product.views_count + 1)

    related = (Product.objects.filter(category=product.category, is_active=True)
               .exclude(pk=product.pk).select_related('brand').prefetch_related('images')[:8])
    reviews     = product.reviews.filter(is_approved=True)
    breadcrumbs = product.category.get_breadcrumbs() + [(product.name, None)]

    # Calculate rating distribution
    rating_dist = {}
    for i in range(5, 0, -1):
        count = reviews.filter(rating=i).count()
        rating_dist[i] = {
            'count': count,
            'percent': int((count / reviews.count() * 100) if reviews.count() else 0)
        }

    # Recently viewed (session)
    rv = request.session.get('recently_viewed', [])
    str_pk = str(product.pk)
    if str_pk in rv: rv.remove(str_pk)
    rv.insert(0, str_pk)
    request.session['recently_viewed'] = rv[:10]
    recently_viewed = (Product.objects.filter(pk__in=rv[:5], is_active=True)
                       .exclude(pk=product.pk).select_related('brand').prefetch_related('images'))

    return render(request, 'products/detail.html', {
        'product': product, 'related_products': related,
        'reviews': reviews, 'breadcrumbs': breadcrumbs,
        'rating_dist': rating_dist, 'recently_viewed': recently_viewed,
        'page_title': product.name,
        'meta_description': product.meta_description or product.short_description,
    })


# ─── Categories Overview ───────────────────────────────────────────────────────

def categories_overview(request):
    root_categories = (Category.objects.filter(is_active=True, parent=None)
                       .prefetch_related('children').order_by('order', 'name'))
    return render(request, 'products/categories.html', {
        'root_categories': root_categories,
        'page_title': 'All Categories',
    })


# ─── Product Inquiry ──────────────────────────────────────────────────────────

@require_http_methods(['POST'])
def submit_inquiry(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    message = request.POST.get('message', '').strip()

    if not all([name, email, message]):
        return JsonResponse({'status': 'error', 'message': 'Please fill all fields'}, status=400)

    inquiry = ProductInquiry.objects.create(
        product=product, name=name, email=email, phone=phone, message=message
    )

    try:
        send_mail(
            subject=f'Product Inquiry: {product.name}',
            message=f'Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )
    except Exception as e:
        print(f'Email error: {e}')

    return JsonResponse({'status': 'success', 'message': 'Inquiry sent! We will contact you soon.'})


# ─── Submit Review ────────────────────────────────────────────────────────────

@require_http_methods(['POST'])
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)

    if not all([request.POST.get('name'), request.POST.get('email'), request.POST.get('rating'), request.POST.get('content')]):
        return JsonResponse({'status': 'error', 'message': 'Please fill all fields'}, status=400)

    try:
        rating = int(request.POST.get('rating'))
        if not (1 <= rating <= 5):
            return JsonResponse({'status': 'error', 'message': 'Invalid rating'}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid rating'}, status=400)

    review = Review.objects.create(
        product=product,
        name=request.POST.get('name'),
        email=request.POST.get('email'),
        rating=rating,
        title=request.POST.get('title', ''),
        content=request.POST.get('content'),
        pros=request.POST.get('pros', ''),
        cons=request.POST.get('cons', ''),
        user=request.user if request.user.is_authenticated else None,
        is_verified_purchase=False,
    )

    return JsonResponse({
        'status': 'success',
        'message': 'Review submitted! It will be visible after approval.',
        'review_id': review.pk,
    })


# ─── Stock Alert ──────────────────────────────────────────────────────────────

@require_http_methods(['POST'])
def stock_alert_signup(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    email = request.POST.get('email', '').strip()
    name = request.POST.get('name', '').strip()

    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email is required'}, status=400)

    alert, created = StockAlert.objects.get_or_create(
        product=product, email=email,
        defaults={'name': name or 'Customer'}
    )

    if not created:
        return JsonResponse({
            'status': 'info',
            'message': 'You are already subscribed for stock alerts on this product.'
        })

    try:
        send_mail(
            subject=f'Stock Alert Confirmed: {product.name}',
            message=f'You will receive a notification when "{product.name}" is back in stock.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        print(f'Email error: {e}')

    return JsonResponse({
        'status': 'success',
        'message': 'You will be notified when this product is back in stock!'
    })


# ─── Rating Distribution (AJAX) ────────────────────────────────────────────────

def rating_distribution(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.filter(is_approved=True)

    distribution = {}
    for i in range(5, 0, -1):
        count = reviews.filter(rating=i).count()
        distribution[i] = {
            'count': count,
            'percent': int((count / reviews.count() * 100) if reviews.count() else 0)
        }

    return JsonResponse({
        'total_reviews': reviews.count(),
        'average_rating': product.average_rating,
        'distribution': distribution,
    })


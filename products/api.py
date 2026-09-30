"""Catalog, reviews and wishlist endpoints under /api/v1/ (Module 14).

    GET    /products/                     list — filters below, search=, ordering=
    GET    /products/{slug}/              detail (specs, variants, FAQs, rating breakdown)
    GET    /products/{slug}/related/      related / viewed-together / popular / same brand
    GET    /products/{slug}/reviews/      approved reviews (sort=recent|helpful|rating_high|rating_low)
    POST   /products/{slug}/reviews/      write a review (held for moderation)
    POST   /products/{slug}/inquiry/      product enquiry (emails the shop)
    GET    /products/compare/?ids=a,b,c   side-by-side comparison (max 3)
    GET    /products/search-suggestions/?q=
    POST   /reviews/{id}/helpful/         "was this helpful" vote
    GET    /categories/  /{slug}/  /tree/
    GET    /brands/  /{slug}/
    GET    /wishlist/  /ids/     POST /wishlist/  /sync/     DELETE /wishlist/{product_id}/   (signed in)
    GET    /auth/me/reviews/              the signed-in user's reviews, pending ones too

Product list filters (all optional, combinable): ids (uuid, repeatable or comma list),
category (slug, includes sub-categories), brand (slug, repeatable or comma list),
min_price, max_price, condition, color, min_rating, min_discount, in_stock=1,
on_sale=1, new_arrival=1, featured=1, trending=1.
"""
from decimal import Decimal, InvalidOperation

from django.db.models import Avg, Count, F, Q
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api_utils import first_time, flag, form_data, form_errors, rate_limited, user_defaults
from core.models import Brand
from .compare import MAX_COMPARE, build_comparison, parse_ids
from .forms import ProductInquiryForm, ReviewForm
from .models import Category, Product, Review, Wishlist
from .related import (get_frequently_viewed_together, get_popular_in_category,
                      get_related_products, get_same_brand)
from .serializers import (
    BrandSerializer, CategoryDetailSerializer, CategorySerializer, MyReviewSerializer,
    ProductDetailSerializer, ProductListSerializer, ReviewSerializer, WishlistSerializer,
)
from .views import notify_product_inquiry

WISHLIST_MAX = 200


def product_queryset():
    """Active products with everything a product card needs, ratings annotated.
    (Explicit order_by: Meta.ordering is not applied to aggregated querysets.)"""
    approved = Q(reviews__is_approved=True)
    return (Product.objects.filter(is_active=True)
            .select_related('category', 'brand').prefetch_related('images')
            .annotate(avg_rating=Avg('reviews__rating', filter=approved),
                      num_reviews=Count('reviews', filter=approved))
            .order_by('-created_at'))


def with_card_data(products):
    """Re-load `products` through product_queryset(), keeping their order —
    for lists built elsewhere (related products) so cards don't cost N+1 queries."""
    pks   = [p.pk for p in products]
    found = {p.pk: p for p in product_queryset().filter(pk__in=pks)}
    return [found[pk] for pk in pks if pk in found]


def _decimal(value):
    try:
        return Decimal(str(value).strip()) if value not in (None, '') else None
    except InvalidOperation:
        return None


def _slugs(params, name):
    return [s.strip() for raw in params.getlist(name) for s in raw.split(',') if s.strip()]


def filter_products(qs, params):
    """The website's product filters (products.views._apply_filters), as query params."""
    if params.get('ids'):
        qs = qs.filter(pk__in=parse_ids(params.getlist('ids'), limit=100))
    if params.get('category'):
        cat = Category.objects.filter(slug=params['category'], is_active=True).first()
        if not cat:
            return qs.none()
        qs = qs.filter(category_id__in=[cat.pk] + [c.pk for c in cat.get_all_descendants()])
    brands = _slugs(params, 'brand')
    if brands:
        qs = qs.filter(brand__slug__in=brands)
    if params.get('condition'):
        qs = qs.filter(condition=params['condition'])
    colors = _slugs(params, 'color')
    if colors:
        color_q = Q()
        for c in colors:
            color_q |= Q(color__iexact=c)
        qs = qs.filter(color_q)

    min_price, max_price = _decimal(params.get('min_price')), _decimal(params.get('max_price'))
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)
    min_rating = _decimal(params.get('min_rating'))
    if min_rating is not None:
        qs = qs.filter(avg_rating__gte=min_rating)
    min_discount = _decimal(params.get('min_discount'))
    if min_discount is not None:
        # discount >= pct  <=>  sale_price <= price * (100 - pct) / 100
        qs = qs.filter(sale_price__isnull=False,
                       sale_price__lte=F('price') * ((Decimal(100) - min_discount) / Decimal(100)))

    if flag(params, 'in_stock'):
        qs = qs.filter(stock__gt=0)
    if flag(params, 'on_sale'):
        qs = qs.filter(sale_price__isnull=False)
    if flag(params, 'new_arrival'):
        qs = qs.filter(is_new_arrival=True)
    if flag(params, 'featured'):
        qs = qs.filter(is_featured=True)
    if flag(params, 'trending'):
        qs = qs.filter(is_trending=True)
    return qs


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BrandSerializer
    lookup_field     = 'slug'
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ['name']
    ordering_fields  = ['name', 'order']

    def get_queryset(self):
        qs = Brand.objects.filter(is_active=True)
        return qs.filter(is_featured=True) if flag(self.request.query_params, 'featured') else qs


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """?parent=<slug> direct children · ?root=1 top level only · ?featured=1"""
    lookup_field    = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields   = ['name', 'description']

    def get_serializer_class(self):
        return CategoryDetailSerializer if self.action == 'retrieve' else CategorySerializer

    def get_queryset(self):
        qs = (Category.objects.filter(is_active=True).select_related('parent')
              .annotate(num_products=Count('products', filter=Q(products__is_active=True)))
              .order_by('order', 'name'))
        p = self.request.query_params
        if p.get('parent'):
            qs = qs.filter(parent__slug=p['parent'])
        if flag(p, 'root'):
            qs = qs.filter(parent__isnull=True)
        if flag(p, 'featured'):
            qs = qs.filter(is_featured=True)
        return qs

    @action(detail=False, pagination_class=None)
    def tree(self, request):
        """Every active category, nested: [{..., "children": [...]}] — one query."""
        cats = list(self.get_queryset())
        data = {c.pk: {**CategorySerializer(c, context={'request': request}).data, 'children': []} for c in cats}
        roots = []
        for c in cats:
            parent = data.get(c.parent_id)
            (parent['children'] if parent else roots).append(data[c.pk])
        return Response(roots)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field    = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ['name', 'short_description', 'sku', 'brand__name', 'category__name']
    ordering_fields = ['price', 'created_at', 'name', 'views_count', 'avg_rating']
    ordering        = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        if self.action == 'reviews':
            return ReviewSerializer
        return ProductListSerializer

    def get_queryset(self):
        qs = product_queryset()
        if self.action == 'retrieve':
            return qs.prefetch_related('attributes__attribute', 'variants', 'faqs')
        if self.action == 'list':
            return filter_products(qs, self.request.query_params)
        return qs

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        if first_time(request, f'product-view:{product.pk}', ttl=300):
            Product.objects.filter(pk=product.pk).update(views_count=F('views_count') + 1)
        return Response(self.get_serializer(product).data)

    @action(detail=True)
    def related(self, request, slug=None):
        product  = self.get_object()
        sections = {
            'related':                    get_related_products(product, limit=8),
            'frequently_viewed_together': get_frequently_viewed_together(product, limit=4),
            'popular_in_category':        list(get_popular_in_category(product, limit=4)),
            'same_brand':                 list(get_same_brand(product, limit=4)),
        }
        cards = {p.pk: p for p in with_card_data([p for ps in sections.values() for p in ps])}
        ctx   = {'request': request}
        return Response({name: ProductListSerializer([cards[p.pk] for p in ps if p.pk in cards],
                                                     many=True, context=ctx).data
                         for name, ps in sections.items()})

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, slug=None):
        product = self.get_object()
        if request.method == 'POST':
            return self._create_review(request, product)
        order = {'helpful': ['-helpful_count', '-created_at'], 'rating_high': ['-rating', '-created_at'],
                 'rating_low': ['rating', '-created_at']}.get(request.query_params.get('sort'), ['-created_at'])
        qs   = product.reviews.filter(is_approved=True).order_by(*order)
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(ReviewSerializer(page, many=True).data)

    def _create_review(self, request, product):
        limited = rate_limited(request, 'review')
        if limited:
            return limited
        form = ReviewForm(form_data(request, ReviewForm.Meta.fields, **user_defaults(request)))
        if not form.is_valid():
            return Response(form_errors(form), status=status.HTTP_400_BAD_REQUEST)
        review = form.save(commit=False)
        review.product = product
        if request.user.is_authenticated:
            review.user = request.user
        review.save()
        return Response({'detail': 'Thank you! Your review is pending approval.',
                         'review': ReviewSerializer(review).data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def inquiry(self, request, slug=None):
        product = self.get_object()
        limited = rate_limited(request, 'product-inquiry')
        if limited:
            return limited
        form = ProductInquiryForm(form_data(request, ProductInquiryForm.Meta.fields, **user_defaults(request)))
        if not form.is_valid():
            return Response(form_errors(form), status=status.HTTP_400_BAD_REQUEST)
        inquiry = form.save(commit=False)
        inquiry.product = product
        inquiry.save()
        notify_product_inquiry(inquiry, request)
        return Response({'detail': 'Enquiry sent! We will respond within 24 hours.'},
                        status=status.HTTP_201_CREATED)

    @action(detail=False)
    def compare(self, request):
        """?ids=a&ids=b or ?ids=a,b,c — row values a product lacks are null."""
        comparison = build_comparison(parse_ids(request.query_params.getlist('ids'), limit=MAX_COMPARE),
                                      blank=None)
        products = comparison.pop('products')
        return Response({
            'products': ProductListSerializer(products, many=True, context={'request': request}).data,
            **comparison,
            'best_price': str(comparison['best_price']) if comparison['best_price'] is not None else None,
            'max_products': MAX_COMPARE,
        })

    @action(detail=False, url_path='search-suggestions')
    def search_suggestions(self, request):
        """Type-ahead: a few matching products, categories and brands (q of 2+ characters)."""
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'products': [], 'categories': [], 'brands': []})
        products = (product_queryset()
                    .filter(Q(name__icontains=q) | Q(sku__iexact=q) | Q(brand__name__icontains=q))
                    .order_by('-is_featured', '-views_count')[:6])
        categories = Category.objects.filter(is_active=True, name__icontains=q)[:5]
        brands     = Brand.objects.filter(is_active=True, name__icontains=q)[:5]
        return Response({
            'products':   ProductListSerializer(products, many=True, context={'request': request}).data,
            'categories': [{'name': c.name, 'slug': c.slug} for c in categories],
            'brands':     [{'name': b.name, 'slug': b.slug} for b in brands],
        })


class ReviewHelpfulView(APIView):
    """POST /reviews/{id}/helpful/ — counted once per user (or connection) per review."""

    def post(self, request, pk):
        review  = get_object_or_404(Review, pk=pk, is_approved=True)
        limited = rate_limited(request, 'helpful', rate='30/10m')
        if limited:
            return limited
        counted = first_time(request, f'helpful:{review.pk}', ttl=86400 * 365)
        if counted:
            Review.objects.filter(pk=review.pk).update(helpful_count=F('helpful_count') + 1)
            review.refresh_from_db(fields=['helpful_count'])
        return Response({'helpful_count': review.helpful_count, 'counted': counted})


class MyReviewsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = MyReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user).select_related('product')


class WishlistViewSet(viewsets.GenericViewSet):
    """The signed-in user's saved products (newest first)."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = WishlistSerializer
    lookup_field       = 'product_id'
    lookup_value_regex = '[0-9a-fA-F-]{36}'

    def get_queryset(self):
        return (Wishlist.objects.filter(user=self.request.user, product__is_active=True)
                .select_related('product').order_by('-added_at'))

    def list(self, request):
        page  = self.paginate_queryset(self.get_queryset())
        cards = {p.pk: p for p in with_card_data([w.product for w in page])}
        for w in page:
            w.product = cards.get(w.product_id, w.product)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def _ids(self):
        return [str(pk) for pk in self.get_queryset().values_list('product_id', flat=True)]

    def create(self, request):
        """{"product_id": "<uuid>"} — adding one that's already saved is a no-op (200)."""
        ids = parse_ids([request.data.get('product_id', '')], limit=1)
        product = get_object_or_404(Product, pk=ids[0], is_active=True) if ids else None
        if not product:
            return Response({'product_id': ['A valid product id is required.']},
                            status=status.HTTP_400_BAD_REQUEST)
        if Wishlist.objects.filter(user=request.user).count() >= WISHLIST_MAX:
            return Response({'detail': f'Your wishlist is full ({WISHLIST_MAX} items).'},
                            status=status.HTTP_400_BAD_REQUEST)
        _, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        return Response({'detail': 'Saved to your wishlist.', 'ids': self._ids()},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def destroy(self, request, product_id=None):
        Wishlist.objects.filter(user=request.user, product_id__in=parse_ids([product_id], limit=1)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, pagination_class=None)
    def ids(self, request):
        """Just the saved product ids — for drawing filled hearts on product cards."""
        return Response(self._ids())

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """{"product_ids": [...]} — merge a guest (on-device) wishlist in after sign-in.
        Returns the full list of saved ids."""
        raw = request.data.get('product_ids') or []
        if not isinstance(raw, list):
            raw = [raw]
        room = max(WISHLIST_MAX - Wishlist.objects.filter(user=request.user).count(), 0)
        ids  = parse_ids(raw, limit=room)
        have = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
        new  = Product.objects.filter(pk__in=[pk for pk in ids if pk not in have], is_active=True)
        Wishlist.objects.bulk_create([Wishlist(user=request.user, product=p) for p in new],
                                     ignore_conflicts=True)
        return Response(self._ids())

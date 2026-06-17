"""DRF viewsets for the public read API (Module 14).

Read-only catalog endpoints under /api/v1/:
    GET /api/v1/products/                list (filter: category, brand, min_price,
                                         max_price, condition, in_stock, featured,
                                         trending; search=; ordering=)
    GET /api/v1/products/{slug}/         detail
    GET /api/v1/categories/              list
    GET /api/v1/categories/{slug}/       detail
    GET /api/v1/brands/                  list
"""
from rest_framework import viewsets, filters
from core.models import Brand
from .models import Category, Product
from .serializers import (
    BrandSerializer, CategorySerializer,
    ProductListSerializer, ProductDetailSerializer,
)


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    lookup_field     = 'slug'
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ['name']
    ordering_fields  = ['name', 'order']


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    lookup_field     = 'slug'
    filter_backends  = [filters.SearchFilter]
    search_fields    = ['name', 'description']

    def get_queryset(self):
        return Category.objects.filter(is_active=True)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field    = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ['name', 'short_description', 'brand__name', 'category__name']
    ordering_fields = ['price', 'created_at', 'name', 'views_count']
    ordering        = ['-created_at']

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == 'retrieve' else ProductListSerializer

    def get_queryset(self):
        qs = (Product.objects.filter(is_active=True)
              .select_related('category', 'brand').prefetch_related('images'))
        p = self.request.query_params

        if p.get('category'):
            qs = qs.filter(category__slug=p['category'])
        if p.get('brand'):
            qs = qs.filter(brand__slug=p['brand'])
        if p.get('condition'):
            qs = qs.filter(condition=p['condition'])
        if p.get('min_price'):
            qs = qs.filter(price__gte=p['min_price'])
        if p.get('max_price'):
            qs = qs.filter(price__lte=p['max_price'])
        if p.get('in_stock') in ('1', 'true', 'True'):
            qs = qs.filter(stock__gt=0)
        if p.get('featured') in ('1', 'true', 'True'):
            qs = qs.filter(is_featured=True)
        if p.get('trending') in ('1', 'true', 'True'):
            qs = qs.filter(is_trending=True)
        return qs

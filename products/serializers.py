"""DRF serializers for the public read API (Module 14)."""
from rest_framework import serializers
from core.models import Brand
from .models import Category, Product, ProductImage, Review


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Brand
        fields = ['id', 'name', 'slug', 'logo', 'website', 'is_featured']


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'parent', 'icon', 'color',
                  'description', 'image', 'banner', 'is_featured', 'product_count']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'order']


class ProductListSerializer(serializers.ModelSerializer):
    brand           = serializers.StringRelatedField()
    category        = serializers.StringRelatedField()
    primary_image   = serializers.SerializerMethodField()
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    average_rating  = serializers.FloatField(read_only=True)

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'sku', 'brand', 'category',
                  'price', 'sale_price', 'effective_price', 'discount_percent',
                  'condition', 'is_in_stock', 'average_rating', 'review_count',
                  'is_featured', 'is_trending', 'primary_image']

    def get_primary_image(self, obj):
        img = obj.primary_image
        if img and img.image:
            request = self.context.get('request')
            url = img.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Review
        fields = ['name', 'rating', 'title', 'content', 'is_verified_purchase',
                  'helpful_count', 'created_at']


class ProductDetailSerializer(ProductListSerializer):
    images  = ProductImageSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'short_description', 'description', 'stock', 'warranty',
            'color', 'weight', 'images', 'reviews',
        ]

    def get_reviews(self, obj):
        qs = obj.reviews.filter(is_approved=True)[:10]
        return ReviewSerializer(qs, many=True).data

"""DRF serializers for the catalog API (Module 14)."""
from rest_framework import serializers
from core.models import Brand
from .models import Category, Product, ProductImage, ProductVariant, Review, Wishlist


def absolute_url(request, file):
    """Absolute URL of an uploaded file, or None when there isn't one."""
    if not file:
        return None
    return request.build_absolute_uri(file.url) if request else file.url


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Brand
        fields = ['id', 'name', 'slug', 'logo', 'website', 'description', 'is_featured']


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    parent_slug   = serializers.SlugRelatedField(source='parent', slug_field='slug', read_only=True)

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'parent', 'parent_slug', 'icon', 'color',
                  'description', 'image', 'banner', 'banner_mobile', 'is_featured', 'product_count']

    def get_product_count(self, obj):
        """Active products directly in this category (the `num_products` annotation when present)."""
        if hasattr(obj, 'num_products'):
            return obj.num_products
        return obj.product_count


class CategoryDetailSerializer(CategorySerializer):
    """Adds the breadcrumb trail and the direct sub-categories."""
    breadcrumbs = serializers.SerializerMethodField()
    children    = serializers.SerializerMethodField()

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['breadcrumbs', 'children']

    def get_breadcrumbs(self, obj):
        return [{'name': c.name, 'slug': c.slug} for c in obj.get_ancestors() + [obj]]

    def get_children(self, obj):
        request = self.context.get('request')
        return [{'id': c.pk, 'name': c.name, 'slug': c.slug, 'icon': c.icon,
                 'image': absolute_url(request, c.image)}
                for c in obj.children.filter(is_active=True)]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'order']


class ProductListSerializer(serializers.ModelSerializer):
    """A product card. Rating fields read the `avg_rating` / `num_reviews`
    annotations when the queryset has them (see products.api.product_queryset),
    so a page of cards costs a fixed number of queries."""
    brand            = serializers.StringRelatedField()
    brand_slug       = serializers.SlugRelatedField(source='brand', slug_field='slug', read_only=True)
    category         = serializers.StringRelatedField()
    category_slug    = serializers.SlugRelatedField(source='category', slug_field='slug', read_only=True)
    primary_image    = serializers.SerializerMethodField()
    effective_price  = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    average_rating   = serializers.SerializerMethodField()
    review_count     = serializers.SerializerMethodField()
    is_wishlisted    = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'sku', 'brand', 'brand_slug', 'category', 'category_slug',
                  'price', 'sale_price', 'effective_price', 'discount_percent',
                  'condition', 'is_in_stock', 'average_rating', 'review_count',
                  'is_featured', 'is_trending', 'is_new_arrival', 'primary_image', 'is_wishlisted']

    def get_primary_image(self, obj):
        imgs = list(obj.images.all())               # uses the prefetch when there is one
        img  = next((i for i in imgs if i.is_primary), imgs[0] if imgs else None)
        return absolute_url(self.context.get('request'), img.image if img else None)

    def get_average_rating(self, obj):
        if hasattr(obj, 'avg_rating'):
            return round(obj.avg_rating or 0, 1)
        return obj.average_rating

    def get_review_count(self, obj):
        if hasattr(obj, 'num_reviews'):
            return obj.num_reviews
        return obj.review_count

    def get_is_wishlisted(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        ids = getattr(request, '_wishlist_ids', None)
        if ids is None:                             # one query per request, not per product
            ids = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
            request._wishlist_ids = ids
        return obj.pk in ids


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Review
        fields = ['id', 'name', 'rating', 'title', 'content', 'pros', 'cons',
                  'is_verified_purchase', 'helpful_count', 'created_at']


class MyReviewSerializer(ReviewSerializer):
    """A signed-in user's own review, including whether it is approved yet."""
    product = serializers.SerializerMethodField()

    class Meta(ReviewSerializer.Meta):
        fields = ReviewSerializer.Meta.fields + ['is_approved', 'product']

    def get_product(self, obj):
        return {'id': obj.product_id, 'name': obj.product.name, 'slug': obj.product.slug}


class ProductVariantSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model  = ProductVariant
        fields = ['id', 'name', 'sku', 'price_modifier', 'price', 'stock', 'image', 'color_code']

    def get_price(self, obj):
        return str(obj.product.effective_price + obj.price_modifier)


class ProductDetailSerializer(ProductListSerializer):
    images              = ProductImageSerializer(many=True, read_only=True)
    reviews             = serializers.SerializerMethodField()
    specifications      = serializers.SerializerMethodField()
    variants            = serializers.SerializerMethodField()
    faqs                = serializers.SerializerMethodField()
    rating_distribution = serializers.SerializerMethodField()
    breadcrumbs         = serializers.SerializerMethodField()
    savings_amount      = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    web_url             = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'short_description', 'description', 'stock', 'is_low_stock', 'savings_amount',
            'warranty', 'color', 'weight', 'images', 'specifications', 'variants', 'faqs',
            'rating_distribution', 'reviews', 'breadcrumbs', 'web_url',
        ]

    def get_reviews(self, obj):
        """The 10 newest approved reviews; the rest page through /products/{slug}/reviews/."""
        return ReviewSerializer(obj.reviews.filter(is_approved=True)[:10], many=True).data

    def get_specifications(self, obj):
        return [{'name': av.attribute.name, 'value': av.value} for av in obj.attributes.all()]

    def get_variants(self, obj):
        active = [v for v in obj.variants.all() if v.is_active]
        return ProductVariantSerializer(active, many=True, context=self.context).data

    def get_faqs(self, obj):
        return [{'question': f.question, 'answer': f.answer} for f in obj.faqs.all() if f.is_active]

    def get_rating_distribution(self, obj):
        return [{'stars': stars, **row} for stars, row in obj.get_rating_distribution().items()]

    def get_breadcrumbs(self, obj):
        cats = obj.category.get_ancestors() + [obj.category]
        return [{'name': c.name, 'slug': c.slug} for c in cats]

    def get_web_url(self, obj):
        """The product page on the website — for share sheets."""
        request = self.context.get('request')
        url = obj.get_absolute_url()
        return request.build_absolute_uri(url) if request else url


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model  = Wishlist
        fields = ['product', 'added_at']

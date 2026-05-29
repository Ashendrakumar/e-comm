from django.contrib import admin
from django.utils.html import format_html
from .models import (Category, Product, ProductImage, ProductAttribute,
                     ProductAttributeValue, ProductVariant, Review,
                     ReviewImage, FAQ, ProductInquiry)


class SubcategoryInline(admin.TabularInline):
    model = Category
    extra = 0
    fields = ('name', 'slug', 'icon', 'color', 'is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}
    show_change_link = True
    verbose_name = 'Sub-category'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'order', '_preview')
    readonly_fields = ('_preview',)
    def _preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:48px;border-radius:6px;">', obj.image.url)
        return '—'
    _preview.short_description = 'Preview'

class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 2
    fields = ('attribute', 'value')

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('name', 'sku', 'price_modifier', 'stock', 'color_code', 'is_active')

class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 1
    fields = ('question', 'answer', 'order', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display   = ('name', 'parent', '_icon', '_color', '_products', 'is_featured', 'is_active', 'show_in_nav', 'order')
    list_editable  = ('is_featured', 'is_active', 'show_in_nav', 'order')
    list_filter    = ('is_active', 'is_featured', 'parent')
    search_fields  = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines        = [SubcategoryInline]
    readonly_fields = ('_banner_preview', 'created_at', 'updated_at')
    fieldsets = (
        ('Identity',    {'fields': ('name', 'slug', 'parent', 'icon', 'color')}),
        ('Images',      {'fields': ('image', 'banner', 'banner_mobile', '_banner_preview')}),
        ('Content',     {'fields': ('description',)}),
        ('Visibility',  {'fields': ('is_active', 'is_featured', 'show_in_nav', 'order')}),
        ('SEO',         {'fields': ('meta_title', 'meta_description', 'meta_keywords'), 'classes': ('collapse',)}),
    )

    def _icon(self, obj):
        if obj.icon:
            return format_html('<i class="{}" style="font-size:18px;color:{};"></i>', obj.icon, obj.color or '#2563eb')
        return '—'
    _icon.short_description = 'Icon'

    def _color(self, obj):
        return format_html('<span style="display:inline-block;width:22px;height:22px;background:{};border-radius:4px;border:1px solid #ddd;"></span>', obj.color or '#2563eb')
    _color.short_description = 'Colour'

    def _products(self, obj):
        d = obj.product_count; t = obj.total_product_count
        if t != d:
            return format_html('{} <small style="color:#9ca3af">({} total)</small>', d, t)
        return d
    _products.short_description = 'Products'

    def _banner_preview(self, obj):
        if obj.banner:
            return format_html('<img src="{}" style="max-width:400px;max-height:100px;border-radius:8px;">', obj.banner.url)
        return 'No banner uploaded'
    _banner_preview.short_description = 'Banner Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display   = ('_thumb', 'name', 'sku', 'category', 'brand', '_price', '_discount', '_stock', 'is_active', 'is_featured', 'is_trending')
    list_editable  = ('is_active', 'is_featured', 'is_trending')
    list_filter    = ('is_active', 'is_featured', 'is_trending', 'is_new_arrival', 'category', 'brand', 'condition')
    search_fields  = ('name', 'sku', 'brand__name', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    inlines        = [ProductImageInline, ProductAttributeValueInline, ProductVariantInline, FAQInline]
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'sku')
    list_per_page  = 25
    fieldsets = (
        ('Basic',       {'fields': ('name', 'slug', 'sku', 'category', 'brand', 'condition', 'color')}),
        ('Description', {'fields': ('short_description', 'description')}),
        ('Pricing',     {'fields': ('price', 'sale_price', 'cost_price')}),
        ('Inventory',   {'fields': ('stock', 'low_stock_threshold', 'warranty', 'weight')}),
        ('Flags',       {'fields': ('is_active', 'is_featured', 'is_trending', 'is_new_arrival')}),
        ('SEO',         {'fields': ('meta_title', 'meta_description', 'meta_keywords'), 'classes': ('collapse',)}),
        ('Stats',       {'fields': ('views_count', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def _thumb(self, obj):
        img = obj.primary_image
        if img:
            return format_html('<img src="{}" style="height:44px;width:44px;object-fit:contain;border-radius:6px;background:#f9fafb;">', img.image.url)
        return '—'
    _thumb.short_description = ''

    def _price(self, obj):
        if obj.sale_price:
            return format_html('<b>₹{}</b> <small style="color:#9ca3af;text-decoration:line-through">₹{}</small>', obj.sale_price, obj.price)
        return format_html('<b>₹{}</b>', obj.price)
    _price.short_description = 'Price'

    def _discount(self, obj):
        p = obj.discount_percent
        if p:
            return format_html('<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700;">-{}%</span>', p)
        return '—'
    _discount.short_description = 'Off'

    def _stock(self, obj):
        if not obj.is_in_stock:
            return format_html('<span style="color:#dc2626;font-weight:600;">Out of Stock</span>')
        if obj.is_low_stock:
            return format_html('<span style="color:#f59e0b;font-weight:600;">Low ({})</span>', obj.stock)
        return format_html('<span style="color:#16a34a;font-weight:600;">{}</span>', obj.stock)
    _stock.short_description = 'Stock'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'brand').prefetch_related('images')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ('name', 'product', 'rating', 'title', 'is_approved', 'is_verified_purchase', 'helpful_count', 'created_at')
    list_editable = ('is_approved',)
    list_filter   = ('is_approved', 'rating', 'is_verified_purchase')
    search_fields = ('name', 'product__name', 'content')
    readonly_fields = ('created_at', 'helpful_count')
    actions       = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} review(s) approved.')
    approve_reviews.short_description = 'Approve selected reviews'

    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} review(s) rejected.')
    reject_reviews.short_description = 'Reject selected reviews'


@admin.register(ProductInquiry)
class ProductInquiryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'phone', 'product', 'status', 'created_at')
    list_editable = ('status',)
    list_filter   = ('status',)
    search_fields = ('name', 'email', 'product__name')
    readonly_fields = ('created_at',)


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


# ── Module 5 ──────────────────────────────────────────────────────────────────
from .models import ProductViewLog, FrequentlyViewedTogether

@admin.register(FrequentlyViewedTogether)
class FrequentlyViewedTogetherAdmin(admin.ModelAdmin):
    list_display  = ('product_a', 'product_b', 'view_count', 'updated_at')
    list_filter   = ('updated_at',)
    search_fields = ('product_a__name', 'product_b__name')
    readonly_fields = ('updated_at',)
    ordering = ('-view_count',)

@admin.register(ProductViewLog)
class ProductViewLogAdmin(admin.ModelAdmin):
    list_display  = ('product', 'session_key_short', 'user', 'viewed_at')
    list_filter   = ('viewed_at',)
    search_fields = ('product__name', 'session_key')
    readonly_fields = ('viewed_at',)

    def session_key_short(self, obj):
        return obj.session_key[:12] + '…'
    session_key_short.short_description = 'Session'

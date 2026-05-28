from django.contrib import admin
from django.utils.html import format_html
from .models import (Category, Product, ProductImage, ProductAttribute,
                     ProductAttributeValue, ProductVariant, Review, FAQ,
                     Wishlist, ProductInquiry, StockAlert)


# ── Inlines ───────────────────────────────────────────────────────────────────

class SubcategoryInline(admin.TabularInline):
    model               = Category
    extra               = 0
    fields              = ('name', 'slug', 'icon', 'color', 'is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}
    show_change_link    = True
    verbose_name        = 'Sub-category'
    verbose_name_plural = 'Sub-categories'


class ProductImageInline(admin.TabularInline):
    model           = ProductImage
    extra           = 1
    fields          = ('image', 'alt_text', 'is_primary', 'order', 'thumb_preview')
    readonly_fields = ('thumb_preview',)

    def thumb_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:6px;">', obj.image.url)
        return '—'
    thumb_preview.short_description = 'Preview'


class ProductAttributeValueInline(admin.TabularInline):
    model  = ProductAttributeValue
    extra  = 2
    fields = ('attribute', 'value')


class ProductVariantInline(admin.TabularInline):
    model  = ProductVariant
    extra  = 1
    fields = ('name', 'sku', 'price_modifier', 'stock', 'color_code', 'is_active')


class FAQInline(admin.TabularInline):
    model  = FAQ
    extra  = 1
    fields = ('question', 'answer', 'order', 'is_active')


# ── Category Admin ────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ('name', 'parent', 'icon_preview', 'color_swatch',
                           'product_count_col', 'is_featured', 'is_active', 'show_in_nav', 'order')
    list_editable       = ('is_featured', 'is_active', 'show_in_nav', 'order')
    list_filter         = ('is_active', 'is_featured', 'show_in_nav', 'parent')
    search_fields       = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines             = [SubcategoryInline]
    readonly_fields     = ('banner_preview', 'icon_image_preview', 'created_at', 'updated_at',
                           'computed_product_count', 'computed_total_count')
    list_per_page       = 25

    fieldsets = (
        ('Identity', {
            'fields': ('name', 'slug', 'parent', 'icon', 'color')
        }),
        ('Images', {
            'fields': ('image', 'icon_image_preview', 'banner', 'banner_mobile', 'banner_preview')
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('Visibility', {
            'fields': ('is_active', 'is_featured', 'show_in_nav', 'order')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Stats', {
            'fields': ('computed_product_count', 'computed_total_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '<span style="font-size:18px;" title="{}">'
                '<i class="{}" style="color:{}"></i>'
                '</span>',
                obj.icon, obj.icon, obj.color or '#2563eb'
            )
        return '—'
    icon_preview.short_description = 'Icon'

    def color_swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:22px;height:22px;background:{};'
            'border-radius:5px;border:1px solid #ddd;vertical-align:middle;" title="{}"></span>',
            obj.color or '#2563eb', obj.color or '#2563eb'
        )
    color_swatch.short_description = 'Colour'

    def product_count_col(self, obj):
        direct = obj.product_count
        total  = obj.total_product_count
        if total != direct:
            return format_html(
                '{} <small style="color:#9ca3af">({}  incl. sub)</small>', direct, total
            )
        return direct
    product_count_col.short_description = 'Products'

    def banner_preview(self, obj):
        if obj.banner:
            return format_html(
                '<img src="{}" style="max-width:400px;max-height:120px;border-radius:8px;'
                'border:1px solid #e5e7eb;">', obj.banner.url
            )
        return 'No banner uploaded yet'
    banner_preview.short_description = 'Banner Preview'

    def icon_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:8px;">', obj.image.url)
        return 'No icon image'
    icon_image_preview.short_description = 'Icon Image Preview'

    def computed_product_count(self, obj):
        return obj.product_count if obj.pk else '—'
    computed_product_count.short_description = 'Direct Products'

    def computed_total_count(self, obj):
        return obj.total_product_count if obj.pk else '—'
    computed_total_count.short_description = 'Total Products (incl. sub)'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')


# ── Product Admin ─────────────────────────────────────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display    = ('thumb_col', 'name', 'sku', 'category', 'brand',
                       'price_col', 'discount_col', 'stock_col',
                       'is_active', 'is_featured', 'is_trending')
    list_editable   = ('is_active', 'is_featured', 'is_trending')
    list_filter     = ('is_active', 'is_featured', 'is_trending', 'is_new_arrival',
                       'category', 'brand', 'condition')
    search_fields   = ('name', 'sku', 'description', 'brand__name', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    inlines         = [ProductImageInline, ProductAttributeValueInline,
                       ProductVariantInline, FAQInline]
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'sku')
    list_per_page   = 25

    fieldsets = (
        ('Basic Info',    {'fields': ('name', 'slug', 'sku', 'category', 'brand', 'condition')}),
        ('Descriptions',  {'fields': ('short_description', 'description')}),
        ('Pricing',       {'fields': ('price', 'sale_price', 'cost_price')}),
        ('Inventory',     {'fields': ('stock', 'low_stock_threshold', 'warranty', 'weight')}),
        ('Flags',         {'fields': ('is_active', 'is_featured', 'is_trending', 'is_new_arrival')}),
        ('SEO',           {'fields': ('meta_title', 'meta_description', 'meta_keywords'), 'classes': ('collapse',)}),
        ('Stats',         {'fields': ('views_count', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def thumb_col(self, obj):
        img = obj.primary_image
        if img:
            return format_html(
                '<img src="{}" style="height:44px;width:44px;object-fit:contain;'
                'border-radius:6px;background:#f9fafb;">', img.image.url
            )
        return format_html(
            '<div style="width:44px;height:44px;background:#f3f4f6;border-radius:6px;'
            'display:flex;align-items:center;justify-content:center;color:#d1d5db;font-size:18px;">📷</div>'
        )
    thumb_col.short_description = ''

    def price_col(self, obj):
        if obj.sale_price:
            return format_html(
                '<span style="font-weight:700;">₹{}</span> '
                '<small style="color:#9ca3af;text-decoration:line-through;">₹{}</small>',
                obj.sale_price, obj.price
            )
        return format_html('<span style="font-weight:700;">₹{}</span>', obj.price)
    price_col.short_description = 'Price'

    def discount_col(self, obj):
        pct = obj.discount_percent
        if pct:
            return format_html(
                '<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;'
                'border-radius:999px;font-size:11px;font-weight:700;">-{}%</span>', pct
            )
        return '—'
    discount_col.short_description = 'Off'

    def stock_col(self, obj):
        if not obj.is_in_stock:
            return format_html('<span style="color:#dc2626;font-weight:600;">Out of Stock</span>')
        if obj.is_low_stock:
            return format_html('<span style="color:#f59e0b;font-weight:600;">Low ({})</span>', obj.stock)
        return format_html('<span style="color:#16a34a;font-weight:600;">{}</span>', obj.stock)
    stock_col.short_description = 'Stock'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'brand').prefetch_related('images')


# ── Review / Attribute ────────────────────────────────────────────────────────

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display    = ('name', 'product', 'rating', 'is_approved', 'is_verified_purchase', 'created_at')
    list_editable   = ('is_approved',)
    list_filter     = ('is_approved', 'rating')
    search_fields   = ('name', 'product__name', 'content')
    readonly_fields = ('created_at',)


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display        = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


# ── Inquiry & Stock Alert Admin ───────────────────────────────────────────────

@admin.register(ProductInquiry)
class ProductInquiryAdmin(admin.ModelAdmin):
    list_display    = ('name', 'product', 'email', 'status', 'is_read', 'created_at')
    list_editable   = ('status', 'is_read')
    list_filter     = ('status', 'is_read', 'created_at')
    search_fields   = ('name', 'email', 'product__name', 'message')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy  = 'created_at'

    fieldsets = (
        ('Inquiry Details', {'fields': ('product', 'name', 'email', 'phone')}),
        ('Message', {'fields': ('message',)}),
        ('Status', {'fields': ('status', 'is_read')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display    = ('email', 'product', 'is_active', 'notified', 'created_at')
    list_editable   = ('is_active',)
    list_filter     = ('is_active', 'notified', 'created_at')
    search_fields   = ('email', 'product__name')
    readonly_fields = ('created_at',)
    date_hierarchy  = 'created_at'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display    = ('user', 'product', 'added_at')
    list_filter     = ('added_at', 'user')
    search_fields   = ('user__username', 'product__name')
    readonly_fields = ('added_at',)
    date_hierarchy  = 'added_at'


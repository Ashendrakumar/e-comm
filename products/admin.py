from decimal import Decimal
from django.contrib import admin
from django.utils.html import format_html
from core.admin_mixins import ExportCsvMixin
from core.importer import (SpreadsheetImportMixin, parse_bool, parse_decimal,
                           parse_int, clean)
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
class CategoryAdmin(SpreadsheetImportMixin, admin.ModelAdmin):
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

    # ── Spreadsheet import ─────────────────────────────────────────
    import_title = 'Import categories'
    import_intro = ('Bulk-create or update categories from a CSV/Excel sheet. '
                    'To build a tree, list parent categories first — child rows '
                    'reference their parent by name or slug. Existing rows are '
                    'matched by <code>slug</code> (or <code>name</code> if no slug is given) and updated.')
    import_columns = [
        ('name',             True,  'Category name.'),
        ('slug',             False, 'URL slug. Auto-generated from the name when blank. Also used as the match key on re-import.'),
        ('parent',           False, 'Parent category, referenced by its name or slug. Leave blank for a top-level category.'),
        ('icon',             False, 'CSS icon class, e.g. <code>ti ti-device-laptop</code>.'),
        ('color',            False, 'Hex colour, e.g. <code>#2563eb</code>.'),
        ('description',      False, 'Long description text.'),
        ('is_active',        False, 'true / false (default true).'),
        ('is_featured',      False, 'true / false (default false).'),
        ('show_in_nav',      False, 'true / false (default true).'),
        ('order',            False, 'Sort order, integer (default 0).'),
        ('meta_title',       False, 'SEO title.'),
        ('meta_description', False, 'SEO description.'),
        ('meta_keywords',    False, 'SEO keywords.'),
    ]
    import_sample_row = {
        'name': 'Laptops', 'slug': 'laptops', 'parent': '', 'icon': 'ti ti-device-laptop',
        'color': '#2563eb', 'description': 'Notebooks and ultrabooks.', 'is_active': 'true',
        'is_featured': 'true', 'show_in_nav': 'true', 'order': '1',
        'meta_title': 'Buy Laptops Online', 'meta_description': 'Top laptop deals.',
        'meta_keywords': 'laptop, notebook, ultrabook',
    }

    def import_row(self, row, request):
        name = clean(row.get('name'))
        if not name:
            raise ValueError('"name" is required.')

        slug = clean(row.get('slug'))
        # Resolve parent (by slug first, then name).
        parent = None
        parent_ref = clean(row.get('parent'))
        if parent_ref:
            parent = (Category.objects.filter(slug=parent_ref).first()
                      or Category.objects.filter(name__iexact=parent_ref).first())
            if not parent:
                raise ValueError(f'parent "{parent_ref}" not found — import it before its children.')

        # Match existing by slug, else by name.
        obj = None
        if slug:
            obj = Category.objects.filter(slug=slug).first()
        if obj is None:
            obj = Category.objects.filter(name__iexact=name).first()
        is_new = obj is None
        if is_new:
            obj = Category(name=name)
            if slug:
                obj.slug = slug

        obj.name = name
        if slug:
            obj.slug = slug
        if parent_ref:
            obj.parent = parent
        if parent and parent.pk == obj.pk:
            raise ValueError('a category cannot be its own parent.')

        # Plain optional text fields — only overwrite when a value is provided.
        for f in ('icon', 'color', 'description', 'meta_title', 'meta_description', 'meta_keywords'):
            val = clean(row.get(f))
            if val:
                setattr(obj, f, val)

        # Booleans / order — only touch when the column is present and non-blank.
        for f, default in (('is_active', True), ('is_featured', False), ('show_in_nav', True)):
            if clean(row.get(f)) != '':
                setattr(obj, f, parse_bool(row.get(f), default))
        if clean(row.get('order')) != '':
            obj.order = parse_int(row.get('order'), 'order', 0) or 0

        obj.full_clean(exclude=['slug'])
        obj.save()
        return 'created' if is_new else 'updated'

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
class ProductAdmin(SpreadsheetImportMixin, admin.ModelAdmin):
    list_display   = ('_thumb', 'name', 'sku', 'category', 'brand', '_price', '_discount', '_stock', 'is_active', 'is_featured', 'is_trending')
    list_editable  = ('is_active', 'is_featured', 'is_trending')
    list_filter    = ('is_active', 'is_featured', 'is_trending', 'is_new_arrival', 'category', 'brand', 'condition')
    search_fields  = ('name', 'sku', 'brand__name', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    inlines        = [ProductImageInline, ProductAttributeValueInline, ProductVariantInline, FAQInline]
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'sku')
    list_per_page  = 25
    actions = ['mark_featured', 'unmark_featured', 'mark_trending',
               'mark_out_of_stock', 'restock_default', 'apply_10_discount', 'clear_discount']
    fieldsets = (
        ('Basic',       {'fields': ('name', 'slug', 'sku', 'category', 'brand', 'condition', 'color')}),
        ('Description', {'fields': ('short_description', 'description')}),
        ('Pricing',     {'fields': ('price', 'sale_price', 'cost_price')}),
        ('Inventory',   {'fields': ('stock', 'low_stock_threshold', 'warranty', 'weight')}),
        ('Flags',       {'fields': ('is_active', 'is_featured', 'is_trending', 'is_new_arrival')}),
        ('SEO',         {'fields': ('meta_title', 'meta_description', 'meta_keywords'), 'classes': ('collapse',)}),
        ('Stats',       {'fields': ('views_count', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    # ── Spreadsheet import ─────────────────────────────────────────
    import_title = 'Import products'
    import_intro = ('Bulk-create or update products with full configuration — pricing, '
                    'inventory, flags, attributes, variants and FAQs — from a CSV/Excel sheet. '
                    'Import the referenced <strong>categories first</strong>. Existing products are '
                    'matched by <code>sku</code>, then <code>slug</code>, then <code>name</code>, and updated in place.')
    import_columns = [
        ('name',                True,  'Product name.'),
        ('category',            True,  'Category referenced by name or slug. Must already exist — import categories first.'),
        ('price',               True,  'Regular price, e.g. <code>59999</code> or <code>59,999.00</code>.'),
        ('sku',                 False, 'Stock-keeping unit. Auto-generated when blank; used as the primary match key on re-import.'),
        ('slug',                False, 'URL slug. Auto-generated from the name when blank.'),
        ('brand',               False, 'Brand name — created automatically if it does not exist yet.'),
        ('sale_price',          False, 'Discounted price (shown struck-through against the regular price).'),
        ('cost_price',          False, 'Internal cost price.'),
        ('short_description',   False, 'One-line summary (max 500 chars).'),
        ('description',         False, 'Full HTML/plain description.'),
        ('stock',               False, 'Units in stock, integer (default 0).'),
        ('low_stock_threshold', False, 'Low-stock warning level, integer (default 5).'),
        ('condition',           False, 'One of <code>new</code>, <code>refurbished</code>, <code>open_box</code> (default new).'),
        ('color',               False, 'Colour label, e.g. <code>Space Grey</code>.'),
        ('weight',              False, 'Weight in kg, decimal.'),
        ('warranty',            False, 'Warranty text, e.g. <code>1 Year</code>.'),
        ('is_active',           False, 'true / false (default true).'),
        ('is_featured',         False, 'true / false (default false).'),
        ('is_trending',         False, 'true / false (default false).'),
        ('is_new_arrival',      False, 'true / false (default true).'),
        ('meta_title',          False, 'SEO title.'),
        ('meta_description',    False, 'SEO description.'),
        ('meta_keywords',       False, 'SEO keywords.'),
        ('attributes',          False, 'Spec sheet as <code>Key=Value</code> pairs separated by <code>|</code>, '
                                       'e.g. <code>RAM=16GB | Storage=512GB SSD | Screen=15.6"</code>.'),
        ('variants',            False, 'Variants separated by <code>||</code>; each is '
                                       '<code>name;price_modifier;stock;color_code</code>, '
                                       'e.g. <code>Black;0;10;#000000 || Silver;1500;5;#c0c0c0</code>.'),
        ('faqs',                False, 'FAQs separated by <code>||</code>; each is <code>question::answer</code>.'),
        ('image_urls',          False, 'Image URLs separated by <code>|</code>; downloaded and attached (first = primary).'),
    ]
    import_sample_row = {
        'name': 'Acme UltraBook 14 Pro', 'category': 'laptops', 'price': '89999',
        'sku': 'ACME-UB14-PRO', 'slug': '', 'brand': 'Acme', 'sale_price': '84999',
        'cost_price': '72000', 'short_description': '14-inch ultrabook with OLED display.',
        'description': 'Full-length marketing description goes here.', 'stock': '25',
        'low_stock_threshold': '5', 'condition': 'new', 'color': 'Space Grey',
        'weight': '1.2', 'warranty': '1 Year', 'is_active': 'true', 'is_featured': 'true',
        'is_trending': 'false', 'is_new_arrival': 'true',
        'meta_title': 'Acme UltraBook 14 Pro', 'meta_description': 'Buy the Acme UltraBook 14 Pro.',
        'meta_keywords': 'ultrabook, laptop, acme',
        'attributes': 'RAM=16GB | Storage=512GB SSD | Screen=14" OLED',
        'variants': 'Black;0;10;#000000 || Silver;1500;5;#c0c0c0',
        'faqs': 'Does it support Thunderbolt?::Yes, two TB4 ports. || Is the RAM upgradable?::No, it is soldered.',
        'image_urls': '',
    }

    def import_row(self, row, request):
        from core.models import Brand

        name = clean(row.get('name'))
        if not name:
            raise ValueError('"name" is required.')

        # Category is mandatory and must already exist.
        cat_ref = clean(row.get('category'))
        if not cat_ref:
            raise ValueError('"category" is required.')
        category = (Category.objects.filter(slug=cat_ref).first()
                    or Category.objects.filter(name__iexact=cat_ref).first())
        if not category:
            raise ValueError(f'category "{cat_ref}" not found — import categories first.')

        price = parse_decimal(row.get('price'), 'price')
        if price is None:
            raise ValueError('"price" is required.')

        sku  = clean(row.get('sku'))
        slug = clean(row.get('slug'))

        # Match by sku, then slug, then name.
        obj = None
        if sku:
            obj = Product.objects.filter(sku=sku).first()
        if obj is None and slug:
            obj = Product.objects.filter(slug=slug).first()
        if obj is None:
            obj = Product.objects.filter(name__iexact=name).first()
        is_new = obj is None
        if is_new:
            obj = Product(name=name)
            if sku:
                obj.sku = sku
            if slug:
                obj.slug = slug

        obj.name     = name
        obj.category = category
        obj.price    = price
        if sku:
            obj.sku = sku
        if slug:
            obj.slug = slug

        # Brand — created on demand.
        brand_ref = clean(row.get('brand'))
        if brand_ref:
            obj.brand = Brand.objects.filter(name__iexact=brand_ref).first() \
                        or Brand.objects.create(name=brand_ref)

        # Decimal fields.
        for f in ('sale_price', 'cost_price', 'weight'):
            if clean(row.get(f)) != '':
                setattr(obj, f, parse_decimal(row.get(f), f))

        # Integer fields.
        if clean(row.get('stock')) != '':
            obj.stock = parse_int(row.get('stock'), 'stock', 0) or 0
        if clean(row.get('low_stock_threshold')) != '':
            obj.low_stock_threshold = parse_int(row.get('low_stock_threshold'), 'low_stock_threshold', 5) or 5

        # Plain text fields.
        for f in ('short_description', 'description', 'color', 'warranty',
                  'meta_title', 'meta_description', 'meta_keywords'):
            val = clean(row.get(f))
            if val:
                setattr(obj, f, val)

        # Condition (validated choice).
        cond = clean(row.get('condition')).lower()
        if cond:
            valid = {c[0] for c in Product.CONDITION_CHOICES}
            if cond not in valid:
                raise ValueError(f'condition "{cond}" must be one of {", ".join(sorted(valid))}.')
            obj.condition = cond

        # Booleans.
        for f, default in (('is_active', True), ('is_featured', False),
                           ('is_trending', False), ('is_new_arrival', True)):
            if clean(row.get(f)) != '':
                setattr(obj, f, parse_bool(row.get(f), default))

        obj.full_clean(exclude=['slug', 'sku'])
        obj.save()

        # Related config (only replaced when the column carries a value).
        self._import_attributes(obj, row.get('attributes'))
        self._import_variants(obj, row.get('variants'))
        self._import_faqs(obj, row.get('faqs'))
        self._import_images(obj, row.get('image_urls'))

        return 'created' if is_new else 'updated'

    # ── Related-object importers ───────────────────────────────────
    def _import_attributes(self, product, raw):
        text = clean(raw)
        if not text:
            return
        for chunk in text.split('|'):
            chunk = chunk.strip()
            if not chunk or '=' not in chunk:
                continue
            key, value = chunk.split('=', 1)
            key, value = key.strip(), value.strip()
            if not key:
                continue
            attr, _ = ProductAttribute.objects.get_or_create(name=key)
            ProductAttributeValue.objects.update_or_create(
                product=product, attribute=attr, defaults={'value': value})

    def _import_variants(self, product, raw):
        text = clean(raw)
        if not text:
            return
        product.variants.all().delete()  # column present -> full replace
        for entry in text.split('||'):
            parts = [p.strip() for p in entry.split(';')]
            if not parts or not parts[0]:
                continue
            vname = parts[0]
            pm    = parse_decimal(parts[1], 'variant price_modifier') if len(parts) > 1 and parts[1] else 0
            stock = parse_int(parts[2], 'variant stock', 0) if len(parts) > 2 and parts[2] else 0
            color = parts[3] if len(parts) > 3 else ''
            ProductVariant.objects.create(
                product=product, name=vname, price_modifier=pm or 0,
                stock=stock or 0, color_code=color)

    def _import_faqs(self, product, raw):
        text = clean(raw)
        if not text:
            return
        product.faqs.all().delete()  # column present -> full replace
        for i, entry in enumerate(text.split('||')):
            if '::' not in entry:
                continue
            q, a = entry.split('::', 1)
            q, a = q.strip(), a.strip()
            if q and a:
                FAQ.objects.create(product=product, question=q, answer=a, order=i)

    def _import_images(self, product, raw):
        text = clean(raw)
        if not text:
            return
        import os
        from urllib.parse import urlparse
        from urllib.request import urlopen, Request
        from django.core.files.base import ContentFile

        urls = [u.strip() for u in text.split('|') if u.strip()]
        has_primary = product.images.filter(is_primary=True).exists()
        for idx, url in enumerate(urls):
            try:
                req = Request(url, headers={'User-Agent': 'TechZone-Importer/1.0'})
                with urlopen(req, timeout=10) as resp:
                    data = resp.read(8 * 1024 * 1024)  # cap at 8 MB
                filename = os.path.basename(urlparse(url).path) or f'import-{idx}.jpg'
                img = ProductImage(product=product, is_primary=(not has_primary and idx == 0), order=idx)
                img.image.save(filename, ContentFile(data), save=True)
            except Exception:
                # Best effort: a broken image URL must not fail the whole row.
                continue

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

    # ── Bulk actions ──────────────────────────────────────────────
    @admin.action(description='⭐ Mark as featured')
    def mark_featured(self, request, queryset):
        n = queryset.update(is_featured=True)
        self.message_user(request, f'{n} product(s) marked featured.')

    @admin.action(description='Remove featured flag')
    def unmark_featured(self, request, queryset):
        n = queryset.update(is_featured=False)
        self.message_user(request, f'{n} product(s) un-featured.')

    @admin.action(description='🔥 Mark as trending')
    def mark_trending(self, request, queryset):
        n = queryset.update(is_trending=True)
        self.message_user(request, f'{n} product(s) marked trending.')

    @admin.action(description='🚫 Mark out of stock')
    def mark_out_of_stock(self, request, queryset):
        n = queryset.update(stock=0)
        self.message_user(request, f'{n} product(s) set to 0 stock.')

    @admin.action(description='Restock to 10 units')
    def restock_default(self, request, queryset):
        n = queryset.update(stock=10)
        self.message_user(request, f'{n} product(s) restocked to 10.')

    @admin.action(description='💸 Apply 10%% discount')
    def apply_10_discount(self, request, queryset):
        count = 0
        for p in queryset:
            p.sale_price = (p.price * Decimal('0.90')).quantize(Decimal('0.01'))
            p.save(update_fields=['sale_price'])
            count += 1
        self.message_user(request, f'10% discount applied to {count} product(s).')

    @admin.action(description='Clear discount (sale price)')
    def clear_discount(self, request, queryset):
        n = queryset.update(sale_price=None)
        self.message_user(request, f'Discount cleared on {n} product(s).')


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
class ProductInquiryAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display  = ('name', 'email', 'phone', 'product', 'status', 'created_at')
    list_editable = ('status',)
    list_filter   = ('status',)
    search_fields = ('name', 'email', 'product__name')
    readonly_fields = ('created_at',)
    actions       = ['export_as_csv']


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

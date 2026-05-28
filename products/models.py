from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import uuid


class Category(models.Model):
    name             = models.CharField(max_length=100)
    slug             = models.SlugField(unique=True, blank=True, max_length=120)
    parent           = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    image            = models.ImageField(upload_to='categories/icons/', blank=True, null=True)
    banner           = models.ImageField(upload_to='categories/banners/', blank=True, null=True)
    banner_mobile    = models.ImageField(upload_to='categories/banners/mobile/', blank=True, null=True)
    icon             = models.CharField(max_length=60, blank=True, help_text='Tabler icon class e.g. ti-device-mobile')
    color            = models.CharField(max_length=7, blank=True, default='#2563eb', help_text='Hex colour for UI accent')
    description      = models.TextField(blank=True)
    meta_title       = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=320, blank=True)
    meta_keywords    = models.CharField(max_length=300, blank=True)
    is_active        = models.BooleanField(default=True)
    is_featured      = models.BooleanField(default=False)
    show_in_nav      = models.BooleanField(default=True, help_text='Show in top navigation bar')
    order            = models.PositiveIntegerField(default=0)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['order', 'name']
        verbose_name        = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} › {self.name}'
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'; n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category', kwargs={'slug': self.slug})

    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()

    @property
    def total_product_count(self):
        ids = [self.pk] + [c.pk for c in self.get_all_descendants()]
        return Product.objects.filter(category_id__in=ids, is_active=True).count()

    def get_all_descendants(self):
        result = []
        for child in self.children.filter(is_active=True):
            result.append(child)
            result.extend(child.get_all_descendants())
        return result

    def get_breadcrumbs(self):
        crumbs, node = [], self
        while node:
            crumbs.insert(0, (node.name, node.get_absolute_url()))
            node = node.parent
        return crumbs

    def get_ancestors(self):
        ancestors, node = [], self.parent
        while node:
            ancestors.insert(0, node); node = node.parent
        return ancestors

    def get_siblings(self):
        return Category.objects.filter(parent=self.parent, is_active=True).exclude(pk=self.pk)

    @property
    def is_root(self):
        return self.parent is None

    def get_featured_products(self, limit=8):
        ids = [self.pk] + [c.pk for c in self.get_all_descendants()]
        return (Product.objects.filter(category_id__in=ids, is_active=True)
                .select_related('brand').prefetch_related('images')
                .order_by('-is_featured', '-created_at')[:limit])


class Product(models.Model):
    CONDITION_CHOICES = [('new','New'),('refurbished','Refurbished'),('open_box','Open Box')]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name                = models.CharField(max_length=300)
    slug                = models.SlugField(unique=True, blank=True, max_length=350)
    sku                 = models.CharField(max_length=100, unique=True, blank=True)
    category            = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    brand               = models.ForeignKey('core.Brand', on_delete=models.PROTECT, related_name='products', null=True, blank=True)
    short_description   = models.TextField(max_length=500, blank=True)
    description         = models.TextField(blank=True)
    price               = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price          = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price          = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock               = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    condition           = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    color               = models.CharField(max_length=50, blank=True, help_text='e.g. Black, Silver, Blue')
    is_active           = models.BooleanField(default=True)
    is_featured         = models.BooleanField(default=False)
    is_trending         = models.BooleanField(default=False)
    is_new_arrival      = models.BooleanField(default=True)
    weight              = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    warranty            = models.CharField(max_length=100, blank=True)
    meta_title          = models.CharField(max_length=200, blank=True)
    meta_description    = models.TextField(max_length=320, blank=True)
    meta_keywords       = models.CharField(max_length=300, blank=True)
    views_count         = models.PositiveIntegerField(default=0)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name); slug = base; n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'; n += 1
            self.slug = slug
        if not self.sku:
            self.sku = f'TZ-{str(self.id)[:8].upper()}'
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})

    @property
    def effective_price(self):
        return self.sale_price if self.sale_price else self.price

    @property
    def discount_percent(self):
        if self.sale_price and self.price > 0:
            return int(((self.price - self.sale_price) / self.price) * 100)
        return 0

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_threshold

    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        return img or self.images.first()


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image      = models.ImageField(upload_to='products/')
    alt_text   = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.product.name} – img {self.order}'


class ProductAttribute(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self): return self.name

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductAttributeValue(models.Model):
    product   = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    value     = models.CharField(max_length=200)

    class Meta:
        unique_together = ['product', 'attribute']

    def __str__(self): return f'{self.attribute.name}: {self.value}'


class ProductVariant(models.Model):
    product        = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name           = models.CharField(max_length=100)
    sku            = models.CharField(max_length=100, blank=True)
    price_modifier = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    stock          = models.PositiveIntegerField(default=0)
    image          = models.ImageField(upload_to='variants/', blank=True, null=True)
    color_code     = models.CharField(max_length=7, blank=True)
    is_active      = models.BooleanField(default=True)

    def __str__(self): return f'{self.product.name} – {self.name}'


class Review(models.Model):
    product              = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user                 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name                 = models.CharField(max_length=100)
    email                = models.EmailField()
    rating               = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title                = models.CharField(max_length=200, blank=True)
    content              = models.TextField()
    pros                 = models.TextField(blank=True)
    cons                 = models.TextField(blank=True)
    is_approved          = models.BooleanField(default=False)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count        = models.PositiveIntegerField(default=0)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self): return f'{self.name} – {self.product.name} ({self.rating}★)'


class FAQ(models.Model):
    product   = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='faqs')
    question  = models.CharField(max_length=300)
    answer    = models.TextField()
    order     = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self): return self.question


class Wishlist(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self): return f'{self.user.username} – {self.product.name}'


class ProductInquiry(models.Model):
    STATUS_CHOICES = [('new','New'),('in_progress','In Progress'),('resolved','Resolved'),('closed','Closed')]

    product       = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inquiries')
    name          = models.CharField(max_length=100)
    email         = models.EmailField()
    phone         = models.CharField(max_length=20, blank=True)
    message       = models.TextField()
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    is_read       = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product Inquiry'
        verbose_name_plural = 'Product Inquiries'

    def __str__(self): return f'{self.name} – {self.product.name}'


class StockAlert(models.Model):
    product   = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_alerts')
    email     = models.EmailField()
    name      = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    notified  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'email']
        ordering = ['-created_at']

    def __str__(self): return f'{self.email} – {self.product.name}'

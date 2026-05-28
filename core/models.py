from django.db import models
from django.utils.text import slugify


class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Banner(models.Model):
    BANNER_TYPE_CHOICES = [
        ('hero', 'Hero Banner'),
        ('promo', 'Promotional Banner'),
        ('category', 'Category Banner'),
        ('sidebar', 'Sidebar Banner'),
    ]
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='banners/')
    mobile_image = models.ImageField(upload_to='banners/mobile/', blank=True, null=True)
    link = models.URLField(blank=True)
    button_text = models.CharField(max_length=50, default='Shop Now')
    banner_type = models.CharField(max_length=20, choices=BANNER_TYPE_CHOICES, default='hero')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    badge_text = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'), ('instagram', 'Instagram'),
        ('twitter', 'Twitter / X'), ('youtube', 'YouTube'),
        ('linkedin', 'LinkedIn'), ('whatsapp', 'WhatsApp'),
    ]
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.get_platform_display()

    def get_icon_class(self):
        icons = {
            'facebook': 'ti-brand-facebook', 'instagram': 'ti-brand-instagram',
            'twitter': 'ti-brand-twitter', 'youtube': 'ti-brand-youtube',
            'linkedin': 'ti-brand-linkedin', 'whatsapp': 'ti-brand-whatsapp',
        }
        return icons.get(self.platform, 'ti-world')


class WhyChooseUs(models.Model):
    icon = models.CharField(max_length=50, default='ti-shield-check')
    title = models.CharField(max_length=100)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class ContactInquiry(models.Model):
    INQUIRY_TYPE_CHOICES = [
        ('general', 'General'), ('product', 'Product'),
        ('service', 'Service'), ('bulk', 'Bulk Order'), ('support', 'Support'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'), ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'), ('closed', 'Closed'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.subject[:50]}'


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='TechZone')
    tagline = models.CharField(max_length=200, default='Your Premium Electronics Destination')
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    google_maps_embed = models.TextField(blank=True)
    working_hours = models.CharField(max_length=200, blank=True, default='Mon–Sat: 10am – 8pm')
    meta_description = models.TextField(max_length=300, blank=True)
    meta_keywords = models.CharField(max_length=300, blank=True)
    google_analytics_id = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

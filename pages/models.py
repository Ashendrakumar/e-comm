from django.db import models
from django.utils.text import slugify
from django.urls import reverse


# ══════════════════════════════════════════════════════════════════
# MODULE 7 — SERVICES
# ══════════════════════════════════════════════════════════════════

class Service(models.Model):
    icon             = models.CharField(max_length=50, default='ti-tool', help_text='Tabler icon class, e.g. ti-tool')
    title            = models.CharField(max_length=100)
    slug             = models.SlugField(unique=True, blank=True)
    short_description = models.TextField(max_length=300)
    description      = models.TextField(blank=True, help_text='Full description shown on the service detail page')
    image            = models.ImageField(upload_to='services/', blank=True, null=True)
    banner           = models.ImageField(upload_to='services/banners/', blank=True, null=True)
    color            = models.CharField(max_length=7, blank=True, default='#2563eb')
    price_info       = models.CharField(max_length=120, blank=True, help_text='e.g. "Starting at ₹499" or "Free"')

    cta_text         = models.CharField(max_length=100, default='Get Started')
    cta_link         = models.CharField(max_length=200, blank=True, help_text='Optional external/internal URL. Defaults to the inquiry form.')

    meta_title       = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=320, blank=True)
    meta_keywords    = models.CharField(max_length=300, blank=True)

    is_active        = models.BooleanField(default=True)
    is_featured      = models.BooleanField(default=False)
    order            = models.PositiveIntegerField(default=0)
    created_at       = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title); slug = base; n = 1
            while Service.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'; n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('pages:service_detail', kwargs={'slug': self.slug})


class ServiceFeature(models.Model):
    """A highlight / bullet point shown on a service detail page."""
    service     = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='features')
    icon        = models.CharField(max_length=50, default='ti-circle-check')
    title       = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True)
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.service.title} — {self.title}'


class ServiceInquiry(models.Model):
    """Inquiry submitted from a service detail page."""
    STATUS_CHOICES = [('new', 'New'), ('in_progress', 'In Progress'), ('resolved', 'Resolved'), ('closed', 'Closed')]

    service    = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='inquiries')
    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    phone      = models.CharField(max_length=20, blank=True)
    city       = models.CharField(max_length=100, blank=True)
    message    = models.TextField()
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Service Inquiry'
        verbose_name_plural = 'Service Inquiries'

    def __str__(self):
        svc = self.service.title if self.service else 'General'
        return f'{self.name} — {svc}'


# ══════════════════════════════════════════════════════════════════
# MODULE 8 — SERVING AREAS
# ══════════════════════════════════════════════════════════════════

class ServingArea(models.Model):
    city             = models.CharField(max_length=100)
    slug             = models.SlugField(unique=True, blank=True)
    state            = models.CharField(max_length=100, default='Gujarat')
    description      = models.TextField(blank=True)
    contact_phone    = models.CharField(max_length=20, blank=True)
    contact_email    = models.EmailField(blank=True)
    address          = models.TextField(blank=True)
    pincodes         = models.CharField(max_length=300, blank=True, help_text='Comma-separated pincodes served')
    map_embed        = models.TextField(blank=True, help_text='Google Maps embed iframe HTML')
    meta_title       = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=320, blank=True)
    is_active        = models.BooleanField(default=True)
    is_featured      = models.BooleanField(default=False)

    class Meta:
        ordering = ['city']

    def __str__(self):
        return f'{self.city}, {self.state}'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.city); slug = base; n = 1
            while ServingArea.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'; n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('pages:area_detail', kwargs={'slug': self.slug})

    @property
    def pincode_list(self):
        return [p.strip() for p in self.pincodes.split(',') if p.strip()]


# ══════════════════════════════════════════════════════════════════
# MODULE 6 — CMS MANAGEMENT (Flat pages + site-wide FAQs)
# ══════════════════════════════════════════════════════════════════

class FlatPage(models.Model):
    """Editable CMS content page (About, Privacy, Terms, etc.)."""
    title            = models.CharField(max_length=200)
    slug             = models.SlugField(unique=True, blank=True, max_length=220)
    content          = models.TextField(help_text='Page body. Basic HTML allowed.')
    icon             = models.CharField(max_length=50, blank=True, default='ti-file-text')
    meta_title       = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=320, blank=True)
    meta_keywords    = models.CharField(max_length=300, blank=True)
    show_in_footer   = models.BooleanField(default=True)
    is_active        = models.BooleanField(default=True)
    order            = models.PositiveIntegerField(default=0)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['order', 'title']
        verbose_name        = 'CMS Page'
        verbose_name_plural = 'CMS Pages'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title); slug = base; n = 1
            while FlatPage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'; n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('pages:flatpage', kwargs={'slug': self.slug})


class FAQCategory(models.Model):
    name      = models.CharField(max_length=100)
    slug      = models.SlugField(unique=True, blank=True)
    icon      = models.CharField(max_length=50, blank=True, default='ti-help-circle')
    order     = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering            = ['order', 'name']
        verbose_name        = 'FAQ Category'
        verbose_name_plural = 'FAQ Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class GeneralFAQ(models.Model):
    """Site-wide FAQ (distinct from product-specific FAQs)."""
    category  = models.ForeignKey(FAQCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='faqs')
    question  = models.CharField(max_length=300)
    answer    = models.TextField()
    order     = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering            = ['order']
        verbose_name        = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question

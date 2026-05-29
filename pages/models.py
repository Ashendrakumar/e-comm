from django.db import models
from django.utils.text import slugify
import json


class Service(models.Model):
    icon = models.CharField(max_length=50, default='ti-tool')
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.TextField(max_length=300)
    description = models.TextField(blank=True)
    cta_text = models.CharField(max_length=100, default='Get Started')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class ServingArea(models.Model):
    city = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    state = models.CharField(max_length=100, default='Gujarat')
    description = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['city']

    def __str__(self):
        return f'{self.city}, {self.state}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.city)
        super().save(*args, **kwargs)


class HomepageBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.TextField(blank=True)
    image = models.ImageField(upload_to='banners/')
    image_mobile = models.ImageField(upload_to='banners/mobile/', blank=True)
    link = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, default='Learn More')
    badge_text = models.CharField(max_length=50, blank=True)
    badge_color = models.CharField(max_length=7, default='#FF6B35')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Homepage Banners'
        indexes = [
            models.Index(fields=['order', 'is_active']),
        ]

    def __str__(self):
        return self.title


SECTION_TYPE_CHOICES = [
    ('hero', 'Hero Banner'),
    ('featured_products', 'Featured Products'),
    ('testimonials', 'Testimonials'),
    ('why_choose_us', 'Why Choose Us'),
    ('categories', 'Categories'),
    ('brands', 'Brand Partners'),
]


class HomepageSection(models.Model):
    name = models.CharField(max_length=200)
    section_type = models.CharField(max_length=50, choices=SECTION_TYPE_CHOICES)
    title = models.CharField(max_length=200, blank=True)
    subtitle = models.TextField(blank=True)
    content = models.JSONField(default=dict)
    template = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Homepage Sections'
        indexes = [
            models.Index(fields=['order', 'is_active']),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_section_type_display()})'

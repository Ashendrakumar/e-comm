from django.db import models
from django.utils.text import slugify


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

from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from taggit.managers import TaggableManager


class BlogCategory(models.Model):
    name             = models.CharField(max_length=100)
    slug             = models.SlugField(unique=True, blank=True, max_length=120)
    description      = models.TextField(blank=True)
    color            = models.CharField(max_length=7, blank=True, default='#2563eb')
    icon             = models.CharField(max_length=60, blank=True, default='ti-news')
    meta_title       = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=320, blank=True)
    is_active        = models.BooleanField(default=True)
    order            = models.PositiveIntegerField(default=0)

    class Meta:
        ordering            = ['order', 'name']
        verbose_name        = 'Blog Category'
        verbose_name_plural = 'Blog Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name); slug = base; n = 1
            while BlogCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'; n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})

    @property
    def post_count(self):
        return self.posts.filter(status='published').count()


class BlogPost(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('published', 'Published')]

    title            = models.CharField(max_length=250)
    slug             = models.SlugField(unique=True, blank=True, max_length=300)
    category         = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    author           = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts')
    author_name      = models.CharField(max_length=100, blank=True, help_text='Override displayed author name')
    featured_image   = models.ImageField(upload_to='blog/', blank=True, null=True)
    excerpt          = models.TextField(max_length=400, blank=True, help_text='Short summary shown in listings')
    content          = models.TextField(help_text='Full article body. Basic HTML is allowed.')
    tags             = TaggableManager(blank=True)

    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured      = models.BooleanField(default=False)
    allow_comments   = models.BooleanField(default=True)
    views_count      = models.PositiveIntegerField(default=0)
    reading_minutes  = models.PositiveIntegerField(default=0, help_text='Auto-estimated on save if left 0')

    meta_title       = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=320, blank=True)
    meta_keywords    = models.CharField(max_length=300, blank=True)

    published_at     = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['-published_at', '-created_at']
        verbose_name        = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
        indexes             = [models.Index(fields=['status', '-published_at'])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title); slug = base; n = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'; n += 1
            self.slug = slug
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        if not self.excerpt and self.content:
            from django.utils.html import strip_tags
            self.excerpt = strip_tags(self.content)[:280]
        if not self.reading_minutes and self.content:
            from django.utils.html import strip_tags
            words = len(strip_tags(self.content).split())
            self.reading_minutes = max(1, round(words / 200))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})

    @property
    def display_author(self):
        if self.author_name:
            return self.author_name
        if self.author:
            return self.author.get_full_name() or self.author.username
        return 'TechZone Team'

    @property
    def approved_comments(self):
        return self.comments.filter(is_approved=True)


class BlogComment(models.Model):
    post        = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    name        = models.CharField(max_length=100)
    email       = models.EmailField()
    content     = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['created_at']
        verbose_name        = 'Blog Comment'
        verbose_name_plural = 'Blog Comments'

    def __str__(self):
        return f'{self.name} on {self.post.title[:40]}'

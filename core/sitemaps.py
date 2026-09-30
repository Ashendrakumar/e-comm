from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from products.models import Product, Category
from pages.models import Service, ServingArea, FlatPage
from blog.models import BlogPost, BlogCategory


class StaticViewSitemap(Sitemap):
    priority   = 0.7
    changefreq = 'weekly'

    def items(self):
        return [
            'core:homepage', 'core:about', 'core:contact',
            'products:list', 'products:categories',
            'pages:services', 'pages:serving_areas', 'pages:faqs',
            'blog:list',
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    priority   = 0.9
    changefreq = 'daily'

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    priority   = 0.8
    changefreq = 'weekly'

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class BlogPostSitemap(Sitemap):
    priority   = 0.7
    changefreq = 'weekly'

    def items(self):
        return BlogPost.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.updated_at


class BlogCategorySitemap(Sitemap):
    priority   = 0.5
    changefreq = 'weekly'

    def items(self):
        return BlogCategory.objects.filter(is_active=True)


class ServiceSitemap(Sitemap):
    priority   = 0.7
    changefreq = 'monthly'

    def items(self):
        return Service.objects.filter(is_active=True)


class ServingAreaSitemap(Sitemap):
    priority   = 0.6
    changefreq = 'monthly'

    def items(self):
        return ServingArea.objects.filter(is_active=True)


class FlatPageSitemap(Sitemap):
    priority   = 0.4
    changefreq = 'monthly'

    def items(self):
        return FlatPage.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    'static':         StaticViewSitemap,
    'products':       ProductSitemap,
    'categories':     CategorySitemap,
    'blog':           BlogPostSitemap,
    'blog_categories': BlogCategorySitemap,
    'services':       ServiceSitemap,
    'areas':          ServingAreaSitemap,
    'pages':          FlatPageSitemap,
}

"""
Custom admin site for TechZone (Module 11 — Admin Dashboard).

Adds branding and a stats dashboard to the admin index. Registered as the
default admin site via ``core.apps.TechZoneAdminConfig`` so every existing
``@admin.register`` continues to work unchanged.
"""
from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta


class TechZoneAdminConfig(AdminConfig):
    """Replaces the default admin site with our branded dashboard site."""
    default_site = 'core.admin_site.TechZoneAdminSite'


class TechZoneAdminSite(admin.AdminSite):
    site_header    = 'TechZone Administration'
    site_title     = 'TechZone Admin'
    index_title    = 'Dashboard'
    index_template = 'admin/techzone_index.html'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context['dashboard'] = self._dashboard_stats()
        except Exception:
            # Never let a stats query break the admin index.
            extra_context['dashboard'] = None
        return super().index(request, extra_context)

    def _dashboard_stats(self):
        from products.models import Product, Category, Review
        from core.models import Brand, ContactInquiry, NewsletterSubscription
        from pages.models import ServiceInquiry

        week_ago = timezone.now() - timedelta(days=7)

        # Top categories by active product count
        top_categories = (
            Category.objects.filter(is_active=True)
            .annotate(n=Count('products', filter=Q(products__is_active=True)))
            .order_by('-n')[:5]
        )

        return {
            'cards': [
                {'label': 'Products',        'value': Product.objects.count(),
                 'sub': f'{Product.objects.filter(is_active=True).count()} active', 'icon': '📦'},
                {'label': 'Categories',      'value': Category.objects.count(), 'icon': '🗂️'},
                {'label': 'Brands',          'value': Brand.objects.count(), 'icon': '🏷️'},
                {'label': 'Reviews',         'value': Review.objects.count(),
                 'sub': f'{Review.objects.filter(is_approved=False).count()} pending', 'icon': '⭐'},
                {'label': 'Contact inquiries (7d)',
                 'value': ContactInquiry.objects.filter(created_at__gte=week_ago).count(),
                 'sub': f'{ContactInquiry.objects.filter(status="new").count()} new total', 'icon': '✉️'},
                {'label': 'Service inquiries (7d)',
                 'value': ServiceInquiry.objects.filter(created_at__gte=week_ago).count(), 'icon': '🛠️'},
                {'label': 'Newsletter subs',
                 'value': NewsletterSubscription.objects.filter(is_active=True).count(), 'icon': '📰'},
                {'label': 'Out of stock',
                 'value': Product.objects.filter(stock=0, is_active=True).count(), 'icon': '🚫'},
            ],
            'top_categories': [{'name': c.name, 'count': c.n} for c in top_categories],
            'low_stock': list(
                Product.objects.filter(is_active=True, stock__gt=0, stock__lte=5)
                .values('name', 'stock')[:8]
            ),
        }

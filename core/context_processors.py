from django.conf import settings
from django.core.cache import cache
from .models import SiteSettings, SocialLink, Brand
from products.models import Category
from pages.models import FlatPage, Service

# Global navigation/footer data is identical for every visitor, so cache it
# for a few minutes instead of re-querying on every request.
NAV_CACHE_KEY     = 'global_nav_context_v1'
NAV_CACHE_SECONDS = 300


def _build_nav_context():
    return {
        'nav_categories': list(Category.objects
                               .filter(is_active=True, parent=None, show_in_nav=True)
                               .prefetch_related('children')
                               .order_by('order', 'name')[:10]),
        'featured_brands': list(Brand.objects.filter(is_featured=True, is_active=True)[:8]),
        'social_links':    list(SocialLink.objects.filter(is_active=True)),
        'footer_pages':    list(FlatPage.objects.filter(is_active=True, show_in_footer=True).order_by('order')),
        'footer_services': list(Service.objects.filter(is_active=True).order_by('order')[:6]),
    }


def global_context(request):
    nav = cache.get(NAV_CACHE_KEY)
    if nav is None:
        nav = _build_nav_context()
        cache.set(NAV_CACHE_KEY, nav, NAV_CACHE_SECONDS)
    return {
        'site_settings': SiteSettings.get_settings(),
        'use_compiled_css': getattr(settings, 'TAILWIND_COMPILED', False),
        **nav,
    }

from .models import SiteSettings, SocialLink, Brand
from products.models import Category


def global_context(request):
    site_settings   = SiteSettings.get_settings()
    nav_categories  = (Category.objects
                       .filter(is_active=True, parent=None, show_in_nav=True)
                       .prefetch_related('children')
                       .order_by('order', 'name')[:10])
    featured_brands = Brand.objects.filter(is_featured=True, is_active=True)[:8]
    social_links    = SocialLink.objects.filter(is_active=True)
    return {
        'site_settings':  site_settings,
        'nav_categories': nav_categories,
        'featured_brands': featured_brands,
        'social_links':   social_links,
    }

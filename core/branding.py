"""The organisation's display name, from Site Settings (admin) — never hard-code it.

Templates get it as {{ site_name }} via core.context_processors.global_context;
Python code calls get_site_name().
"""
DEFAULT_SITE_NAME = 'TechZone'


def get_site_name():
    from .models import SiteSettings
    return (SiteSettings.get_settings().site_name or '').strip() or DEFAULT_SITE_NAME

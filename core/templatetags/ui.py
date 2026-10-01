"""Shared UI template tags.

{% load ui %}

Breadcrumbs — one component for every page (renders partials/breadcrumbs.html):

    {% breadcrumbs "Products" list_url "Compare" %}       inline title/url pairs;
                                                          the last title is the current page
    {% breadcrumbs trail=breadcrumbs %}                   a list of (title, url) tuples or
                                                          {"title", "url"} dicts from a view
    {% breadcrumbs "Categories" cats_url trail=crumbs %}  pairs are placed before the trail
    {% block breadcrumb_bar %}{% breadcrumbs "Contact" bar=True %}{% endblock %}
                                                          the standard: plain bar under the header
    {% breadcrumbs "Contact" on_dark=True align="center" %}   inline on a coloured banner (not used now)

"Home" is prepended automatically unless the trail already starts at the homepage.
"""
from django import template
from django.urls import reverse

register = template.Library()


def _normalise(item):
    if isinstance(item, dict):
        return {'title': item.get('title') or item.get('name'), 'url': item.get('url')}
    title, url = item
    return {'title': title, 'url': url}


@register.filter
def absolute_url(url, request):
    """{{ img.image.url|absolute_url:request }} -> a full https://… URL.

    Media URLs are relative ("/media/…") on local disk but already absolute on
    Supabase Storage; build_absolute_uri leaves absolute ones untouched.
    """
    if not url:
        return ''
    return request.build_absolute_uri(url) if request else url


@register.inclusion_tag('partials/breadcrumbs.html', takes_context=True)
def breadcrumbs(context, *args, trail=None, on_dark=False, align='start', bar=False):
    home = reverse('core:homepage')
    # Positional args first (title, url, …, title — the final title may stand alone),
    # then the view-supplied trail, so a page can prefix a fixed parent to it.
    crumbs = [{'title': args[i], 'url': args[i + 1] if i + 1 < len(args) else None}
              for i in range(0, len(args), 2)]
    crumbs += [_normalise(c) for c in (trail or [])]
    if not crumbs or crumbs[0]['url'] != home:
        crumbs.insert(0, {'title': 'Home', 'url': home})
    return {'crumbs': crumbs, 'on_dark': on_dark, 'align': align, 'bar': bar, 'request': context.get('request')}

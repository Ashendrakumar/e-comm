from django.conf import settings

from .views import handler404


class FriendlyDebug404Middleware:
    """Show the site's own 404 page in development too.

    With DEBUG on, Django answers unknown URLs (and get_object_or_404 misses)
    with its technical "URLconf" page, so templates/404.html is never seen
    locally. This swaps that page for the real one.

    Left untouched: non-HTML 404s (the JSON API), static/media files, and the
    admin. Set SHOW_TECHNICAL_404 = True in settings to get Django's debug page
    back while tracking down a routing problem. Production (DEBUG off) already
    uses core.views.handler404, so this middleware does nothing there.
    """

    SKIP_PREFIXES = ('/admin/',)

    def __init__(self, get_response):
        self.get_response = get_response
        self.skip = self.SKIP_PREFIXES + tuple(
            p for p in (settings.STATIC_URL, settings.MEDIA_URL) if p and p.startswith('/'))

    def __call__(self, request):
        response = self.get_response(request)
        if (settings.DEBUG
                and not getattr(settings, 'SHOW_TECHNICAL_404', False)
                and response.status_code == 404
                and response.get('Content-Type', '').startswith('text/html')
                and not request.path.startswith(self.skip)
                and not getattr(response, 'is_friendly_404', False)):
            response = handler404(request, None)
            response.is_friendly_404 = True
        return response

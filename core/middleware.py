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

    def __init__(self, get_response):
        self.get_response = get_response
        self.skip = ('/' + settings.ADMIN_URL,) + tuple(
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


class ContentSecurityPolicyMiddleware:
    """Send the Content-Security-Policy built from settings.CSP_DIRECTIVES.

    Off while DEBUG is on (the Tailwind CDN and debug toolbar need looser
    rules locally). CSP_REPORT_ONLY=True sends it as report-only, to try a
    stricter policy without breaking pages.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        directives = getattr(settings, 'CSP_DIRECTIVES', {})
        self.policy = '; '.join(f'{k} {" ".join(v)}'.strip() for k, v in directives.items())
        self.header = ('Content-Security-Policy-Report-Only'
                       if getattr(settings, 'CSP_REPORT_ONLY', False) else 'Content-Security-Policy')

    def __call__(self, request):
        response = self.get_response(request)
        if (getattr(settings, 'CSP_ENABLED', False) and not settings.DEBUG and self.policy
                and self.header not in response):
            response[self.header] = self.policy
        return response


class HealthCheckMiddleware:
    """Answer GET /healthz/ (liveness + database) before anything else runs.

    First in MIDDLEWARE on purpose: Docker and load balancers probe with their
    own Host header over plain HTTP, which ALLOWED_HOSTS validation and the
    HTTPS redirect would otherwise reject.
    """

    PATH = '/healthz/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info != self.PATH:
            return self.get_response(request)
        from django.db import connection
        from django.http import JsonResponse
        try:
            with connection.cursor() as cur:
                cur.execute('SELECT 1')
        except Exception:
            response = JsonResponse({'status': 'error', 'database': 'unreachable'}, status=503)
        else:
            response = JsonResponse({'status': 'ok'})
        response['Cache-Control'] = 'no-store'
        return response

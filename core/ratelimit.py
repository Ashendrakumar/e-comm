"""Abuse protection for the public POST endpoints (contact, newsletter, reviews,
enquiries, "helpful" votes) and the admin login.

Two layers, both cheap:
  * a honeypot field (HONEYPOT_FIELD) that is hidden from people — bots that
    fill every input get a fake "thank you" and nothing is saved;
  * a fixed-window rate limit per client IP and per form, kept in the cache
    (use Redis in production so every gunicorn worker shares the counters).

Settings: RATELIMIT_ENABLED, RATELIMIT_FORMS ("10/10m"), RATELIMIT_LOGIN,
TRUSTED_PROXY_COUNT (see settings/base.py).
"""
import functools
import hashlib
import logging
import re

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

log = logging.getLogger(__name__)

HONEYPOT_FIELD = 'hp_website'
_UNITS = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}


def client_ip(request):
    """The visitor's IP. Behind N trusted proxies, each appends the address it
    saw to X-Forwarded-For, so the real client is N entries from the right —
    anything further left is client-supplied and can be forged."""
    proxies = getattr(settings, 'TRUSTED_PROXY_COUNT', 0)
    if proxies:
        chain = [p.strip() for p in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',') if p.strip()]
        if len(chain) >= proxies:
            return chain[-proxies]
    return request.META.get('REMOTE_ADDR', '')


def parse_rate(rate):
    """'10/10m' -> (10, 600). A bare unit ('5/m') means 1 of that unit."""
    m = re.fullmatch(r'\s*(\d+)\s*/\s*(\d*)\s*([smhd])\s*', rate or '')
    if not m:
        raise ValueError(f'Bad rate {rate!r}; expected e.g. "10/10m"')
    return int(m[1]), int(m[2] or 1) * _UNITS[m[3]]


def hit(request, scope, rate):
    """Count one attempt; True when the caller is over the limit."""
    if not getattr(settings, 'RATELIMIT_ENABLED', True):
        return False
    limit, window = parse_rate(rate)
    ident = hashlib.sha256(client_ip(request).encode()).hexdigest()[:24]
    key = f'rl:{scope}:{ident}'
    if cache.add(key, 1, window):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:                  # expired between add() and incr()
            cache.set(key, 1, window)
            count = 1
    if count > limit:
        if count == limit + 1:
            log.warning('Rate limit hit: scope=%s ip=%s', scope, client_ip(request))
        return True
    return False


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _back(request):
    ref = request.META.get('HTTP_REFERER', '')
    if ref and url_has_allowed_host_and_scheme(ref, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
        return redirect(ref)
    return redirect('core:homepage')


def protect_form(scope, rate=None):
    """Decorate a POST view: honeypot check, then rate limit, then the view."""
    def decorator(view):
        @functools.wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method == 'POST':
                if request.POST.get(HONEYPOT_FIELD):
                    log.info('Honeypot tripped: scope=%s ip=%s', scope, client_ip(request))
                    msg = 'Thank you! We will get back to you shortly.'
                    if _is_ajax(request):
                        return JsonResponse({'success': True, 'message': msg})
                    messages.success(request, msg)
                    return _back(request)
                if hit(request, scope, rate or settings.RATELIMIT_FORMS):
                    msg = 'Too many submissions from your connection. Please wait a few minutes and try again.'
                    if _is_ajax(request):
                        return JsonResponse({'success': False, 'message': msg}, status=429)
                    messages.error(request, msg)
                    return _back(request)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator

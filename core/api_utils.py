"""Shared helpers for the REST API under /api/v1/ (the mobile app's backend).

The API reuses the site's Django forms for validation and the same per-IP rate
limit scopes as the web forms (core.ratelimit), so a visitor has one budget
whether they post from the website or the app.
"""
import hashlib

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response

from .ratelimit import client_ip, hit

TOO_MANY = 'Too many requests from your connection. Please wait a few minutes and try again.'
TRUE_VALUES = ('1', 'true', 'True', 'yes')


def rate_limited(request, scope, rate=None):
    """A 429 Response when this client is over the limit for `scope`, else None."""
    if hit(request, scope, rate or settings.RATELIMIT_FORMS):
        return Response({'detail': TOO_MANY}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    return None


def form_errors(form):
    """Django form errors in DRF's shape: {"field": ["message", ...]}."""
    return {field: [e['message'] for e in errs] for field, errs in form.errors.get_json_data().items()}


def form_data(request, fields, **defaults):
    """The posted values for `fields`, with `defaults` filling any left blank
    (e.g. a signed-in user's name and email)."""
    data = {f: request.data.get(f, '') for f in fields}
    for key, value in defaults.items():
        if not data.get(key) and value:
            data[key] = value
    return data


def user_defaults(request):
    """Name / email to prefill forms with for a signed-in user."""
    user = request.user
    if not user.is_authenticated:
        return {}
    return {'name': user.get_full_name() or user.username, 'email': user.email}


def viewer_key(request):
    if request.user.is_authenticated:
        return f'u{request.user.pk}'
    return hashlib.sha256(client_ip(request).encode()).hexdigest()[:24]


def first_time(request, key, ttl=86400):
    """True the first time this viewer (user, else IP) does `key` within `ttl`
    seconds — the token-auth stand-in for the web's session flags
    (view counts, "helpful" votes)."""
    return cache.add(f'api-once:{key}:{viewer_key(request)}', 1, ttl)


def flag(params, name):
    return params.get(name) in TRUE_VALUES

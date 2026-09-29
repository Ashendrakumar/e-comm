"""
TechZone Electronics — Production settings.

Activate with:
    DJANGO_SETTINGS_MODULE=techzone.settings.production   (default for wsgi.py / Docker)

Required env vars: SECRET_KEY, ALLOWED_HOSTS, DB_* (PostgreSQL).
Recommended: REDIS_URL, CSRF_TRUSTED_ORIGINS, EMAIL_*, ADMINS, SENTRY_DSN, ADMIN_URL.
"""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa

DEBUG = False

# ── Fail closed: refuse to boot with a missing or placeholder secret ─
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if len(SECRET_KEY) < 40 or SECRET_KEY.startswith(('change-me', 'your-secret-key', 'django-insecure')):
    raise ImproperlyConfigured(
        'SECRET_KEY must be set to a long random value in production. Generate one with:\n'
        '  python -c "import secrets; print(secrets.token_urlsafe(50))"')

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('ALLOWED_HOSTS must list the domain(s) this site is served on.')

# ── PostgreSQL ─────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ.get('DB_NAME', 'techzone'),
        'USER':     os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST':     os.environ.get('DB_HOST', 'localhost'),
        'PORT':     os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}

# ── Cache — Redis if REDIS_URL is set, else local memory ───────────
# Redis is strongly recommended: rate limits and the homepage cache are then
# shared by every gunicorn worker instead of kept per process.
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND':  'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# ── Behind the reverse proxy (Caddy / Nginx) ───────────────────────
TRUSTED_PROXY_COUNT = int(os.environ.get('TRUSTED_PROXY_COUNT', 1))

# ── Security hardening ────────────────────────────────────────────
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 31536000))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'  # nothing frames the site itself
CSP_DIRECTIVES = {**CSP_DIRECTIVES, 'frame-ancestors': ["'none'"], 'upgrade-insecure-requests': []}

# ── SMTP email ─────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# ── Error tracking (optional): set SENTRY_DSN to enable ────────────
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.environ.get('SENTRY_ENVIRONMENT', 'production'),
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', 0.0)),
        send_default_pii=False,
    )

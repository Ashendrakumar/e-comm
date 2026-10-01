"""
TechZone Electronics - Base Settings

Shared by development.py and production.py. Defaults here are the *safe* ones
(DEBUG off, no hosts allowed, no secret key), so a missing env var fails loudly
instead of running a debug site. development.py relaxes them for local work.
"""
import os
import sys
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from a .env file at the project root (if present).
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY', '')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]

# Admin lives at /<ADMIN_URL>/ - change it in production to keep bots off the login page.
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/').strip('/') + '/'

TESTING = 'test' in sys.argv[1:2]

# Application definition
INSTALLED_APPS = [
    # Django core
    # Custom branded admin site with dashboard (Module 11).
    # Replaces 'django.contrib.admin'; @admin.register still targets it.
    'core.admin_site.TechZoneAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    # Third party
    'taggit',
    'rest_framework',
    'rest_framework.authtoken',     # mobile app sign-in tokens
    'corsheaders',                  # lets browser-based clients (Expo web) call /api/

    # Local apps
    'accounts',
    'core',
    'products',
    'pages',
    'blog',
]

MIDDLEWARE = [
    'core.middleware.HealthCheckMiddleware',        # /healthz/ — answered before host checks / SSL redirect
    'corsheaders.middleware.CorsMiddleware',        # before anything that can return a response (CommonMiddleware, WhiteNoise)
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.ContentSecurityPolicyMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'core.middleware.FriendlyDebug404Middleware',   # dev: show templates/404.html instead of Django's debug 404
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'techzone.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'techzone.wsgi.application'

# Database - PostgreSQL via env vars (see .env / .env.example)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='postgres'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
]

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {
    'default':     {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'techzone.storage.StaticStorage'},   # WhiteNoise manifest + dev cache-busting
}
# Tests run with DEBUG=False, where the manifest storage demands a fresh
# `collectstatic`; plain storage keeps the suite independent of that build step.
if TESTING:
    STORAGES['staticfiles'] = {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}

# Product-image import (Admin -> Products -> "Import images from Drive", or
# `manage.py import_product_images`). Point it at a Google Drive for desktop folder,
# e.g. PRODUCT_IMAGES_DIR="G:\My Drive\Product Images" in .env.
PRODUCT_IMAGES_DIR = os.environ.get('PRODUCT_IMAGES_DIR', '')

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Uploaded files (media) on Supabase Storage ─────────────────────
# Every ImageField upload goes through STORAGES['default'], so models, admin,
# importers and the API need no changes: an upload to upload_to='products/' is
# stored as object "products/<file>" in the bucket, the DB keeps that relative
# key, and `.url` returns
#   https://<ref>.supabase.co/storage/v1/object/public/<bucket>/products/<file>
# Enabled when the four vars below are set (bucket must be *public*); otherwise
# files stay on local disk under MEDIA_ROOT. Tests always use local disk.
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')          # https://<ref>.supabase.co
SUPABASE_STORAGE_BUCKET = os.environ.get('SUPABASE_STORAGE_BUCKET', '')
SUPABASE_S3_ACCESS_KEY_ID = os.environ.get('SUPABASE_S3_ACCESS_KEY_ID', '')
SUPABASE_S3_SECRET_ACCESS_KEY = os.environ.get('SUPABASE_S3_SECRET_ACCESS_KEY', '')
USE_SUPABASE_STORAGE = not TESTING and all(
    (SUPABASE_URL, SUPABASE_STORAGE_BUCKET, SUPABASE_S3_ACCESS_KEY_ID, SUPABASE_S3_SECRET_ACCESS_KEY))

if USE_SUPABASE_STORAGE:
    _public_base = f"{SUPABASE_URL.split('://', 1)[-1]}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}"
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'endpoint_url':      f'{SUPABASE_URL}/storage/v1/s3',
            'region_name':       os.environ.get('SUPABASE_S3_REGION', 'ap-northeast-1'),
            'access_key':        SUPABASE_S3_ACCESS_KEY_ID,
            'secret_key':        SUPABASE_S3_SECRET_ACCESS_KEY,
            'bucket_name':       SUPABASE_STORAGE_BUCKET,
            'location':          os.environ.get('SUPABASE_STORAGE_PREFIX', '').strip('/'),  # optional folder inside the bucket
            'custom_domain':     _public_base,      # public, unsigned URLs
            'querystring_auth':  False,
            'default_acl':       None,              # Supabase uses bucket policies, not object ACLs
            'file_overwrite':    False,             # same name twice -> Django appends a suffix
            'addressing_style':  'path',
            'signature_version': 's3v4',
            'object_parameters': {'CacheControl': 'public, max-age=31536000'},  # names are unique; cache hard
        },
    }
    MEDIA_URL = f'https://{_public_base}/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1

# Frontend CSS strategy (Module 12).
#   True  -> compiled /static/css/app.css  (built by `npm run build`)
#   False -> Tailwind via the CDN runtime
#
# The CDN build is a script that generates the stylesheet in the browser *after*
# the document is parsed, so the first paint is unstyled — a visible flash on
# every load, and not something to ship. It therefore auto-enables as soon as a
# compiled bundle exists, and `TAILWIND_COMPILED` is only needed to force it
# either way (e.g. TAILWIND_COMPILED=False to fall back to the CDN).
_compiled_css = BASE_DIR / 'static' / 'css' / 'app.css'
TAILWIND_COMPILED = os.environ.get('TAILWIND_COMPILED', str(_compiled_css.exists())) == 'True'


# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', 10))   # a hung SMTP server must not hang a worker
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@techzone.com')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
# Enquiry notifications are sent from a background thread so the visitor never
# waits on SMTP. Tests send inline so mail.outbox is filled deterministically.
NOTIFY_ASYNC = not TESTING


def _parse_admins(raw):
    """"Jane Doe <jane@x.com>, ops@y.com" -> [('Jane Doe', 'jane@x.com'), ('ops@y.com', 'ops@y.com')]"""
    out = []
    for item in (i.strip() for i in raw.split(',')):
        if not item:
            continue
        if '<' in item and item.endswith('>'):
            name, email = item[:-1].split('<', 1)
            out.append((name.strip() or email.strip(), email.strip()))
        else:
            out.append((item, item))
    return out


# People emailed on server errors (500s).
ADMINS = _parse_admins(os.environ.get('ADMINS', ''))

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session
SESSION_COOKIE_AGE = 86400 * 30  # 30 days

# ── Django REST Framework (public read API) ────────────────────────
REST_FRAMEWORK = {
    # The app sends "Authorization: Token <key>"; sessions keep the browsable API usable.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 24,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle',
                                 'rest_framework.throttling.UserRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'anon': os.environ.get('API_THROTTLE_ANON', '120/min'),
                               'user': os.environ.get('API_THROTTLE_USER', '240/min')},
}
# CORS (django-cors-headers): which *browser* origins may call the API. Native apps don't
# send an Origin and aren't affected. Only /api/ is opened; no cookies are shared
# (the app authenticates with an Authorization: Token header).
CORS_URLS_REGEX = r'^/api/.*$'
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()
]
CORS_ALLOW_CREDENTIALS = False

# Deep link put in password-reset emails from the app, e.g.
# "toyollamobileapp://forgot-password?uid={uid}&token={token}". Empty: the email carries the code only.
API_PASSWORD_RESET_URL = os.environ.get('API_PASSWORD_RESET_URL', '')

# ── Security ───────────────────────────────────────────────────────
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Content-Security-Policy (core.middleware.ContentSecurityPolicyMiddleware).
# The templates use inline <script> blocks and onclick handlers, so scripts need
# 'unsafe-inline'; the policy still pins *where* code, styles and frames load from.
CSP_ENABLED     = os.environ.get('CSP_ENABLED', 'True') == 'True'
CSP_REPORT_ONLY = os.environ.get('CSP_REPORT_ONLY', 'False') == 'True'
CSP_DIRECTIVES = {
    'default-src':     ["'self'"],
    # unsafe-eval: Alpine.js evaluates x-* attribute expressions at runtime
    'script-src':      ["'self'", "'unsafe-inline'", "'unsafe-eval'",
                        'https://www.googletagmanager.com', 'https://www.google-analytics.com'],
    'style-src':       ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
    'font-src':        ["'self'", 'data:', 'https://fonts.gstatic.com'],
    'img-src':         ["'self'", 'data:', 'blob:', 'https:'],
    'connect-src':     ["'self'", 'https://www.google-analytics.com', 'https://*.google-analytics.com',
                        'https://*.analytics.google.com', 'https://www.googletagmanager.com'],
    'frame-src':       ['https://www.google.com', 'https://maps.google.com',
                        'https://www.youtube.com', 'https://www.youtube-nocookie.com'],
    'frame-ancestors': ["'self'"],
    'form-action':     ["'self'"],
    'base-uri':        ["'self'"],
    'object-src':      ["'none'"],
}

# -- Abuse protection for public forms (core.ratelimit) ----------------
# Per client IP and per form: at most N submissions per window ("5/10m").
RATELIMIT_ENABLED = not TESTING
RATELIMIT_FORMS   = os.environ.get('RATELIMIT_FORMS', '10/10m')
RATELIMIT_LOGIN   = os.environ.get('RATELIMIT_LOGIN', '10/15m')
# How many reverse proxies sit in front of Django (Caddy in docker-compose = 1).
# The client IP is then read from X-Forwarded-For; 0 means use REMOTE_ADDR.
TRUSTED_PROXY_COUNT = int(os.environ.get('TRUSTED_PROXY_COUNT', 0))

# CSRF trusted origins (comma-separated env var, e.g. "https://techzone.in,https://www.techzone.in")
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]

# HTTPS hardening (secure cookies, HSTS, SSL redirect) lives in production.py.

# -- Logging: everything to the console (Docker / systemd collect it) --
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'plain': {'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'}},
    'filters': {'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'}},
    'handlers': {
        'console':     {'class': 'logging.StreamHandler', 'formatter': 'plain'},
        'mail_admins': {'class': 'django.utils.log.AdminEmailHandler', 'level': 'ERROR',
                        'filters': ['require_debug_false']},
    },
    'root': {'handlers': ['console'], 'level': os.environ.get('LOG_LEVEL', 'INFO')},
    'loggers': {
        'django.request': {'handlers': ['console', 'mail_admins'], 'level': 'ERROR', 'propagate': False},
    },
}

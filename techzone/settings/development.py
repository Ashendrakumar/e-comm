"""Local development: debug on, any host, console email, insecure fallback key.

This is the default for manage.py. Servers use techzone.settings.production
(the default for wsgi.py / asgi.py and the Docker image).
"""
import os
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['*']
SECRET_KEY = os.environ.get('SECRET_KEY') or 'django-insecure-dev-only-never-use-in-production'

# Expo web runs on its own port (8081 / 19006 / a LAN IP), so let any origin call /api/ locally.
CORS_ALLOW_ALL_ORIGINS = True

# Development: add Django Debug Toolbar if available
try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass

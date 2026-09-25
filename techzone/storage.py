import os

from django.conf import settings
from django.contrib.staticfiles import finders
from whitenoise.storage import CompressedManifestStaticFilesStorage


class StaticStorage(CompressedManifestStaticFilesStorage):
    """WhiteNoise manifest storage, plus cache-busting in development.

    With DEBUG on, {% static %} returns plain unhashed URLs and runserver sends
    no Cache-Control header, so browsers keep serving stale CSS/JS after an
    edit. Appending the source file's mtime (?v=…) gives every edit a new URL.
    Production (DEBUG off) is untouched: the manifest's hashed names do the job.
    """

    def url(self, name, force=False):
        url = super().url(name, force)
        # Only CSS/JS: fonts are also requested from inside stylesheets without the
        # query, so stamping their preload URL would make the browser fetch them twice.
        if settings.DEBUG and not force and name.endswith(('.css', '.js')):
            path = finders.find(name)
            if path and os.path.isfile(path):
                url += ('&' if '?' in url else '?') + f'v={int(os.path.getmtime(path))}'
        return url

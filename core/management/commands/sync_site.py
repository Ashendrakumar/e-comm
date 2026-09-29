"""Point the django.contrib.sites record at the real domain.

The sitemap (and anything else using get_current_site) builds absolute URLs
from this record, which Django creates as "example.com". Run on every deploy
(docker-entrypoint.sh does, when SITE_DOMAIN is set):

    python manage.py sync_site --domain shop.example.in --name "TechZone"
"""
import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Set the Sites framework domain/name (defaults: SITE_DOMAIN / SITE_NAME env vars).'

    def add_arguments(self, parser):
        parser.add_argument('--domain', default=os.environ.get('SITE_DOMAIN', ''))
        parser.add_argument('--name', default=os.environ.get('SITE_NAME', ''))

    def handle(self, *args, domain, name, **opts):
        domain = domain.strip().removeprefix('https://').removeprefix('http://').rstrip('/')
        if not domain:
            raise CommandError('Pass --domain or set SITE_DOMAIN.')
        site, _ = Site.objects.update_or_create(
            pk=settings.SITE_ID, defaults={'domain': domain, 'name': name.strip() or domain})
        self.stdout.write(self.style.SUCCESS(f'Site {site.pk} -> {site.domain} ({site.name})'))

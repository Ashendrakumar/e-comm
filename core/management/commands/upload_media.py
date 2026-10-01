"""Copy local media/ files into the configured media storage (Supabase Storage).

    python manage.py upload_media              # upload what the bucket doesn't have yet
    python manage.py upload_media --dry-run    # just list what would be uploaded

Each file keeps its relative path as the object key ("products/x.webp" ->
"<bucket>/products/x.webp"), which is exactly the value the database already
stores, so existing rows keep working without any data migration.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Upload files from MEDIA_ROOT (or --source) to the default media storage.'

    def add_arguments(self, parser):
        parser.add_argument('--source', default=str(settings.MEDIA_ROOT),
                            help='Local folder to upload (default: MEDIA_ROOT).')
        parser.add_argument('--dry-run', action='store_true', help='List files without uploading.')

    def handle(self, *args, **opts):
        if not getattr(settings, 'USE_SUPABASE_STORAGE', False):
            raise CommandError('Supabase Storage is not configured: set SUPABASE_URL, SUPABASE_STORAGE_BUCKET, '
                               'SUPABASE_S3_ACCESS_KEY_ID and SUPABASE_S3_SECRET_ACCESS_KEY.')
        root = Path(opts['source'])
        if not root.is_dir():
            raise CommandError(f'{root} is not a folder.')

        uploaded = skipped = 0
        for path in sorted(p for p in root.rglob('*') if p.is_file()):
            key = path.relative_to(root).as_posix()
            if default_storage.exists(key):
                skipped += 1
                continue
            if opts['dry_run']:
                self.stdout.write(f'would upload {key}')
            else:
                with path.open('rb') as fh:
                    saved = default_storage.save(key, File(fh))
                if saved != key:  # storage renamed it; the DB would point at the wrong object
                    raise CommandError(f'{key} was stored as {saved}; aborting.')
                self.stdout.write(f'uploaded {key}')
            uploaded += 1

        verb = 'to upload' if opts['dry_run'] else 'uploaded'
        self.stdout.write(self.style.SUCCESS(f'{uploaded} {verb}, {skipped} already in the bucket.'))

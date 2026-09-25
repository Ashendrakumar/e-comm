"""Bulk-attach product photos from a folder (e.g. Google Drive for desktop) or a ZIP.

    python manage.py import_product_images                     # preview PRODUCT_IMAGES_DIR
    python manage.py import_product_images --apply             # import it
    python manage.py import_product_images --create-folders    # make a folder per product
    python manage.py import_product_images "D:\\photos.zip" --apply --mode replace

The folder defaults to settings.PRODUCT_IMAGES_DIR (env var of the same name).
Layout, matching and ordering rules: see products/image_import.py.
The same import is available in the admin: Products -> "Import images from Drive".
"""
import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from products.image_import import ImageImporter, create_folders


class Command(BaseCommand):
    help = 'Attach product images from a folder tree (Drive for desktop, Dropbox...) or a ZIP file.'

    def add_arguments(self, parser):
        parser.add_argument('source', nargs='?', help='Folder or .zip (default: settings.PRODUCT_IMAGES_DIR)')
        parser.add_argument('--apply', action='store_true', help='Actually save (default is a dry-run preview)')
        parser.add_argument('--mode', choices=['skip', 'append', 'replace'], default='skip',
                            help='skip: only products without images (default) | append | replace')
        parser.add_argument('--create-folders', action='store_true',
                            help='Create <Category>/<SKU> - <Name>/ folders for products that have no images')
        parser.add_argument('--all-products', action='store_true',
                            help='With --create-folders: include products that already have images')
        parser.add_argument('--max-px', type=int, default=1600, help='Longest side after resizing (default 1600)')
        parser.add_argument('--format', choices=['jpeg', 'webp'], default='webp', help='Output format when resizing')
        parser.add_argument('--no-resize', action='store_true', help='Keep original files as they are')
        parser.add_argument('--report', help='Write a CSV report of every folder/file and what happened')

    def handle(self, *args, **opts):
        source = opts['source'] or getattr(settings, 'PRODUCT_IMAGES_DIR', '')
        if not source:
            raise CommandError('Give a folder, or set PRODUCT_IMAGES_DIR (e.g. "G:\\My Drive\\Product Images").')
        source = Path(source)

        if opts['create_folders']:
            created, existing = create_folders(source, only_missing=not opts['all_products'])
            self.stdout.write(self.style.SUCCESS(
                f'Folders ready in {source}: {created} created, {existing} already there. '
                f"Drop each product's photos into its folder, then run with --apply."))
            return

        if not source.exists():
            raise CommandError(f'Not found: {source}. Is Google Drive for desktop running and signed in?')

        importer = ImageImporter(mode=opts['mode'], max_px=opts['max_px'], fmt=opts['format'],
                                 resize=not opts['no_resize'])
        res = importer.run(source, apply=opts['apply'])

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'{"APPLY" if opts["apply"] else "DRY RUN"} | mode={opts["mode"]} | {source}'))
        marks = {'done': '+', 'ready': '+', 'skipped': '-', 'unmatched': '?', 'error': '!'}
        for r in res.rows:
            line = f'  {marks[r["status"]]} {(r["product"] or r["key"])[:44]:<44} {r["detail"]}'
            style = {'unmatched': self.style.WARNING, 'error': self.style.ERROR}.get(r['status'])
            self.stdout.write(style(line) if style else line)

        if opts.get('report'):
            with open(opts['report'], 'w', newline='', encoding='utf-8') as fh:
                w = csv.DictWriter(fh, fieldnames=['key', 'product', 'found', 'status', 'detail'],
                                   extrasaction='ignore')
                w.writeheader()
                w.writerows(res.rows)
            self.stdout.write(f'Report written to {opts["report"]}')

        verb = 'Imported' if opts['apply'] else 'Would import'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} {res.added} image(s) for {res.products} product(s) | '
            f'{res.skipped} skipped | {res.unmatched} unmatched | {res.errors} error(s).'))
        if not opts['apply']:
            self.stdout.write('Nothing was saved. Re-run with --apply to import.')

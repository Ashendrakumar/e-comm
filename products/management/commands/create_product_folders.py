"""Create the whole photo folder tree for the catalogue, ready to drop photos into:

    <root>/<Category>/<SKU> - <Product name>/

    python manage.py create_product_folders                     # in PRODUCT_IMAGES_DIR
    python manage.py create_product_folders "G:\\My Drive\\Product Images"
    python manage.py create_product_folders --dry-run           # list what would be made
    python manage.py create_product_folders --only-missing      # skip products that have photos

A product that already has a folder (by SKU, slug or name, anywhere in the tree) is left
alone, so it's safe to re-run after adding products. Nothing is renamed or deleted.
Then fill the folders and run `import_product_images --apply`.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from products.image_import import FolderError, create_folders


class Command(BaseCommand):
    help = 'Create <Category>/<SKU> - <Name>/ photo folders for every active product (existing ones are kept).'

    def add_arguments(self, parser):
        parser.add_argument('root', nargs='?', help='Folder to build in (default: settings.PRODUCT_IMAGES_DIR)')
        parser.add_argument('--only-missing', action='store_true', help='Skip products that already have images')
        parser.add_argument('--dry-run', action='store_true', help='Only list the folders that would be created')

    def handle(self, *args, **opts):
        root = opts['root'] or getattr(settings, 'PRODUCT_IMAGES_DIR', '')
        if not root:
            raise CommandError('Give a folder, or set PRODUCT_IMAGES_DIR (e.g. "G:\\My Drive\\Product Images").')
        root = Path(root)
        try:
            created, existing = create_folders(root, only_missing=opts['only_missing'], dry_run=opts['dry_run'])
        except FolderError as exc:
            raise CommandError(str(exc))

        for folder in created:
            self.stdout.write(f'  + {folder.relative_to(root)}')
        verb = 'Would create' if opts['dry_run'] else 'Created'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} {len(created)} folder(s) in {root}; {existing} product(s) already had one.'))
        if created and not opts['dry_run']:
            self.stdout.write("Drop each product's photos into its folder, then run: "
                              'python manage.py import_product_images --apply')

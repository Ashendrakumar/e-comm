"""Bulk-attach product photos from a folder (e.g. a synced Google Drive folder) or a ZIP.

    python manage.py import_product_images "G:\\My Drive\\Product Images"            # preview
    python manage.py import_product_images "G:\\My Drive\\Product Images" --apply    # save
    python manage.py import_product_images images.zip --apply --mode replace

Folder structure (category folders are optional and ignored — nest however you like):

    Product Images/
      Mobiles/
        TZ-32E6AADD/            <- folder named by SKU, slug or product name
          main.jpg              <- "main" / "cover" / "primary" becomes the primary image
          2.jpg
          3.jpg
        samsung-galaxy-a55-5g/
          front.png
      TZ-55F23A1E-1.jpg          <- loose files work too: <key>-<n>.<ext> or <key>_<n>.<ext>
      TZ-55F23A1E-2.jpg

Matching (case-insensitive): SKU, then slug, then the product name (slugified).
Order: natural sort (2.jpg before 10.jpg); the primary is a main/cover/primary file,
otherwise the first file.

Modes:
    skip     (default) only products that have no images yet
    append   add the new images after the existing ones
    replace  delete the product's existing images first

Large photos are resized so the longest side is --max-px (default 1600) and saved as
optimised JPEG/WebP; --no-resize keeps the originals (they must be under the 5 MB limit).
A report of unmatched folders/files is printed at the end, and can be written with --report.
"""
import csv
import io
import os
import re
import tempfile
import zipfile
from collections import OrderedDict
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from core.validators import ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE_MB
from products.models import Product, ProductImage

IMAGE_EXTS = ALLOWED_IMAGE_EXTENSIONS - {'.svg', '.gif'}      # real photos only
PRIMARY_WORDS = {'main', 'cover', 'primary', 'hero', 'front'}
SUFFIX_RE = re.compile(r'^(?P<key>.+?)[\s_-]+(?P<n>\d+|main|cover|primary|hero|front)$', re.I)


def natural_key(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', name)]


def is_primary_name(stem):
    return stem.lower() in PRIMARY_WORDS or any(stem.lower().endswith(f'-{w}') or stem.lower().endswith(f'_{w}')
                                                for w in PRIMARY_WORDS)


class Command(BaseCommand):
    help = 'Attach product images from a folder tree (Drive/Dropbox sync folder) or a ZIP file.'

    def add_arguments(self, parser):
        parser.add_argument('source', help='Folder path or .zip file')
        parser.add_argument('--apply', action='store_true', help='Actually save (default is a dry-run preview)')
        parser.add_argument('--mode', choices=['skip', 'append', 'replace'], default='skip')
        parser.add_argument('--max-px', type=int, default=1600, help='Longest side after resizing (default 1600)')
        parser.add_argument('--format', choices=['jpeg', 'webp'], default='webp', help='Output format when resizing')
        parser.add_argument('--no-resize', action='store_true', help='Keep original files as they are')
        parser.add_argument('--report', help='Write a CSV report of every folder/file and what happened')

    # ── entry point ─────────────────────────────────────────────────────
    def handle(self, *args, **opts):
        src = Path(opts['source'])
        if not src.exists():
            raise CommandError(f'Not found: {src}')
        tmp = None
        if src.is_file() and src.suffix.lower() == '.zip':
            tmp = tempfile.TemporaryDirectory()
            with zipfile.ZipFile(src) as zf:
                zf.extractall(tmp.name)
            root = Path(tmp.name)
        elif src.is_dir():
            root = src
        else:
            raise CommandError('Source must be a folder or a .zip file.')

        try:
            self.product_lookup()              # needed first: loose files are grouped by product key
            groups = self.collect(root)
            self.run(groups, opts)
        finally:
            if tmp:
                tmp.cleanup()

    # ── discovery ───────────────────────────────────────────────────────
    def collect(self, root):
        """Return {key: [paths]} — one key per product folder or loose-file prefix."""
        groups = OrderedDict()
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort(key=natural_key)
            imgs = sorted((f for f in filenames if Path(f).suffix.lower() in IMAGE_EXTS and not f.startswith('.')),
                          key=natural_key)
            if not imgs:
                continue
            here = Path(dirpath)
            for f in imgs:
                stem = Path(f).stem
                m = SUFFIX_RE.match(stem)
                # 1. the whole file name is a product ("iphone-15.jpg" — don't split off "15")
                # 2. <product>-<n> / <product>_main
                # 3. otherwise the file belongs to the folder it's in (folder = product)
                if self.looks_like_key(stem):
                    key = stem
                elif m and self.looks_like_key(m.group('key')):
                    key = m.group('key')
                elif here != root:
                    key = here.name
                else:
                    key = m.group('key') if m else stem
                groups.setdefault(key, []).append(here / f)
        return groups

    _lookup_cache = None

    def looks_like_key(self, key):
        return self.match(key) is not None

    def product_lookup(self):
        lookup = {}
        for p in Product.objects.all().only('id', 'sku', 'slug', 'name'):
            for k in (p.sku, p.slug, slugify(p.name)):
                if k:
                    lookup.setdefault(k.lower(), p)
        self._lookup_cache = lookup
        return lookup

    def match(self, key):
        lookup = self._lookup_cache or {}
        return lookup.get(key.strip().lower()) or lookup.get(slugify(key))

    # ── import ──────────────────────────────────────────────────────────
    def run(self, groups, opts):
        apply, mode = opts['apply'], opts['mode']
        rows, added, touched = [], 0, 0
        unmatched = []
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'{"APPLY" if apply else "DRY RUN"} | mode={mode} | {len(groups)} image group(s) found'))

        for key, paths in groups.items():
            product = self.match(key)
            if not product:
                unmatched.append(key)
                rows.append([key, '', len(paths), 'unmatched: rename the folder to the product SKU, slug or name'])
                continue
            existing = product.images.count()
            if mode == 'skip' and existing:
                rows.append([key, product.name, len(paths), f'skipped: already has {existing} image(s)'])
                continue

            ordered = sorted(paths, key=lambda p: (not is_primary_name(p.stem), natural_key(p.name)))
            if apply:
                with transaction.atomic():
                    if mode == 'replace' and existing:
                        for img in product.images.all():
                            img.image.delete(save=False)
                            img.delete()
                        existing = 0
                    start = product.images.count()
                    has_primary = product.images.filter(is_primary=True).exists()
                    for i, path in enumerate(ordered):
                        name, data = self.prepare(path, product, i, opts)
                        img = ProductImage(product=product, alt_text=product.name, order=start + i,
                                           is_primary=(not has_primary and i == 0))
                        img.image.save(name, ContentFile(data), save=True)
                        added += 1
            else:
                added += len(ordered)
            touched += 1
            action = {'skip': 'add', 'append': 'append', 'replace': 'replace with'}[mode]
            rows.append([key, product.name, len(paths),
                         f'{"done" if apply else "would"} {action} {len(ordered)} image(s); primary = {ordered[0].name}'])
            self.stdout.write(f'  + {product.name:<42} <- {len(ordered)} image(s)  [{key}]')

        for key in unmatched:
            self.stdout.write(self.style.WARNING(f'  ? no product matches "{key}"'))

        if opts.get('report'):
            with open(opts['report'], 'w', newline='', encoding='utf-8') as fh:
                w = csv.writer(fh)
                w.writerow(['folder_or_file_key', 'product', 'images_found', 'result'])
                w.writerows(rows)
            self.stdout.write(f'Report written to {opts["report"]}')

        verb = 'Imported' if apply else 'Would import'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} {added} image(s) for {touched} product(s); {len(unmatched)} unmatched.'))
        if not apply:
            self.stdout.write('Nothing was saved. Re-run with --apply to import.')

    # ── image processing ────────────────────────────────────────────────
    def prepare(self, path, product, index, opts):
        raw = path.read_bytes()
        base = f'{slugify(product.slug or product.name)[:60]}-{index + 1}'
        if opts['no_resize']:
            if len(raw) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise CommandError(f'{path} is over {MAX_IMAGE_SIZE_MB} MB — drop --no-resize to shrink it.')
            return base + path.suffix.lower(), raw
        from PIL import Image, ImageOps
        with Image.open(io.BytesIO(raw)) as im:
            im = ImageOps.exif_transpose(im)                 # respect phone-camera rotation
            im.thumbnail((opts['max_px'], opts['max_px']))
            out = io.BytesIO()
            if opts['format'] == 'webp':
                im.save(out, 'WEBP', quality=82, method=6)
                ext = '.webp'
            else:
                if im.mode in ('RGBA', 'LA', 'P'):
                    bg = Image.new('RGB', im.size, (255, 255, 255))
                    bg.paste(im.convert('RGBA'), mask=im.convert('RGBA').split()[-1])
                    im = bg
                im.convert('RGB').save(out, 'JPEG', quality=85, optimize=True, progressive=True)
                ext = '.jpg'
        return base + ext, out.getvalue()

"""Bulk product-image import from a folder tree (a Google Drive for desktop folder,
Dropbox, a USB drive…) or a ZIP. Used by both

    python manage.py import_product_images [folder] [--apply] …
    Admin -> Products -> "Import images from Drive"

Folder layout (category folders are optional and ignored):

    <root>/
      Mobiles/
        TZ-32E6AADD - Canon EOS R50/     <- "<SKU> - <name>" (what create_folders() makes),
          main.jpg                          or just the SKU, the slug, or the product name
          2.jpg
      TZ-55F23A1E-1.jpg                  <- loose files: <key>-<n>.<ext>

Matching is case-insensitive: SKU, then slug, then slugified name; for "<SKU> - <name>"
the part before " - " is enough. Order is natural (2 before 10); a file called
main / cover / primary / hero / front becomes the primary image, else the first file.
"""
import io
import os
import re
import shutil
import tempfile
import zipfile
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify

from core.validators import ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE_MB
from .models import Product, ProductImage

IMAGE_EXTS = ALLOWED_IMAGE_EXTENSIONS - {'.svg', '.gif'}      # real photos only
PRIMARY_WORDS = {'main', 'cover', 'primary', 'hero', 'front'}
SUFFIX_RE = re.compile(r'^(?P<key>.+?)[\s_-]+(?P<n>\d+|main|cover|primary|hero|front)$', re.I)
UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')                 # not allowed in Windows/Drive names


def natural_key(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', name)]


def is_primary_name(stem):
    s = stem.lower()
    return s in PRIMARY_WORDS or any(s.endswith(f'-{w}') or s.endswith(f'_{w}') for w in PRIMARY_WORDS)


def safe_name(text):
    return UNSAFE.sub('-', text).strip(' .')[:120] or 'untitled'


@dataclass
class ImportResult:
    rows: list = field(default_factory=list)      # dicts: key, product, found, status, detail
    added: int = 0
    products: int = 0
    unmatched: int = 0
    skipped: int = 0
    errors: int = 0


class ImageImporter:
    def __init__(self, mode='skip', max_px=1600, fmt='webp', resize=True):
        assert mode in ('skip', 'append', 'replace')
        self.mode, self.max_px, self.fmt, self.resize = mode, max_px, fmt, resize
        self.lookup = {}
        for p in Product.objects.all().only('id', 'sku', 'slug', 'name'):
            for k in (p.sku, p.slug, slugify(p.name)):
                if k:
                    self.lookup.setdefault(k.lower(), p)

    # ── matching ──
    def match(self, key):
        key = key.strip()
        hit = self.lookup.get(key.lower()) or self.lookup.get(slugify(key))
        if not hit and ' - ' in key:                         # "<SKU> - <name>": SKU first, then the name
            head, tail = key.split(' - ', 1)
            hit = (self.lookup.get(head.strip().lower()) or self.lookup.get(slugify(head))
                   or self.lookup.get(tail.strip().lower()) or self.lookup.get(slugify(tail)))
        return hit

    # ── discovery ──
    def collect(self, root):
        root = Path(root)
        groups = OrderedDict()
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted((d for d in dirnames if not d.startswith('.')), key=natural_key)
            imgs = sorted((f for f in filenames
                           if Path(f).suffix.lower() in IMAGE_EXTS and not f.startswith(('.', '~'))),
                          key=natural_key)
            here = Path(dirpath)
            for f in imgs:
                stem = Path(f).stem
                m = SUFFIX_RE.match(stem)
                if self.match(stem):                          # "iphone-15.jpg" is a product, not image 15
                    key = stem
                elif m and self.match(m.group('key')):         # "<product>-2.jpg"
                    key = m.group('key')
                elif here != root:                             # file inside a product folder
                    key = here.name
                else:
                    key = m.group('key') if m else stem
                groups.setdefault(key, []).append(here / f)
        return groups

    # ── run ──
    def run(self, source, apply=False):
        source = Path(source)
        tmp = None
        if source.is_file() and source.suffix.lower() == '.zip':
            tmp = tempfile.mkdtemp()
            with zipfile.ZipFile(source) as zf:
                zf.extractall(tmp)
            source = Path(tmp)
        try:
            return self._run(self.collect(source), apply)
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)

    def _run(self, groups, apply):
        res = ImportResult()
        for key, paths in groups.items():
            product = self.match(key)
            row = {'key': key, 'product': product.name if product else '', 'found': len(paths),
                   'product_id': product.pk if product else None}
            if not product:
                res.unmatched += 1
                res.rows.append({**row, 'status': 'unmatched',
                                 'detail': 'No product has this SKU, slug or name — rename the folder.'})
                continue
            existing = product.images.count()
            if self.mode == 'skip' and existing:
                res.skipped += 1
                res.rows.append({**row, 'status': 'skipped', 'detail': f'Already has {existing} image(s).'})
                continue
            ordered = sorted(paths, key=lambda p: (not is_primary_name(p.stem), natural_key(p.name)))
            try:
                if apply:
                    self._save(product, ordered)
                res.added += len(ordered)
                res.products += 1
                verb = {'skip': 'Add', 'append': 'Append', 'replace': 'Replace with'}[self.mode]
                res.rows.append({**row, 'status': 'done' if apply else 'ready',
                                 'detail': f'{verb} {len(ordered)} image(s); primary: {ordered[0].name}'})
            except Exception as exc:                          # one bad photo never stops the batch
                res.errors += 1
                res.rows.append({**row, 'status': 'error', 'detail': str(exc)[:200]})
        return res

    def _save(self, product, ordered):
        with transaction.atomic():
            if self.mode == 'replace':
                for img in product.images.all():
                    img.image.delete(save=False)
                    img.delete()
            start = product.images.count()
            has_primary = product.images.filter(is_primary=True).exists()
            for i, path in enumerate(ordered):
                name, data = self.prepare(path, product, start + i)
                img = ProductImage(product=product, alt_text=product.name, order=start + i,
                                   is_primary=(not has_primary and i == 0))
                img.image.save(name, ContentFile(data), save=True)

    def prepare(self, path, product, index):
        raw = Path(path).read_bytes()
        base = f'{slugify(product.slug or product.name)[:60]}-{index + 1}'
        if not self.resize:
            if len(raw) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise ValueError(f'{Path(path).name} is over {MAX_IMAGE_SIZE_MB} MB; turn resizing on to shrink it.')
            return base + Path(path).suffix.lower(), raw
        from PIL import Image, ImageOps
        with Image.open(io.BytesIO(raw)) as im:
            im = ImageOps.exif_transpose(im)                  # respect phone-camera rotation
            im.thumbnail((self.max_px, self.max_px))
            out = io.BytesIO()
            if self.fmt == 'webp':
                im.save(out, 'WEBP', quality=82, method=6)
                return base + '.webp', out.getvalue()
            if im.mode in ('RGBA', 'LA', 'P'):
                rgba = im.convert('RGBA')
                bg = Image.new('RGB', im.size, (255, 255, 255))
                bg.paste(rgba, mask=rgba.split()[-1])
                im = bg
            im.convert('RGB').save(out, 'JPEG', quality=85, optimize=True, progressive=True)
            return base + '.jpg', out.getvalue()


def create_folders(root, only_missing=True):
    """Make <root>/<Category>/<SKU> - <Product name>/ for every active product.

    Never renames or deletes anything. With only_missing, products that already
    have images are left out. Returns (created, existing) counts.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    created = existing = 0
    qs = Product.objects.filter(is_active=True).select_related('category').order_by('category__name', 'name')
    if only_missing:
        qs = qs.filter(images__isnull=True)
    for p in qs:
        folder = root / safe_name(p.category.name if p.category_id else 'Uncategorised') / safe_name(f'{p.sku} - {p.name}')
        if folder.exists():
            existing += 1
        else:
            folder.mkdir(parents=True)
            created += 1
    return created, existing

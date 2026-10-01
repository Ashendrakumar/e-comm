# TechZone — Deploying to Render with Supabase

The app runs on **Render** (Docker web service + Key Value/Redis). The **database** is
**Supabase PostgreSQL** and all **uploaded files** (product photos, banners, logos, blog
images…) live in **Supabase Storage**. Static CSS/JS is still served by WhiteNoise from the
container.

---

## Architecture

| Piece | Where | Notes |
|-------|-------|-------|
| Django 5.2 + DRF, Gunicorn | Render web service (Docker) | `Dockerfile`, `docker-entrypoint.sh` |
| PostgreSQL | **Supabase** | same `DB_*` settings as your `.env` |
| Uploaded media | **Supabase Storage** (public bucket `media`) | S3-compatible API via `django-storages` |
| Static files (CSS/JS/fonts) | WhiteNoise, inside the container | built during `docker build` |
| Cache / sessions / rate limits | Render Key Value (Redis) | optional but recommended |

```
Browser / mobile app
   │  pages, API              │  <img src="https://<ref>.supabase.co/storage/v1/object/public/media/...">
   ▼                          ▼
Render: Django ──SQL──► Supabase Postgres
      │ uploads (S3 API) ───► Supabase Storage bucket "media"
      └─cache──► Render Key Value
```

Because files are no longer on the container's disk, **no Render persistent disk is needed**
and redeploys never lose images.

---

## Part 1 — Supabase

### 1.1 Database

The database setup is unchanged — use the same `DB_*` values that already work in your
`.env` (Supabase pooler host, `postgres.<ref>` user, port, password).

### 1.2 Storage bucket

1. Supabase → **Storage** → **New bucket**
   - **Name:** `media`
   - **Public bucket:** **ON** (images are shown on public pages, so they must be readable without a token)
   - *Restrict file upload size:* `5 MB` (matches the app's own validator)
   - *Allowed MIME types:* `image/*`
2. Supabase → **Project Settings → Storage → S3 Connection / S3 Access Keys**
   - Note the **Region** shown there (e.g. `ap-northeast-1`).
   - Click **New access key** → copy the **Access key ID** and **Secret access key**
     (the secret is only shown once).
3. Your **Project URL** is under **Project Settings → Data API** (`https://<ref>.supabase.co`).

The S3 access key has full access to the project's storage — keep it only in Render's
environment, never in the repo or in the mobile app.

---

## Part 2 — Render

### Option A: Blueprint (recommended)

`render.yaml` in the repo root defines the web service and the Key Value instance.

1. Push the code to GitHub.
2. Render → **New → Blueprint** → pick the repo.
3. Render asks for every value marked `sync: false` — fill them in from the table below.
   `SECRET_KEY` is generated for you and `REDIS_URL` is wired automatically.

### Option B: Manual

1. **New → Key Value** → name `techzone-redis`, plan Free → copy the **Internal URL**.
2. **New → Web Service** → your repo → **Language: Docker**, branch `main`.
3. **Health Check Path:** `/healthz/`
4. Add the environment variables below.

### Environment variables

| Key | Value / example | Required |
|-----|-----------------|----------|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(50))"` | ✅ |
| `DEBUG` | `False` | ✅ |
| `ALLOWED_HOSTS` | `techzone.onrender.com` | ✅ |
| `CSRF_TRUSTED_ORIGINS` | `https://techzone.onrender.com` | ✅ |
| `SITE_DOMAIN` | `techzone.onrender.com` | ✅ |
| `PORT` | `8000` | ✅ (Gunicorn binds 8000) |
| `TRUSTED_PROXY_COUNT` | `1` | ✅ |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | same as your working `.env` | ✅ |
| `SUPABASE_URL` | `https://<ref>.supabase.co` | ✅ |
| `SUPABASE_STORAGE_BUCKET` | `media` | ✅ |
| `SUPABASE_S3_ACCESS_KEY_ID` | from 1.2 | ✅ |
| `SUPABASE_S3_SECRET_ACCESS_KEY` | from 1.2 | ✅ |
| `SUPABASE_S3_REGION` | `ap-northeast-1` (from 1.2) | ✅ |
| `SUPABASE_STORAGE_PREFIX` | e.g. `prod` — folder inside the bucket, to share one bucket between environments | optional |
| `REDIS_URL` | Key Value internal URL | recommended |
| `CORS_ALLOWED_ORIGINS` | Expo web origin(s), comma-separated | optional |
| `ADMIN_URL` | e.g. `manage-7f3k/` | optional |
| `SENTRY_DSN` | Sentry DSN | optional |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | SMTP | optional |
| `ADMINS` | `Ops <ops@example.com>` | optional |

Media storage switches to Supabase **only when all four** `SUPABASE_URL`,
`SUPABASE_STORAGE_BUCKET`, `SUPABASE_S3_ACCESS_KEY_ID` and `SUPABASE_S3_SECRET_ACCESS_KEY` are
set. If any is missing, uploads go to the container disk and **disappear on the next deploy**.

### What happens on each deploy

`docker-entrypoint.sh` runs, in order:

1. `python manage.py migrate --noinput` (against Supabase)
2. `python manage.py sync_site` (when `SITE_DOMAIN` is set)
3. `python manage.py check --deploy --fail-level WARNING`
4. Gunicorn

### First deploy — one-time steps (Render → web service → **Shell**)

```bash
python manage.py createsuperuser
python manage.py setup_roles      # staff groups/permissions
python manage.py seed_data        # optional demo content
```

---

## Part 3 — Moving existing data and images

### Database

From your machine, with the **old** database in `.env`:

```bash
python manage.py dumpdata --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission --exclude sessions --exclude admin.logentry \
  --indent 2 -o data.json
```

Then point the `DB_*` vars in `.env` at Supabase and:

```bash
python manage.py migrate
python manage.py loaddata data.json
```

(Or use `pg_dump` / `psql` directly.)

### Images already in `media/`

The database stores each file as a **relative key** (e.g. `products/r50.webp`). Upload the
local files under the same keys and every existing row works unchanged:

```bash
# .env must contain the four SUPABASE_* storage vars
python manage.py upload_media --dry-run     # list what would be uploaded
python manage.py upload_media               # upload; skips files already in the bucket
python manage.py upload_media --source D:\backup\media   # from another folder
```

---

## Part 4 — How file paths work (upload & get)

### Where each upload goes

Every `ImageField` has an `upload_to` folder. That folder becomes the object path inside the
bucket; the database column stores only the relative key.

| Model.field | `upload_to` | Object in bucket `media` |
|-------------|-------------|--------------------------|
| `products.ProductImage.image` | `products/` | `media/products/<file>` |
| `products.ProductVariant.image` | `variants/` | `media/variants/<file>` |
| `products.ReviewImage.image` | `reviews/` | `media/reviews/<file>` |
| `products.Category.image` | `categories/icons/` | `media/categories/icons/<file>` |
| `products.Category.banner` | `categories/banners/` | `media/categories/banners/<file>` |
| `products.Category.banner_mobile` | `categories/banners/mobile/` | `media/categories/banners/mobile/<file>` |
| `core.Brand.logo` | `brands/` | `media/brands/<file>` |
| `core.Banner.image` | `banners/` | `media/banners/<file>` |
| `core.Banner.mobile_image` | `banners/mobile/` | `media/banners/mobile/<file>` |
| `core.Testimonial.avatar` | `testimonials/` | `media/testimonials/<file>` |
| `core.SiteSettings.logo` / `.favicon` | `site/` | `media/site/<file>` |
| `pages.Service.image` | `services/` | `media/services/<file>` |
| `pages.Service.banner` | `services/banners/` | `media/services/banners/<file>` |
| `blog.BlogPost.featured_image` | `blog/` | `media/blog/<file>` |

With `SUPABASE_STORAGE_PREFIX=prod` every key gets that folder in front
(`media/prod/products/<file>`).

The public URL of any object is:

```
https://<ref>.supabase.co/storage/v1/object/public/<bucket>/<key>
e.g. https://<ref>.supabase.co/storage/v1/object/public/media/products/r50.webp
```

If a file with the same name already exists, Django appends a random suffix
(`r50_aB3xYz1.webp`) rather than overwriting it, so URLs never change underneath a cached page.

### Uploading — in code

All existing upload paths (Django admin forms, spreadsheet image import, "Import images from
Drive", `import_product_images`, review photos) already use the storage API, so they upload to
Supabase with no code changes. For new code, do the same:

```python
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Through a model field — the key is built from upload_to
img = ProductImage(product=product)
img.image.save('r50.webp', ContentFile(data), save=True)   # -> products/r50.webp

# Straight to the bucket, any path
key = default_storage.save('exports/report.csv', ContentFile(b'...'))

# Delete
img.image.delete(save=False)        # removes the object from the bucket
default_storage.delete(key)
```

Never use `.path` or `open(settings.MEDIA_ROOT / ...)` — remote storage has no local path.
Read a file's bytes with `img.image.open('rb')` or `default_storage.open(key)`.

### Getting the URL

| Where | How | Result |
|-------|-----|--------|
| Templates | `{{ img.image.url }}` | full Supabase URL |
| Templates — meta tags / JSON-LD that need an absolute URL | `{% load ui %}{{ img.image.url\|absolute_url:request }}` | works for both local `/media/…` and Supabase URLs |
| Python | `img.image.url` / `default_storage.url(key)` | full Supabase URL |
| REST API / mobile app | serializers use `request.build_absolute_uri(file.url)` | full Supabase URL — the app loads images directly from Supabase |

Don't write `{{ request.scheme }}://{{ request.get_host }}{{ x.url }}` — once `.url` is
absolute that produces a broken `https://site.comhttps://…` link. Use the `absolute_url` filter.

### Local development

- No `SUPABASE_*` vars in `.env` → files are saved to `./media/` and served at `/media/` by
  `runserver`.
- With the vars set, local uploads go to the same bucket. Use a separate bucket or
  `SUPABASE_STORAGE_PREFIX=dev` so test uploads don't mix with production.
- `manage.py test` always uses local disk, never the bucket.

---

## Verify after deploying

| Check | Expected |
|-------|----------|
| `https://<app>.onrender.com/healthz/` | `{"status": "ok"}` |
| `/admin/` → upload a product image | Saves without error |
| Right-click that image → *Open in new tab* | URL starts with `https://<ref>.supabase.co/storage/v1/object/public/media/` |
| Supabase → Storage → `media` | The file appears under `products/` |
| `/api/v1/products/` | `primary_image` values are Supabase URLs |
| Redeploy, reload the page | Image still there |

---

## Troubleshooting

**Upload fails with `AccessDenied` / `SignatureDoesNotMatch`**
Wrong S3 key pair or `SUPABASE_S3_REGION`. Regenerate the key in Supabase and copy the region
from the S3 Connection panel.

**Upload works but the image shows 400/404**
The bucket isn't **public**, or `SUPABASE_STORAGE_BUCKET` doesn't match the bucket name.

**Images still go to `/media/…` and vanish after redeploy**
One of the four `SUPABASE_*` storage vars is missing. Check in the Render Shell:
`python manage.py shell -c "from django.conf import settings; print(settings.USE_SUPABASE_STORAGE)"`
— it must print `True`.

**Upload rejected with `Payload too large`**
The bucket's size limit is lower than the file. The app allows up to 5 MB per image.

**Free tier notes**
Render free web services sleep after 15 minutes (first request then takes ~30 s). Supabase
free projects pause after a week without activity — unpause them from the dashboard.

---

## Custom domain

1. Web service → **Settings → Custom Domains** → add `shop.example.com` and create the DNS
   records Render shows.
2. Update `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` (`https://shop.example.com`) and
   `SITE_DOMAIN`.
3. Image URLs keep pointing at Supabase; nothing to change there.

## Rollback

Web service → **Events** → pick a previous successful deploy → **Rollback**. Migrations are not
reversed automatically; a rollback across a schema change needs a manual `migrate <app> <n>`.

## Cost (monthly, approximate)

| Service | Free | Paid |
|---------|------|------|
| Render web service | $0 (sleeps) | Starter $7 |
| Render Key Value | $0 | Starter $10 |
| Supabase (DB 500 MB + Storage 1 GB) | $0 (pauses when idle) | Pro $25 (8 GB DB, 100 GB storage) |

# TechZone — Premium Electronics Web Application

## ✅ Module 1 — Landing Page
## ✅ Module 2 — Product Categories
## ✅ Module 3 — Product Listing Page
## ✅ Module 4 — Product Details Page
## ✅ Module 5 — Related Products Algorithm
## ✅ Module 6 — CMS Management
## ✅ Module 7 — Services Section
## ✅ Module 8 — Serving Areas Section
## ✅ Module 9 — Contact Section
## ✅ Module 10 — Additional Features (SEO / Performance / Security)
## ✅ Module 11 — Admin Dashboard (branding, dashboard widget, bulk actions, CSV export, roles)
## ✅ Module 12 — UI/UX (dark mode, Tailwind build pipeline, accessibility)
## ✅ Module 13 — Database Models (indexed, validated)
## ✅ Module 14 — Deliverables (REST API, Docker, env config)
## ✅ Module 15 — Final QA (tests, deploy check)

---

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1    # PowerShell (use `source .venv/bin/activate` on macOS/Linux)
pip install -r requirements.txt
cp .env.example .env          # optional locally — manage.py defaults to development settings
python manage.py migrate
python manage.py seed_data
python manage.py setup_roles  # optional: create staff permission groups
npm install && npm run build  # frontend CSS -> static/css/app.css (see Static assets)
python manage.py runserver
```

**Site:** http://localhost:8000  
**Admin:** http://localhost:8000/admin/ → `admin / admin123` (created by `seed_data`, development only)  
**REST API:** http://localhost:8000/api/v1/

---

## REST API (Module 14)

JSON API for the customer mobile app under `/api/v1/` (DRF; token auth; paginated 24/page;
120 req/min anonymous, 240 req/min signed in). **Full reference: [docs/MOBILE_API.md](docs/MOBILE_API.md).**

| Area | Endpoints |
|---|---|
| Accounts | `auth/register` · `login` · `logout` · `me` · `me/reviews` · `change-password` · `password-reset` (+ `confirm`) · `delete-account` |
| Catalog | `products` (website filters, search, ordering) · `products/{slug}` · `…/related` · `…/reviews` · `…/inquiry` · `products/compare` · `products/search-suggestions` · `categories` (+ `tree`) · `brands` · `reviews/{id}/helpful` |
| Wishlist | `wishlist` · `wishlist/ids` · `wishlist/sync` · `wishlist/{product_id}` (signed in) |
| Content | `home` · `config` · `banners` · `testimonials` · `services` (+ `inquiry`) · `serving-areas` (+ `check?pincode=`) · `service-availability` · `faqs` · `pages` · `blog/posts` (+ `comments`) · `blog/categories` |
| Forms | `contact` · `newsletter` |

> Note: the website's own AJAX endpoints (filtering, quick-view, reviews) remain under `/products/ajax/…` as server-rendered partials.

---

## Production deployment

The stack in `docker-compose.yml`:

| Service | Role |
|---|---|
| `caddy` | Public entry point on 80/443. Gets and renews the HTTPS certificate automatically, serves uploaded `/media/`, proxies everything else. Config: `deploy/Caddyfile`. |
| `web` | gunicorn + Django (`techzone.settings.production`), non-root, WhiteNoise serves `/static/`. Health check: `GET /healthz/`. |
| `db` | PostgreSQL 16 |
| `redis` | Cache, sessions and the shared rate-limit counters |

### First deploy

```bash
# On a server whose DNS for $DOMAIN (and www.$DOMAIN) points at it, ports 80+443 open:
cp .env.example .env
#   set DOMAIN, SECRET_KEY, DB_PASSWORD, EMAIL_*, ADMINS, ADMIN_URL (and SENTRY_DSN if used)
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py setup_roles       # optional staff groups
```

On every start `docker-entrypoint.sh` waits for Postgres, runs `migrate`, points the Sites
record at `$DOMAIN` (`manage.py sync_site`, so sitemap links are right) and runs
`check --deploy --fail-level WARNING` — the container refuses to start with an insecure config.
`docker compose` itself refuses to start while `DOMAIN`, `SECRET_KEY` or `DB_PASSWORD` is unset.

To try the whole stack locally, set `DOMAIN=localhost` (Caddy issues a locally-trusted certificate).

### Updating

```bash
git pull && docker compose up -d --build
```

### Backups

`scripts/backup.sh [dir]` dumps Postgres and archives `media/` (keeps the newest 14 of each).
Run it daily from cron and copy the directory **off the server**; the script header has the
cron line and the restore commands.

### Settings that fail closed

- `manage.py` defaults to `techzone.settings.development`; `wsgi.py`, `asgi.py` and the Docker
  image default to `techzone.settings.production`. `base.py` itself has `DEBUG` off and no hosts.
- Production raises `ImproperlyConfigured` for a missing / placeholder `SECRET_KEY` or empty
  `ALLOWED_HOSTS`.

### Security in production

- HTTPS only: SSL redirect, HSTS (1 year, preload), secure + HttpOnly cookies, `X-Frame-Options: DENY`.
- **Content-Security-Policy** from `CSP_DIRECTIVES` in `settings/base.py`
  (`core.middleware.ContentSecurityPolicyMiddleware`, off while `DEBUG` is on). Adding a new
  external script, font, map or video host means adding it there. `CSP_REPORT_ONLY=True` tests a
  change without blocking anything.
- **Public forms** (contact, newsletter, reviews, enquiries, blog comments, "helpful" votes) have a
  honeypot field and a per-IP rate limit (`core/ratelimit.py`, `RATELIMIT_FORMS`). The admin
  login is rate-limited too (`RATELIMIT_LOGIN`). Include `partials/honeypot.html` after
  `{% csrf_token %}` in any new public form and decorate its view with `@protect_form('name')`.
- The admin lives at `/$ADMIN_URL` (default `admin/`) and is not listed in `robots.txt`.
- Front-end libraries are self-hosted, version-pinned copies in `static/vendor/`
  (`npm run vendor`), not CDN links.
- Enquiry emails are sent from a background thread with `EMAIL_TIMEOUT`, so a slow SMTP server
  never delays a visitor.

### Monitoring

- `GET /healthz/` → `{"status": "ok"}` (checks the database; answered before host validation so
  Docker / load-balancer probes work).
- Server errors email everyone in `ADMINS`; set `SENTRY_DSN` for Sentry error tracking.
- All logs go to stdout: `docker compose logs -f web caddy`.

### CI

`.github/workflows/ci.yml` builds the front-end assets (and fails if the committed
`static/css/app.css` / `static/vendor/` are stale), runs `npm audit` and `pip-audit`,
`makemigrations --check`, the test suite, `check --deploy` under production settings,
`collectstatic`, and a Docker image build.

### Dependencies

`requirements.txt` and `package.json` pin exact versions. To upgrade: bump the pin, run the
tests (and `npm run build` for front-end packages), commit.

---

## Static assets & frontend build

Templates contain **markup only** — no inline `<style>`/`<script>`. CSS and JS live in
feature files under `static/` and are linked with `{% static %}`:

| Asset | Loaded from | Applies to |
|---|---|---|
| `css/base.css` · `js/base.js` | `base.html` | every page (chrome, theme toggle, toasts, CSRF, swipers) |
| `css/product-card.css` · `js/product-card.js` | `base.html` | every page (Quick View · Compare · Wishlist) |
| `js/header.js` | `partials/header.html` | every page (slide-in mobile menu) |
| `css/product-filters.css` · `js/product-filters.js` | the filter partials | product list + category |
| `css/product-detail.css` · `js/product-detail.js` | `products/detail.html` | product detail |
| `css/homepage.css` | `core/homepage.html` | homepage |
| `css/product-category.css` | `products/category.html` | category |
| `css/compare.css` · `js/compare.js` | `products/compare.html` | compare |
| `js/ajax-form.js` | contact / service / area / homepage | any `<form data-ajax-form>` |
| `css/tabler-icons.css` + `fonts/tabler-icons.woff2` | `base.html` | self-hosted icon font (preloaded) |

Two things stay inline **on purpose**: the theme bootstrap in `<head>` (blocking, before
the first stylesheet — moving it out reintroduces a light→dark flash on refresh) and the
`ld+json` / `json_script` data payloads.

### Commands

```bash
npm install                                  # once — installs the Tailwind CLI + Alpine + Swiper
npm run build                                # -> static/vendor/* + static/css/app.css (minified)
npm run vendor                               # only re-copy Alpine / Swiper into static/vendor/
npm run dev                                  # same, in watch mode while developing
python manage.py collectstatic --no-input    # production / Docker only
```

**Locally you do not need `collectstatic`.** With `DEBUG=True`, `django.contrib.staticfiles`
serves `static/` straight off disk.

### Notes

- **`TAILWIND_COMPILED` auto-enables** as soon as `static/css/app.css` exists, so the compiled
  bundle is used the moment you build it. Set `TAILWIND_COMPILED=False` to force the Tailwind
  CDN runtime instead — handy if you are editing classes without a watcher, but it generates
  CSS in the browser after first paint, so never ship it.
- **Run `npm run build` (or `npm run dev`) after adding Tailwind classes.** With a compiled
  bundle in place, a class that was never scanned simply will not exist.
- **`tailwind.config.js` scans `static/js/**/*.js` as well as the templates**, because some
  JS builds class strings at runtime (`updateCompareUI`, …). Removing that glob purges
  those utilities from the bundle.
- **The Docker image builds the CSS itself** (a Node stage runs `npm ci && npm run build`), so a
  deploy always ships a bundle that matches the templates. Still commit `static/css/app.css` and
  `static/vendor/` — local runs and CI use them, and CI fails if they are out of date.
- Icons are vendored from `@tabler/icons-webfont` (pinned 3.46.0). To upgrade, re-download the
  CSS + `woff2` at a pinned version and repoint the `@font-face` `src` at `../fonts/` — keep it
  query-free so whitenoise's manifest storage can rewrite it.

---

## Admin dashboard (Module 11)

- Branded admin (`TechZone Administration`) with a stats dashboard on the index (product/category/brand/review counts, inquiries this week, top categories, low-stock list).
- **Product bulk actions:** mark featured/trending, out-of-stock, restock, apply/clear 10% discount.
- **CSV export** on contact / product / service inquiries and newsletter subscribers.
- **Staff roles:** `python manage.py setup_roles` creates *Catalog Managers*, *Content Editors*, *Support Agents* permission groups.
- **Media validation:** product/review image uploads limited to 5 MB and image extensions.

---

## Product photos from Google Drive

Bulk-import product photos from a Google Drive for desktop folder instead of uploading them one by one.
Full guide: [docs/PRODUCT_IMAGES.md](docs/PRODUCT_IMAGES.md).

1. Set the folder in `.env`: `PRODUCT_IMAGES_DIR=G:\My Drive\Product Images`
2. Generate the folder tree — one `Category\SKU - Product name\` folder per active product:

   ```bash
   python manage.py create_product_folders                  # uses PRODUCT_IMAGES_DIR
   python manage.py create_product_folders --dry-run        # only list what would be created
   python manage.py create_product_folders --only-missing   # skip products that already have photos
   ```

   Folders that already exist (matched by SKU, slug or name, even if renamed or moved) are left
   alone and nothing is renamed or deleted, so re-run it whenever you add products. Only
   `G:\My Drive` must exist — `Product Images` and everything below it are created for you.
   Also available as `scripts\create_product_folders.bat` and the admin's **Create product folders** button.
3. Drop each product's photos into its folder (`main.jpg` = primary photo; `2.jpg`, `3.jpg`… set the order).
4. Import (photos are resized to 1600 px and saved as WebP):

   ```bash
   python manage.py import_product_images            # preview, nothing saved
   python manage.py import_product_images --apply    # import
   ```

   Or Admin → *Products* → **Import images from Drive** → **Preview** → **Import now**.

---

## Testing

```bash
python manage.py test                      # full suite
DJANGO_SETTINGS_MODULE=techzone.settings.production SECRET_KEY=... ALLOWED_HOSTS=example.com \
  python manage.py check --deploy          # security audit
```
Covers models, views, the REST API, validators, infinite scroll batches, the gallery, and the
production hardening (rate limits, honeypot, client-IP parsing, admin lockout, CSP header,
health check, `sync_site`). Runs on Django 5.2 LTS with Python 3.14.

---

## Module 5 — Related Products Algorithm

### 7 Scoring Signals

| Signal | Points | Description |
|---|---|---|
| Same brand + same category | 50 | Highest-intent match |
| Same category + price ±30% | 30 | Relevant alternative |
| Same category (any price) | 20 | Broad category match |
| Same brand (other category) | 15 | Brand loyalty signal |
| Frequently viewed together | up to 40 | Session co-view count × 4 |
| Popular in category | up to 20 | Views above category average |
| User browsing history | 25 | Appeared in same session |

All signals are **additive** — a product can score on multiple signals simultaneously.

### New Models

**`ProductViewLog`** — Records every product page view with session key, user (if logged in), and timestamp. Powers browsing-pattern and frequently-viewed-together signals.

**`FrequentlyViewedTogether`** — Denormalised pair-count table. Incremented in real time when two products appear in the same session within 30 minutes. Always stored with `product_a < product_b` (by pk string) to prevent duplicates.

### New Files (Module 5)

```
products/
  related.py          Complete algorithm module:
                        get_related_products()       — scored multi-signal list
                        get_frequently_viewed_together()
                        get_popular_in_category()
                        get_same_brand()
                        record_view()               — logs view + updates FVT pairs
  models.py           + ProductViewLog, FrequentlyViewedTogether
  views.py            + record_view() called on every detail page load
                      + ajax_related endpoint
  urls.py             + /products/ajax/related/<slug>/
  migrations/
    0004_module5_related_tracking.py

templates/products/
  detail.html         + 4 new related sections (FVT, scored, same brand, popular)
  partials/
    related_row.html  AJAX-replaceable related product grid
```

### Detail Page Sections (in order)

1. **Frequently Viewed Together** — products co-viewed in same session  
2. **You May Also Like** — full scored algorithm result  
3. **More from [Brand]** — same brand, sorted by featured/popularity  
4. **Popular in [Category]** — top by views_count  
5. **Recently Viewed** — session-based horizontal scroll strip

### API Endpoint

```
GET /products/ajax/related/<slug>/
Returns: { html: "...", count: N }
```

---

## All URLs

| URL | Description |
|---|---|
| `/` | Homepage |
| `/products/` | Product listing with all filters |
| `/products/categories/` | All categories overview |
| `/products/category/<slug>/` | Category detail |
| `/products/<slug>/` | Product detail (M4+M5) |
| `/products/compare/?ids=...` | Compare up to 3 products |
| `/products/ajax/filter/` | AJAX filter (JSON) |
| `/products/ajax/quick-view/<slug>/` | Quick view modal |
| `/products/ajax/wishlist/toggle/<uuid>/` | Wishlist toggle |
| `/products/ajax/review/<slug>/` | Submit review |
| `/products/ajax/inquiry/<slug>/` | Submit enquiry |
| `/products/ajax/helpful/<id>/` | Mark review helpful |
| `/products/ajax/related/<slug>/` | Related products (JSON+HTML) |
| `/blog/` | Blog list (featured + search + tags + pagination) |
| `/blog/category/<slug>/` | Posts in a blog category |
| `/blog/<slug>/` | Blog post detail (comments, share, related) |
| `/blog/<slug>/comment/` | Submit a comment (moderated) |
| `/pages/services/` | Services overview |
| `/pages/services/<slug>/` | Service detail + inquiry form |
| `/pages/services/<slug>/inquiry/` | AJAX service inquiry submit |
| `/pages/faqs/` | Site-wide FAQ accordion (grouped) |
| `/pages/p/<slug>/` | CMS flat page (Privacy, Terms, …) |
| `/pages/areas/<slug>/` | Serving-area detail page |
| `/sitemap.xml` | Auto-generated XML sitemap |
| `/robots.txt` | Robots file (links to sitemap) |

---

## Module 6 — CMS Management

A clean Django-admin-driven content layer (no external `django-cms` dependency).

### Blog / News (`blog` app)

| Model | Purpose |
|---|---|
| `BlogCategory` | Grouping with colour, icon, SEO meta |
| `BlogPost` | Articles with `taggit` tags, auto slug/excerpt/reading-time, draft→publish workflow, per-session view counting |
| `BlogComment` | Visitor comments, **held for moderation** until approved in admin |

Features: featured post hero, category & tag filtering, full-text search, popular-posts sidebar, pagination, share buttons, JSON-LD `BlogPosting` schema, related posts.

### Flat (CMS) Pages — `pages.FlatPage`
Editable content pages (Privacy Policy, Terms, Shipping & Returns, Warranty Policy) at `/pages/p/<slug>/`. Pages flagged `show_in_footer` auto-appear in the footer via the global context processor.

### Site-wide FAQs — `pages.FAQCategory` + `pages.GeneralFAQ`
Grouped, accordion-style FAQ page (distinct from product-level FAQs). Managed inline in the admin.

### SEO infrastructure (`core/sitemaps.py`)
`sitemap.xml` covers products, categories, blog posts/categories, services, serving areas, flat pages and static views. `robots.txt` is generated dynamically and references the sitemap.

> `taggit` was added to `INSTALLED_APPS` and `requirements.txt` (already present).

---

## Module 7 — Services Section

The `pages.Service` model was expanded into a full service catalogue.

**New / expanded fields:** `image`, `banner`, `color`, `price_info`, `cta_link`, `is_featured`, SEO meta.

| Model | Purpose |
|---|---|
| `Service` | Service entry with full description + detail page |
| `ServiceFeature` | "What's included" bullet points (admin inline) |
| `ServiceInquiry` | Per-service inquiry submissions with status workflow |

### Service detail page (`/pages/services/<slug>/`)
Hero with banner + pricing badge, rich description, features grid, sticky **AJAX inquiry form** (with WhatsApp + call fallbacks, email notification on submit), and an "other services" carousel. Seven services are seeded with descriptions, features and pricing.

### Bonus
The previously-missing `service_detail` and `area_detail` templates are now implemented, so those routes no longer 500. Serving-area detail pages gained contact info, pincodes and an optional Google Maps embed (groundwork for Module 8).

---

## Module 8 — Serving Areas Section

City-wise SEO pages backed by `pages.ServingArea` (slug URLs at `/pages/areas/<slug>/`).

- **List page** — featured cities as gradient cards + full A–Z grid, every card links to its detail page, plus a service-availability strip.
- **Detail page** — local description, service availability, **pincodes served**, optional **Google Maps embed**, area-specific contact card, an **AJAX inquiry form** (posts to the contact handler with the city pre-filled) and a WhatsApp deep-link.
- **Homepage** serving section now links each city chip to its detail page (falls back to the static list if no areas exist).
- All areas are included in `sitemap.xml`.

## Module 9 — Contact Section

- **Professional contact page** (`/contact/`) — quick-action cards (call / WhatsApp / email / hours), full inquiry form with type selector, store address, social links and an auto-embedded **Google Map** (uses `SiteSettings.google_maps_embed` or falls back to an address-based embed).
- **AJAX submission** with graceful non-JS fallback.
- **Email notifications** — every contact / area inquiry triggers `send_mail` to the business (console backend in dev, SMTP in production).
- **Admin inquiry management** — `ContactInquiryAdmin` with status workflow, admin notes, date hierarchy, search and bulk *Mark Resolved / In Progress* actions.

## Module 10 — Additional Features

| Feature | Implementation |
|---|---|
| **SEO** | `sitemap.xml`, dynamic `robots.txt`, canonical URLs, Open Graph + Twitter Card meta, `meta keywords`, per-page `og:*` blocks |
| **Breadcrumbs** | Reusable `partials/breadcrumbs.html` — visual bar **+ JSON-LD `BreadcrumbList`** schema; wired into blog detail |
| **Structured data** | `BlogPosting` + `BreadcrumbList` JSON-LD |
| **Analytics** | GA4 `gtag` snippet auto-injected from `SiteSettings.google_analytics_id` |
| **Performance** | `loading="lazy"` images, cached global nav/footer queries (5-min low-level cache in the context processor) |
| **Caching** | `CACHE_MIDDLEWARE_*` config; Redis-ready cache backend in `production.py` |
| **Security** | Auto-applied when `DEBUG=False`: SSL redirect, secure/HTTPOnly cookies, 1-yr HSTS, nosniff, referrer-policy, COOP; `CSRF_TRUSTED_ORIGINS` from env |
| **Production settings** | `techzone/settings/production.py` — PostgreSQL, Redis cache + cached sessions, SMTP email, logging, env-driven `ALLOWED_HOSTS`/`SECRET_KEY` |

Run production settings with `DJANGO_SETTINGS_MODULE=techzone.settings.production`.

> **Note:** the global nav/footer is cached for 5 minutes — content edits in the admin appear after the cache expires (or restart the server in dev).

---

## Coming Next — Module 11: Admin Dashboard

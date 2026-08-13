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
cp .env.example .env          # then edit values
python manage.py migrate
python manage.py seed_data
python manage.py setup_roles  # optional: create staff permission groups
npm install && npm run build  # frontend CSS -> static/css/app.css (see Static assets)
python manage.py runserver
```

**Site:** http://localhost:8000  
**Admin:** http://localhost:8000/admin/ → `admin / admin123`  
**REST API:** http://localhost:8000/api/v1/

---

## REST API (Module 14)

Public, read-only catalog API under `/api/v1/` (DRF, paginated 24/page, 120 req/min anon throttle):

| Endpoint | Description |
|---|---|
| `GET /api/v1/products/` | List products. Filters: `category=`, `brand=` (slugs), `min_price=`, `max_price=`, `condition=`, `in_stock=1`, `featured=1`, `trending=1`, `search=`, `ordering=price\|-created_at\|name` |
| `GET /api/v1/products/{slug}/` | Product detail incl. images + approved reviews |
| `GET /api/v1/categories/` · `/{slug}/` | Categories with product counts |
| `GET /api/v1/brands/` | Active brands |

> Note: AJAX UI endpoints (filtering, quick-view, wishlist, reviews) remain under `/products/ajax/…` as server-rendered partials; the DRF API above is the JSON catalog interface.

---

## Docker (Module 14)

```bash
docker compose up --build      # web (gunicorn) + postgres + redis
```
Migrations run automatically via `docker-entrypoint.sh`. Override secrets via env / a `.env` file (`SECRET_KEY`, `ALLOWED_HOSTS`, `DB_*`).

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
npm install                                  # once — installs the Tailwind CLI
npm run build                                # -> static/css/app.css (minified)
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
  JS builds class strings at runtime (`setView`, `updateCompareUI`). Removing that glob purges
  those utilities from the bundle.
- **The Docker image does not build the CSS** — it only runs `collectstatic`. Either commit
  `static/css/app.css` or add a node build stage before `docker compose up --build`.
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

## Testing

```bash
python manage.py test                      # full suite
python manage.py check --deploy            # security audit (use real SECRET_KEY)
```
Logic-level tests (models, REST API, validators) cover pricing/discount/stock/rating
properties and API filtering. Template-rendering view tests are included but require
Python ≤ 3.13 with Django 4.2 (Django 4.2's test-client template instrumentation has a
known incompatibility with Python 3.14; the views themselves serve 200s normally).

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

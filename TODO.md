# TechZone — Project Status & TODO

Updated: 2026-09-28. Reflects the **actual** state of the codebase.

Apps: `core`, `products`, `pages`, `blog` · Settings split: `base.py` /
`development.py` / `production.py` · DB: SQLite (dev), PostgreSQL (prod-ready).

Legend: `[x]` done · `[~]` partial · `[ ]` not started

> **All 15 modules complete.** Remaining open items are inherently-manual QA
> (cross-browser, Lighthouse, visual parity) and one decided deviation (custom CMS).

---

## Decisions taken

1. **CMS** — kept the **custom CMS** (editable `FlatPage`/`Banner`/`Service`/`ServingArea`/
   `FAQ`/`SiteSettings` via Django admin) rather than the `djangocms` package. Functionally
   a CMS; a full Django CMS swap was judged too high-risk a rewrite of working features.
2. **REST API** — **added Django REST Framework** (`/api/v1/`) alongside the existing
   server-rendered AJAX endpoints. DRF is the JSON catalog API; AJAX views remain the UI layer.

---

## Modules 1–10

| # | Module | Status |
|---|--------|--------|
| 1 | Landing page | `[x]` |
| 2 | Product categories | `[x]` |
| 3 | Product listing | `[x]` |
| 4 | Product details | `[x]` |
| 5 | Related products | `[x]` |
| 6 | CMS management | `[x]` (custom CMS — see decision #1) |
| 7 | Services | `[x]` |
| 8 | Serving areas | `[x]` |
| 9 | Contact | `[x]` |
| 10 | Additional (SEO/perf/security) | `[x]` (sitemaps, robots, JSON-LD, GA4, lazy-load, caching, security) |

---

## Module 11 — Admin Dashboard `[x]`

- [x] Rich model admins — inlines, image previews, fieldsets, `list_editable`, filters
- [x] **Branded admin site** (`TechZoneAdminSite`) — site header/title/index title
- [x] **Dashboard widget** on admin index — stat cards (products, categories, brands,
      reviews, inquiries 7d, newsletter, out-of-stock) + top-categories + low-stock panels
- [x] **Bulk actions** on Product — featured/trending, out-of-stock, restock, apply/clear 10% discount
- [x] **CSV export** — contact/product/service inquiries + newsletter (`ExportCsvMixin`)
- [x] **Media upload validation** — 5 MB + image-extension limit on product/review images
- [x] **Staff roles** — `setup_roles` command: Catalog Managers / Content Editors / Support Agents

## Module 12 — UI/UX `[x]` (manual audits remain)

- [x] Tailwind theme, dark/light toggle (localStorage), reusable partials, Swiper, Alpine
- [x] Lazy-load + `fetchpriority` images (Module 10)
- [x] **Tailwind compiled-build pipeline** — `package.json`, `tailwind.config.js`,
      `static_src/input.css`; `TAILWIND_COMPILED` setting switches CDN ↔ compiled
- [x] **Accessibility quick wins** — skip-to-content link, `aria-label`/`aria-hidden`
      on icon buttons, `<main id>` focus target
- [ ] Mobile-first device audit (mega menu, filters) — *manual*
- [ ] Skeleton/empty/error states audit for AJAX — *manual/optional*

## Module 13 — Database Models `[x]`

- [x] All required models (products, categories, brands, images, variants, attributes,
      reviews, services, areas, CMS pages, inquiries, tracking)
- [x] **Product DB indexes** added (is_active/featured/trending, category, brand, price, created_at)
- [x] **Media validators** on image fields
- [x] `makemigrations --check` → no drift (also repaired a pre-existing conflicting migration branch)

## Module 14 — Deliverables `[x]`

- [x] Split settings, `seed_data` sample data, WhiteNoise + manifest static storage
- [x] **`.env.example`** (full) + **`django-environ`** wired to load `.env` in `base.py`
- [x] **DRF read API** at `/api/v1/` — products/categories/brands, filtering, search, pagination, throttle
- [x] **Mobile app API** (2026-09-30) — full reference in `docs/MOBILE_API.md`:
      token auth (`accounts` app: register/login/logout/profile/change + reset password/delete account),
      server-side wishlist + guest sync, reviews (list/write/helpful/"my reviews"), product/service/contact
      enquiries, compare, related, search suggestions, category tree, home feed, app config, banners,
      testimonials, services, serving areas + pincode check, FAQs, CMS pages, blog + comments, newsletter.
      Reuses the site's forms, rate-limit scopes and enquiry emails; product lists no longer N+1 on ratings.
- [ ] Mobile app: push notifications (FCM) and an order/checkout flow — not in scope; the store is enquiry-based
- [x] **Docker** — `Dockerfile`, `docker-compose.yml` (web + postgres + redis),
      `.dockerignore`, `docker-entrypoint.sh` (waits for DB, migrates)
- [x] **`gunicorn`** + `djangorestframework` + `django-environ` + `redis` in `requirements.txt`
- [x] `collectstatic` verified (152 files) under production settings

## Module 15 — Final QA `[x]` (manual passes remain)

- [x] SEO: sitemap, robots, breadcrumbs, meta, Product JSON-LD
- [x] Performance: caching + `select_related`/`prefetch_related` + lazy-load + DB indexes
- [x] **`check --deploy`** → clean (with a real `SECRET_KEY`); set `X_FRAME_OPTIONS=DENY` in prod
- [x] **Tests written** — products (model/view/API), core (home/contact/validators), pages,
      plus the production hardening below. Full suite passes on Django 5.2 LTS / Python 3.14.
- [ ] Lighthouse pass + image `width`/`height` for CLS — *manual*
- [ ] Cross-browser / cross-device walkthrough — *manual*
- [ ] Visual parity review vs Croma / Reliance Digital / Best Buy — *manual*

---

## Production readiness (2026-09-28) `[x]`

- [x] Django 4.2 (EOL April 2026) → **5.2 LTS**; `STATICFILES_STORAGE` → `STORAGES`; Python 3.14 shim removed
- [x] **Fail-closed settings** — `base.py` has DEBUG off / no hosts / no key; `manage.py` → development,
      `wsgi.py`/`asgi.py`/Docker → production; production refuses placeholder `SECRET_KEY` / empty `ALLOWED_HOSTS`
- [x] **Docker** — Node stage builds CSS + vendor files, Python 3.14, non-root user, `HEALTHCHECK`,
      no `collectstatic || true`; entrypoint runs `migrate`, `sync_site`, `check --deploy --fail-level WARNING`
- [x] **Caddy** reverse proxy (`deploy/Caddyfile`) — automatic HTTPS, serves `/media/`; compose requires
      `DOMAIN` / `SECRET_KEY` / `DB_PASSWORD`
- [x] **Sites domain** from `SITE_DOMAIN` (`manage.py sync_site`) — sitemap no longer points at example.com
- [x] **Abuse protection** — honeypot + per-IP rate limits on every public form; admin login lockout
- [x] **Content-Security-Policy** header; Alpine + Swiper self-hosted and pinned (Swiper 11 → 12.2,
      fixes GHSA-hmx5-qpq5-p643)
- [x] Enquiry emails sent in a background thread with `EMAIL_TIMEOUT`
- [x] Monitoring — `/healthz/`, `ADMINS` error mail, optional Sentry (`SENTRY_DSN`)
- [x] Backups — `scripts/backup.sh` (Postgres dump + media archive, rotation, restore notes)
- [x] Exact version pins (`requirements.txt`, `package.json`); Pillow 12.3 + DRF 3.17.2 security fixes
- [x] CI — `.github/workflows/ci.yml` (assets, audits, migrations, tests, deploy check, Docker build)
- [x] Configurable admin path (`ADMIN_URL`), removed from `robots.txt`
- [x] `seed_data` refuses to run with DEBUG off (and never creates admin/admin123 there)

---

## Remaining (need a person / the live server)

- Replace the placeholder Privacy Policy / Terms of Service text (Admin -> Pages) with real legal copy
- Upload product photos (Admin -> Products -> Import images)
- Two-factor login for staff accounts (e.g. django-otp) — not yet added
- Off-site copy of the backup directory (rclone / S3) + a test restore
- Mobile + cross-browser device testing, Lighthouse, visual parity (need a browser/human)

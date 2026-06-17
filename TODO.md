# TechZone — Project Status & TODO

Updated: 2026-06-10. Reflects the **actual** state of the codebase.

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
- [x] **Docker** — `Dockerfile`, `docker-compose.yml` (web + postgres + redis),
      `.dockerignore`, `docker-entrypoint.sh` (waits for DB, migrates)
- [x] **`gunicorn`** + `djangorestframework` + `django-environ` + `redis` in `requirements.txt`
- [x] `collectstatic` verified (152 files) under production settings

## Module 15 — Final QA `[x]` (manual passes remain)

- [x] SEO: sitemap, robots, breadcrumbs, meta, Product JSON-LD
- [x] Performance: caching + `select_related`/`prefetch_related` + lazy-load + DB indexes
- [x] **`check --deploy`** → clean (with a real `SECRET_KEY`); set `X_FRAME_OPTIONS=DENY` in prod
- [x] **Tests written** — products (model/view/API), core (home/contact/validators), pages.
      Logic tests (models/API/validators) pass; template view tests need Python ≤3.13
      (Django 4.2 test-client × Python 3.14 instrumentation bug — app serves 200s normally)
- [ ] Lighthouse pass + image `width`/`height` for CLS — *manual*
- [ ] Cross-browser / cross-device walkthrough — *manual*
- [ ] Visual parity review vs Croma / Reliance Digital / Best Buy — *manual*

---

## Remaining (all manual / environmental)

- Mobile + cross-browser device testing, Lighthouse, visual parity (need a browser/human)
- Run `npm install && npm run build` once to generate the compiled CSS, then set `TAILWIND_COMPILED=True`
- Template view tests need Python ≤ 3.13 to run under Django 4.2's test client

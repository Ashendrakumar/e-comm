# TechZone — Premium Electronics Web Application

## ✅ Module 1 — Landing Page
## ✅ Module 2 — Product Categories
## ✅ Module 3 — Product Listing Page
## ✅ Module 4 — Product Details Page
## ✅ Module 5 — Related Products Algorithm  ← CURRENT

---

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

**Site:** http://localhost:8000  
**Admin:** http://localhost:8000/admin/ → `admin / admin123`

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

---

## Coming Next — Module 6: CMS Management

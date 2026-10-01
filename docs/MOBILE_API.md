# Mobile App API — `/api/v1/`

JSON API behind the customer mobile app. Everything the website shows is here:
the catalog, account sign-in, the wishlist, reviews, enquiries, services, serving
areas, CMS pages and the blog.

The store works by **enquiry**: there is no cart, checkout or order history.
Customers find a product, then ask about it (`POST /products/{slug}/inquiry/`),
call, or use WhatsApp (`GET /config/` has the numbers).

In development, open any URL in a browser to use DRF's browsable API.

---

## Conventions

| | |
|---|---|
| Base URL | `https://<domain>/api/v1/` — every path ends with `/` |
| Format | JSON in and out (`Content-Type: application/json`). Form-encoded bodies also work. |
| Auth | `Authorization: Token <token>`. The token comes from register / login. Leave the header off for guest use. |
| IDs | Products use UUIDs; everything else uses integer ids. Detail URLs use **slugs**. |
| Money | Decimal **strings**, e.g. `"54999.00"` (INR). Parse them as decimals, not floats. |
| Images | Absolute URLs, or `null` when there is no image. |
| Dates | ISO 8601 with a time zone (`2026-09-30T12:00:00+05:30`). |
| HTML | `description` (product), `content` (CMS page, blog post) and `map_embed` hold admin-written HTML. Render them in a WebView or an HTML widget. |

### Pagination

Lists marked **paged** return 24 items per page:

```json
{ "count": 120, "next": "https://…/api/v1/products/?page=2", "previous": null, "results": [ … ] }
```

Follow `next` until it is `null`, or pass `?page=N`. Lists not marked paged return a plain JSON array.

### Errors

| Status | Body | Meaning |
|---|---|---|
| 400 | `{"field": ["message", …]}` or `{"detail": "…"}` | Validation failed. Show the field messages next to the inputs. |
| 401 | `{"detail": "Authentication credentials were not provided."}` | Sign-in required, or the token was revoked. Clear the stored token and send the user to login. |
| 403 | `{"detail": "…"}` | Not allowed (e.g. comments are closed). |
| 404 | `{"detail": "No … matches the given query."}` | Unknown slug, or the item is inactive or unpublished. |
| 429 | `{"detail": "…"}` | Too many requests. Wait and retry, or show the message. |

### Rate limits

- **General:** 120 requests/min per IP for guests, 240/min per signed-in account.
- **Form posts:** reviews, enquiries, contact, newsletter, comments, register and password reset allow **10 per 10 minutes per IP**. The website draws on the same budget.
- **Sign-in:** login, change-password and delete-account allow 10 per 15 minutes. Password-reset emails allow 5 per hour.

---

## Accounts

The app signs users in with email and password. Each account has **one token**, shared by all of the user's devices. **Logging out, changing the password or resetting it revokes that token everywhere.**

| Method | Path | Auth | Body → Response |
|---|---|---|---|
| POST | `auth/register/` | — | `{email, password, first_name?, last_name?}` → **201** `{token, user}` |
| POST | `auth/login/` | — | `{login, password}` (`login` is the email or username) → `{token, user}` |
| POST | `auth/logout/` | ✔ | → **204** |
| GET | `auth/me/` | ✔ | → `user` |
| PATCH | `auth/me/` | ✔ | any of `{email, first_name, last_name}` → `user` |
| GET | `auth/me/reviews/` | ✔ | → **paged** reviews by this user, including pending ones (`is_approved`, `product {id, name, slug}`) |
| POST | `auth/change-password/` | ✔ | `{old_password, new_password}` → `{token, user}`. **Store the new token.** |
| POST | `auth/password-reset/` | — | `{email}` → always 200 (it never reveals whether the email has an account) |
| POST | `auth/password-reset/confirm/` | — | `{uid, token, new_password}` → `{token, user}` (signs the user in) |
| POST | `auth/delete-account/` | ✔ | `{password}` → **204**. Deletes the account permanently. Staff accounts get 403. |

`user` = `{id, username, email, first_name, last_name, date_joined}`

Passwords must pass the server's rules: at least 8 characters, not too common, not entirely numeric, and not too similar to the name or email. A failing password returns `{"password": ["…", …]}`.

**Password reset.** The email contains a *Reset ID* (`uid`) and a *Reset code* (`token`), and the user can type both into the app. If the server sets `API_PASSWORD_RESET_URL` (e.g. `toyollamobileapp://forgot-password?uid={uid}&token={token}`), the email also carries that deep link. A code works once and expires after 3 days, or as soon as the password changes.

---

## Home and configuration

| Method | Path | Notes |
|---|---|---|
| GET | `home/` | Every home-screen section in one call (see below). |
| GET | `config/` | Store details and choice lists. Fetch it at launch and cache it. |
| GET | `banners/?type=hero\|promo\|category\|sidebar` | Array. Use `mobile_image` when present, otherwise `image`. |
| GET | `testimonials/` | Array. |

`home/` returns `hero_banners`, `promo_banners`, `featured_categories`, `featured_brands`,
`featured_products`, `trending_products`, `new_arrivals`, `deals` (on sale and in stock),
`services`, `serving_areas`, `testimonials` and `why_choose_us`. Each product list holds up to 8 **product cards**.
Banners, categories, brands, testimonials and `why_choose_us` are cached for up to 10 minutes.

`config/` returns:

```json
{
  "store": {"name", "tagline", "logo", "favicon", "phone", "whatsapp", "email", "address", "working_hours"},
  "social_links": [{"platform": "instagram", "label": "Instagram", "url": "…"}],
  "pages": [{"title": "Privacy Policy", "slug": "privacy-policy", "icon": "ti-file-text"}],
  "choices": {
    "product_condition":    [{"value": "new", "label": "New"}, …],
    "product_ordering":     [{"value": "-created_at", "label": "Newest"}, …],
    "contact_inquiry_type": [{"value": "general", "label": "General"}, …],
    "banner_type":          [ … ]
  }
}
```

Icons (`icon` fields) are [Tabler icon](https://tabler.io/icons) class names such as `ti-truck`. Map them to your icon set; drop the `ti-` prefix to get the Tabler name.

---

## Catalog

### Product card

Lists, the home feed, related products, compare and the wishlist all use the same **product card**:

```json
{
  "id": "32e6aadd-…", "name": "Canon EOS R50", "slug": "canon-eos-r50", "sku": "TZ-32E6AADD",
  "brand": "Canon", "brand_slug": "canon", "category": "Cameras › Mirrorless", "category_slug": "mirrorless",
  "price": "79999.00", "sale_price": "69999.00", "effective_price": "69999.00", "discount_percent": 12,
  "condition": "new", "is_in_stock": true, "average_rating": 4.5, "review_count": 12,
  "is_featured": true, "is_trending": false, "is_new_arrival": true,
  "primary_image": "https://<ref>.supabase.co/storage/v1/object/public/media/products/r50.webp", "is_wishlisted": false
}
```

Show `effective_price`, with `price` struck through when `sale_price` is set.
`is_wishlisted` is always `false` for guests.

### Products

| Method | Path | Notes |
|---|---|---|
| GET | `products/` | **Paged** product cards. |
| GET | `products/{slug}/` | Full product: the card fields plus the detail fields below. |
| GET | `products/{slug}/related/` | `{related[8], frequently_viewed_together[4], popular_in_category[4], same_brand[4]}`. Hide empty sections. |
| GET | `products/{slug}/reviews/?sort=recent\|helpful\|rating_high\|rating_low` | **Paged** approved reviews. |
| POST | `products/{slug}/reviews/` | `{rating 1-5, content, title?, pros?, cons?, name, email}` → 201. Signed-in users can leave out `name` and `email`. Reviews appear only after staff approve them. |
| POST | `products/{slug}/inquiry/` | `{message, phone?, name, email}` → 201. Signed-in users can leave out `name` and `email`. The shop is emailed. |
| POST | `reviews/{id}/helpful/` | → `{helpful_count, counted}`. Counts once per user (or per IP for guests). |
| GET | `products/compare/?ids=a,b,c` | Up to 3 products (see below). |
| GET | `products/search-suggestions/?q=` | Type-ahead: `{products[6 cards], categories[5 {name, slug}], brands[5]}`. Needs 2+ characters. |

**`products/` query parameters** (all optional and combinable). These are the same filters as the website's filter panel:

| Param | Example | |
|---|---|---|
| `search` | `search=oled` | Name, short description, SKU, brand, category |
| `category` | `category=televisions` | Slug. **Includes sub-categories.** An unknown slug returns no products. |
| `brand` | `brand=sony,lg` | Slugs, comma-separated or repeated |
| `min_price` / `max_price` | `min_price=10000` | Applies to the list price (`price`) |
| `condition` | `condition=refurbished` | `new` / `refurbished` / `open_box` |
| `color` | `color=black` | Case-insensitive; comma-separated or repeated |
| `min_rating` | `min_rating=4` | Average of approved reviews |
| `min_discount` | `min_discount=20` | Percent off |
| `in_stock` `on_sale` `new_arrival` `featured` `trending` | `in_stock=1` | Flags |
| `ids` | `ids=<uuid>,<uuid>` | Fetch specific products, e.g. a guest wishlist or recently viewed. Up to 100. |
| `ordering` | `ordering=-avg_rating` | `created_at`, `price`, `name`, `views_count`, `avg_rating`. Prefix with `-` for descending. Default: `-created_at`. |

**Detail fields**, in addition to the card fields:
`short_description`, `description` (HTML), `stock`, `is_low_stock`, `savings_amount`,
`warranty`, `color`, `weight`,
`images` `[{image, alt_text, is_primary, order}]`,
`specifications` `[{name, value}]`,
`variants` `[{id, name, sku, price_modifier, price, stock, image, color_code}]` (`price` already includes the modifier),
`faqs` `[{question, answer}]`,
`rating_distribution` `[{stars, count, percent}]` (5 down to 1),
`reviews` (the 10 newest; fetch more from `…/reviews/`),
`breadcrumbs` `[{name, slug}]` (category path),
`web_url` (the website page, for share sheets).

**Compare** returns:

```json
{
  "products": [card, card],
  "general_rows": [{"label": "Brand", "values": ["Sony", "LG"], "differs": true}, …],
  "spec_rows":    [{"label": "Screen size", "values": ["55\"", null], "differs": true}, …],
  "best_price": "54999.00", "price_differs": true, "max_products": 3
}
```

`values` follow the order of `products`. `null` means that product has no value for the row, and rows no product has a value for are left out. Keep the compare list on the device; the server doesn't store it.

### Categories and brands

| Method | Path | Notes |
|---|---|---|
| GET | `categories/?root=1` · `?parent=<slug>` · `?featured=1` · `?search=` | **Paged.** `{id, name, slug, parent, parent_slug, icon, color, description, image, banner, banner_mobile, is_featured, product_count}` |
| GET | `categories/tree/` | Array of every active category, nested under `children`. Use it for the category menu. |
| GET | `categories/{slug}/` | Adds `breadcrumbs` and direct `children`. List its products with `products/?category={slug}`. |
| GET | `brands/?featured=1` · `?search=` | **Paged.** `{id, name, slug, logo, website, description, is_featured}` |
| GET | `brands/{slug}/` | One brand. List its products with `products/?brand={slug}`. |

`product_count` counts active products directly in the category, not in its sub-categories.

---

## Wishlist (signed in)

A signed-in user's wishlist is stored on the server. Guests keep theirs on the device and fetch its products with `products/?ids=…`. After sign-in, send the guest list to `wishlist/sync/` once, then clear it from the device.

| Method | Path | Body → Response |
|---|---|---|
| GET | `wishlist/` | → **paged** `[{product: card, added_at}]`, newest first |
| GET | `wishlist/ids/` | → `["<uuid>", …]`. Use it to fill in the hearts on product cards. |
| POST | `wishlist/` | `{product_id}` → 201 (added) or 200 (already saved), `{detail, ids}` |
| DELETE | `wishlist/{product_id}/` | → 204 |
| POST | `wishlist/sync/` | `{product_ids: [...]}` → the full list of ids after the merge |

A wishlist holds at most 200 items. Unknown or inactive products are skipped.

---

## Services, serving areas, FAQs, pages

| Method | Path | Notes |
|---|---|---|
| GET | `services/?featured=1` | Array `{id, title, slug, icon, short_description, image, color, price_info, is_featured}` |
| GET | `services/{slug}/` | Adds `description` (HTML), `banner`, `cta_text`, `cta_link`, `features [{icon, title, description}]` |
| POST | `services/{slug}/inquiry/` | `{message, phone?, city?, name, email}` → 201. Signed-in users can leave out `name` and `email`. |
| GET | `serving-areas/` | Array `{id, city, slug, state, is_featured}` |
| GET | `serving-areas/{slug}/` | Adds `description`, `contact_phone`, `contact_email`, `address`, `pincodes []`, `map_embed` (HTML iframe), `available_services []` |
| GET | `serving-areas/check/?pincode=380015` | `{pincode, serviceable, areas []}`. A pincode that isn't 6 digits returns 400. |
| GET | `service-availability/?area=<slug>` | Array `{id, icon, title, description}`: the services offered in that city |
| GET | `faqs/` | Array `[{name, slug, icon, faqs: [{id, question, answer}]}]`. Questions without a category come last, under "General". |
| GET | `pages/` · `pages/{slug}/` | CMS pages (About, Privacy Policy, Terms…). The detail adds `content` (HTML). |

---

## Blog

| Method | Path | Notes |
|---|---|---|
| GET | `blog/categories/` | Array `{id, name, slug, description, color, icon, post_count}` |
| GET | `blog/posts/?category=<slug>&tag=<name>&featured=1&search=&ordering=-views_count` | **Paged** `{id, title, slug, category, category_slug, author, featured_image, excerpt, is_featured, reading_minutes, views_count, published_at}` |
| GET | `blog/posts/{slug}/` | Adds `content` (HTML), `tags`, `allow_comments`, `comment_count`, `related_posts [3]`, `updated_at`, `web_url` |
| GET | `blog/posts/{slug}/comments/` | **Paged** approved comments `{id, name, content, created_at}` |
| POST | `blog/posts/{slug}/comments/` | `{content, name, email}` → 201. Signed-in users can leave out `name` and `email`. Comments appear after moderation. Returns 403 when comments are closed. |

---

## Contact and newsletter

| Method | Path | Body |
|---|---|---|
| POST | `contact/` | `{name, email, subject, message, phone?, inquiry_type?}` → 201. `inquiry_type` values come from `config.choices.contact_inquiry_type`; the default is `general`. |
| POST | `newsletter/` | `{email}` → 201 (subscribed) or 200 (already subscribed) |

### Field rules for every form

| Field | Rule |
|---|---|
| `name` | 2–100 characters |
| `subject` | 2–200 characters |
| `city` | 2–100 characters |
| `title` | up to 200 characters |
| `message`, `content` | 10–2000 characters |
| `pros`, `cons` | up to 1000 characters |
| `phone` | optional; 7–15 digits, may include `+ ( ) - .` and spaces |
| `email` | a valid email address |

Check these in the app before submitting. The server applies the same rules and returns field errors if a value fails.

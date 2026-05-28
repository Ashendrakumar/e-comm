# TechZone — Premium Electronics Web Application

## ✅ Module 1 — Landing Page
## ✅ Module 2 — Product Categories
## ✅ Module 3 — Product Listing Page
## ✅ Module 4 — Product Details Page  ← CURRENT

---

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

- Site:  http://localhost:8000/
- Admin: http://localhost:8000/admin/ → **admin / admin123**

---

## Module 4 — What's Included

### Features Delivered
| Feature | Status |
|---|---|
| Image carousel with Swiper.js | ✅ |
| Image gallery with zoom on hover | ✅ |
| Lightbox modal for full-screen viewing | ✅ |
| Previous/Next navigation in lightbox | ✅ |
| Thumbnail switcher | ✅ |
| Review submission form (client-side) | ✅ |
| Rating selection with star UI | ✅ |
| Pros/Cons fields in review form | ✅ |
| Rating distribution chart (5-star breakdown) | ✅ |
| Product inquiry form (in-stock products) | ✅ |
| Stock alert signup form (out-of-stock products) | ✅ |
| Email notifications for inquiries | ✅ |
| Email notifications for stock alerts | ✅ |
| Admin interface for managing inquiries | ✅ |
| Admin interface for managing stock alerts | ✅ |
| Status tracking for inquiries (New, In Progress, Resolved, Closed) | ✅ |
| Collapsible inquiry/stock alert sections | ✅ |
| AJAX form submission with toast notifications | ✅ |
| Dark mode support for all new components | ✅ |
| Mobile responsive forms and carousel | ✅ |

### New Models
```
products/
  models.py
    - ProductInquiry (product, name, email, phone, message, status)
    - StockAlert (product, email, name, is_active, notified)
```

### New Database Tables & Migrations
```
products/
  migrations/
    0004_add_inquiry_stockalert.py
```

### Updated Files (Module 4)
```
products/
  views.py              — Product detail, inquiry, review, stock alert handlers
  urls.py               — New endpoints for inquiries, reviews, stock alerts
  admin.py              — ProductInquiry, StockAlert, Wishlist admin panels
  models.py             — ProductInquiry & StockAlert models

templates/products/
  detail.html           — Enhanced with Swiper, forms, lightbox, rating chart
```

---

## New API Endpoints

| URL | Method | Description |
|---|---|---|
| `/products/<slug>/` | GET | Product detail page |
| `/products/<slug>/inquiry/` | POST | Submit product inquiry |
| `/products/<slug>/review/` | POST | Submit product review |
| `/products/<slug>/stock-alert/` | POST | Register for stock alerts |
| `/products/ajax/rating-dist/<slug>/` | GET | Rating distribution JSON |

---

## Form Features

### Review Submission Form
- Name, Email, Rating (required)
- Title, Content (required)
- Pros/Cons (optional)
- Client-side AJAX submission
- Toast success/error notifications
- Pending approval before display

### Inquiry Form
- Available only for in-stock products
- Name, Email, Phone (optional), Message (required)
- Stored in database for admin review
- Email notification to admin
- Status tracking in admin

### Stock Alert Signup
- Available only for out-of-stock products
- Name (optional), Email (required)
- Unique constraint: one alert per product per email
- Confirmation email sent to subscriber
- Marked as "notified" when product back in stock
- Email notification to subscriber when stock returns

---

## Admin Dashboard Enhancements

### ProductInquiry Admin
- List view with search and filtering
- Status dropdown (New, In Progress, Resolved, Closed)
- Mark as read/unread
- Filter by date created
- View full message and contact details

### StockAlert Admin
- View all active alerts
- Mark alert as notified
- Search by email or product name
- Filter by date
- Manage alert status

### Wishlist Admin
- View all wishlisted products
- Filter by user and date
- Search capability

---

## JavaScript Features

### Image Gallery (Swiper)
- Smooth carousel with prev/next buttons
- Pagination dots
- Touch-enabled on mobile
- Thumbnail switcher
- Zoom on hover effect

### Lightbox
- Full-screen image viewer
- Previous/Next navigation
- Close button (X)
- Keyboard navigation (Escape to close)

### Form Validation & Submission
- Client-side validation
- CSRF token handling
- Async form submission
- FormData handling
- Error/success toast notifications

### Rating Selection
- Visual star selection UI
- Click to select 1-5 stars
- Show selected rating count

---

## Database Queries

### Get Product with All Details
```python
product = Product.objects.select_related('category', 'brand')\
    .prefetch_related('images', 'reviews', 'attributes', 'inquiries', 'stock_alerts')\
    .get(slug='product-slug')
```

### Get Rating Distribution
```python
reviews = product.reviews.filter(is_approved=True)
distribution = {i: reviews.filter(rating=i).count() for i in range(1, 6)}
```

### Get Pending Inquiries (Admin)
```python
pending = ProductInquiry.objects.filter(status='new').order_by('-created_at')
```

---

## Email Configuration

Add to `.env`:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your@gmail.com
```

---

## Environment Variables (.env)

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL (SQLite used by default)
# DB_NAME=techzone
# DB_USER=postgres
# DB_PASSWORD=
# DB_HOST=localhost
# DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your@email.com
```

---

## Coming Next — Module 5: Shopping Cart & Checkout
- Add to cart functionality
- Cart management (update quantities, remove items)
- Persistent cart (session + database for auth users)
- Checkout flow
- Order placement
- Order management in admin
- Email order confirmations

# TechZone — Render.com Deployment Guide

This guide covers deploying the TechZone E-Commerce Django application to [Render.com](https://render.com).

---

## Architecture Overview

| Component | Technology |
|-----------|------------|
| Framework | Django 5.2 LTS + DRF |
| WSGI Server | Gunicorn |
| Database | PostgreSQL 16 |
| Cache / Sessions | Redis 7 |
| Static Files | WhiteNoise |
| Frontend Build | Tailwind CSS + Alpine.js + Swiper |
| Container | Docker (multi-stage build) |

---

## Prerequisites

- A [Render.com](https://render.com) account
- Your code pushed to a GitHub/GitLab/Bitbucket repository
- Node.js installed locally (for building frontend assets before pushing)

---

## Deployment Methods

### Method 1: Docker Deployment (Recommended)

Uses the existing `Dockerfile` for a fully containerized deploy.

#### Step 1: Push Code to Git

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

#### Step 2: Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: `techzone-db`
   - **Database**: `techzone`
   - **User**: `techzone_user`
   - **Plan**: Free (or Starter for production)
4. Save the following from the **Connections** panel:
   - Internal Database URL
   - External Database URL
   - Database name, user, password, host, port

#### Step 3: Create Redis Instance

1. Click **New** → **Redis**
2. Configure:
   - **Name**: `techzone-redis`
   - **Plan**: Free
3. Save the **Internal Redis URL** from the Connections panel

#### Step 4: Create Web Service

1. Click **New** → **Web Service**
2. Select your repository
3. Configure:
   - **Name**: `techzone`
   - **Branch**: `main`
   - **Environment**: **Docker**
   - **Plan**: Free (or Starter)
4. Render auto-detects the `Dockerfile`

#### Step 5: Configure Environment Variables

In the Web Service → **Environment** tab, add the following:

| Key | Value | Example |
|-----|-------|---------|
| `SECRET_KEY` | Long random string | `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | `False` | `False` |
| `ALLOWED_HOSTS` | Your Render URL | `techzone.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | HTTPS origin | `https://techzone.onrender.com` |
| `SITE_DOMAIN` | Your Render URL | `techzone.onrender.com` |
| `DB_NAME` | From PostgreSQL | `techzone` |
| `DB_USER` | From PostgreSQL | `techzone_user` |
| `DB_PASSWORD` | From PostgreSQL | `••••••••` |
| `DB_HOST` | Internal hostname | `dpg-xxx.render.com` |
| `DB_PORT` | `5432` | `5432` |
| `REDIS_URL` | Internal Redis URL | `rediss://red-xxx.render.com:6379` |
| `TRUSTED_PROXY_COUNT` | `1` | `1` |
| `ADMIN_URL` | Admin path (optional) | `admin/` |
| `SENTRY_DSN` | Error tracking (optional) | `https://xxx@yyy.ingest.sentry.io/zzz` |

#### Step 6: Configure Health Check

In the Web Service → **Settings** tab:
- **Health Check Path**: `/healthz/`

#### Step 7: Add Persistent Disk (for media files)

Render's filesystem is ephemeral. To persist uploaded media:

1. In **Settings** → **Disks**, click **Add Disk**
2. Configure:
   - **Name**: `media`
   - **Mount Path**: `/app/media`
   - **Size**: 1 GB (or as needed)

> **Alternative**: Use S3, Cloudinary, or Supabase Storage for media files instead of a disk.

#### Step 8: Deploy

Render automatically builds and deploys the Docker image. The `docker-entrypoint.sh` will:

1. Wait for PostgreSQL to be ready
2. Run `python manage.py migrate --noinput`
3. Sync the site domain (`python manage.py sync_site`)
4. Run `python manage.py check --deploy --fail-level WARNING`
5. Start Gunicorn on port 8000

#### Step 9: Create Superuser

After the first successful deploy, open the **Shell** tab and run:

```bash
python manage.py createsuperuser
```

#### Step 10: Verify

- Visit `https://techzone.onrender.com` — homepage should load
- Visit `https://techzone.onrender.com/admin/` — log in with superuser
- Visit `https://techzone.onrender.com/healthz/` — should return `{"status": "ok"}`
- Visit `https://techzone.onrender.com/api/v1/` — API should respond

---

### Method 2: Native Python Web Service (No Docker)

Deploy using Render's native Python runtime.

#### Step 1: Push Code to Git

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

#### Step 2: Create PostgreSQL & Redis

Same as Method 1, Steps 2–3.

#### Step 3: Create Web Service

1. Click **New** → **Web Service**
2. Select your repository
3. Configure:
   - **Name**: `techzone`
   - **Branch**: `main`
   - **Environment**: **Python**
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && npm ci && npm run build && python manage.py collectstatic --noinput
     ```
   - **Start Command**:
     ```bash
     gunicorn techzone.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --threads 2 --timeout 60
     ```

#### Step 4: Configure Environment Variables

Same as Method 1, Step 5.

#### Step 5: Configure Health Check & Disk

Same as Method 1, Steps 6–7.

#### Step 6: Deploy & Create Superuser

Same as Method 1, Steps 8–9.

---

## Post-Deployment Checklist

| Task | Command / Location |
|------|-------------------|
| Create superuser | Shell: `python manage.py createsuperuser` |
| Create staff roles | Shell: `python manage.py setup_roles` |
| Seed initial data | Shell: `python manage.py seed_data` |
| Verify health check | Visit `/healthz/` |
| Verify admin | Visit `/admin/` |
| Verify API | Visit `/api/v1/` |
| Verify sitemap | Visit `/sitemap.xml` |
| Verify robots.txt | Visit `/robots.txt` |
| Check static files | Visit `/static/css/app.css` |
| Set up Sentry | Add `SENTRY_DSN` env var |
| Configure email | Add `EMAIL_*` env vars |

---

## Custom Domain

1. In Web Service → **Settings** → **Custom Domains**, click **Add Custom Domain**
2. Enter your domain (e.g., `shop.example.com`)
3. Add the DNS records shown by Render to your domain registrar
4. Update environment variables:
   - `ALLOWED_HOSTS` → add your custom domain
   - `CSRF_TRUSTED_ORIGINS` → add `https://yourdomain.com`
   - `SITE_DOMAIN` → your custom domain
5. Render automatically provisions HTTPS via Let's Encrypt

---

## Environment Variables Reference

### Required

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (generate with `secrets.token_urlsafe(50)`) |
| `DEBUG` | Set to `False` in production |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins |
| `SITE_DOMAIN` | Primary domain for sitemaps and absolute URLs |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL username |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | PostgreSQL internal hostname |
| `DB_PORT` | PostgreSQL port (`5432`) |
| `REDIS_URL` | Redis connection URL |
| `TRUSTED_PROXY_COUNT` | Number of proxy hops (`1` for Render) |

### Optional

| Variable | Description |
|----------|-------------|
| `ADMIN_URL` | Admin URL path (default: `admin/`) |
| `SENTRY_DSN` | Sentry error tracking DSN |
| `EMAIL_HOST` | SMTP server hostname |
| `EMAIL_PORT` | SMTP port (`587`) |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password |
| `EMAIL_USE_TLS` | Use TLS for email (`True`) |
| `DEFAULT_FROM_EMAIL` | Default sender email address |
| `ADMINS` | Comma-separated admin emails for error notifications |
| `CSP_REPORT_ONLY` | Set to `True` to test CSP without blocking |

---

## Updating Your Deployment

### Docker Method

```bash
git add .
git commit -m "Update: description of changes"
git push origin main
```

Render automatically rebuilds and redeploys on every push.

### Manual Redeploy

1. Go to your Web Service in Render Dashboard
2. Click **Manual Deploy** → **Deploy latest commit**

---

## Troubleshooting

### Build fails

- Check the **Logs** tab for build errors
- Ensure `requirements.txt` and `package.json` are committed
- Verify `npm run build` succeeds locally

### Database connection errors

- Verify `DB_HOST` uses the **Internal** database URL (not external)
- Check that PostgreSQL is running and accessible
- Ensure `DB_PASSWORD` is correct

### Static files not loading

- Verify `collectstatic` ran during build
- Check that `static/css/app.css` exists
- Ensure WhiteNoise is configured in production settings

### Media files disappearing

- Add a **Disk** mounted at `/app/media`
- Or configure external storage (S3, Cloudinary, etc.)

### Health check failing

- Verify `/healthz/` returns 200 OK
- Check that the database is reachable
- Review application logs for errors

### Service sleeping (Free tier)

- Free Web Services sleep after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake
- Upgrade to Starter plan to prevent sleeping

---

## Rollback

1. Go to your Web Service → **Events** tab
2. Find the previous successful deploy
3. Click **Rollback to this deploy**

---

## Cost Estimation (Monthly)

| Service | Free | Starter |
|---------|------|---------|
| Web Service | $0 (sleeps) | $7 |
| PostgreSQL | $0 (90 days) | $15 |
| Redis | $0 | $15 |
| **Total** | **$0** | **$37** |

> Free PostgreSQL expires after 90 days. Export data before it expires or upgrade.

---

## Security Notes

- `DEBUG` is always `False` in production
- HTTPS is enforced with HSTS (1 year, preload)
- Secure + HttpOnly cookies
- `X-Frame-Options: DENY`
- Content-Security-Policy headers
- Rate limiting on public forms and admin login
- Honeypot fields on all public forms
- Self-hosted frontend libraries (no CDN dependencies)

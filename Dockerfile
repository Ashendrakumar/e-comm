# ── TechZone Electronics — production image ─────────────────────────

# 1) Front-end assets: compiled Tailwind CSS + pinned Alpine/Swiper copies.
FROM node:22-slim AS assets
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY tailwind.config.js ./
COPY static_src ./static_src
COPY static ./static
COPY templates ./templates
COPY blog ./blog
COPY core ./core
COPY pages ./pages
COPY products ./products
RUN npm run build

# 2) Python app.
FROM python:3.14-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=techzone.settings.production

WORKDIR /app

# psycopg2-binary and Pillow wheels bundle their C libraries; curl is for the health check.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY --from=assets /build/static/css/app.css ./static/css/app.css
COPY --from=assets /build/static/vendor ./static/vendor

# collectstatic needs settings to import, not real secrets: a throwaway key and
# host are enough. No `|| true` — a broken static build must fail the image.
RUN SECRET_KEY=build-only-$(python -c "import secrets;print(secrets.token_urlsafe(48))") \
    ALLOWED_HOSTS=localhost python manage.py collectstatic --noinput

# Run as an unprivileged user; only media/ needs to be writable.
RUN useradd --system --uid 1000 --home /app app \
    && mkdir -p /app/media \
    && chown -R app:app /app/media \
    && chmod +x /app/docker-entrypoint.sh
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "techzone.wsgi:application", "--bind", "0.0.0.0:8000", \
     "--workers", "3", "--threads", "2", "--timeout", "60", \
     "--access-logfile", "-", "--forwarded-allow-ips", "*"]

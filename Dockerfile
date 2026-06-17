# ── TechZone Electronics — production image ─────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=techzone.settings.production

WORKDIR /app

# System deps for psycopg2 / Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev libjpeg-dev zlib1g-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static at build time (uses dummy SECRET_KEY so the step never needs secrets)
RUN SECRET_KEY=build-only DJANGO_SETTINGS_MODULE=techzone.settings.production \
    ALLOWED_HOSTS=localhost python manage.py collectstatic --noinput || true

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "techzone.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]

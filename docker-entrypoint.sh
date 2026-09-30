#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres if DB_HOST is set
if [ -n "${DB_HOST:-}" ]; then
  echo "Waiting for database at $DB_HOST:${DB_PORT:-5432}..."
  for _ in $(seq 1 60); do
    if python -c "import socket,os,sys; s=socket.socket(); s.settimeout(2); \
      sys.exit(0 if s.connect_ex((os.environ['DB_HOST'], int(os.environ.get('DB_PORT','5432')))) == 0 else 1)"; then
      echo "Database is up."
      break
    fi
    sleep 1
  done
fi

echo "Applying migrations..."
python manage.py migrate --noinput

# Keep sitemap / absolute URLs on the real domain (django.contrib.sites).
if [ -n "${SITE_DOMAIN:-}" ]; then
  python manage.py sync_site
fi

# Refuse to serve with an insecure configuration.
python manage.py check --deploy --fail-level WARNING

exec "$@"

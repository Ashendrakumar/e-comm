#!/usr/bin/env bash
set -e

# Wait for Postgres if DB_HOST is set
if [ -n "$DB_HOST" ]; then
  echo "Waiting for database at $DB_HOST:${DB_PORT:-5432}..."
  until python -c "import socket,os,sys; s=socket.socket(); s.settimeout(2); \
    sys.exit(0) if s.connect_ex((os.environ['DB_HOST'], int(os.environ.get('DB_PORT','5432')))) == 0 else sys.exit(1)" 2>/dev/null; do
    sleep 1
  done
  echo "Database is up."
fi

echo "Applying migrations..."
python manage.py migrate --noinput

exec "$@"

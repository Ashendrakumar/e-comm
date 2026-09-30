#!/usr/bin/env bash
# Back up the Postgres database and uploaded media from the docker-compose stack.
#
#   scripts/backup.sh [backup-dir]        (default: ./backups)
#
# Keeps the newest $KEEP (default 14) of each. Run it daily from cron, e.g.
#   30 2 * * * cd /srv/techzone && scripts/backup.sh /srv/backups >> /var/log/techzone-backup.log 2>&1
# and copy the backup directory off the server (rclone / rsync / S3) — a backup
# on the same disk does not survive losing that disk.
#
# Restore:
#   gunzip -c db-YYYYmmdd-HHMMSS.sql.gz | docker compose exec -T db psql -U "$DB_USER" "$DB_NAME"
#   docker compose run --rm -v "$PWD/backups:/b" --entrypoint tar web -xzf /b/media-YYYYmmdd-HHMMSS.tar.gz -C /app
set -euo pipefail

DEST="${1:-./backups}"
KEEP="${KEEP:-14}"
STAMP="$(date +%Y%m%d-%H%M%S)"
[ -f .env ] && set -a && . ./.env && set +a
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-techzone}"

mkdir -p "$DEST"

echo "[$(date)] Dumping database $DB_NAME..."
docker compose exec -T db pg_dump -U "$DB_USER" --no-owner --clean --if-exists "$DB_NAME" \
  | gzip > "$DEST/db-$STAMP.sql.gz"

echo "[$(date)] Archiving media..."
docker compose run --rm --no-deps -T -v "$(cd "$DEST" && pwd):/backup" --entrypoint tar web \
  -czf "/backup/media-$STAMP.tar.gz" -C /app media

for kind in db media; do
  ls -1t "$DEST"/$kind-*.gz 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm --
done
echo "[$(date)] Done: $DEST/db-$STAMP.sql.gz, $DEST/media-$STAMP.tar.gz"

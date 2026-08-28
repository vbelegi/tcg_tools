#!/bin/sh
# Daily MySQL backup for Docker Compose deploy (run from /opt/tcg_tools).
set -eu

cd /opt/tcg_tools

BACKUP_DIR=/opt/tcg_tools/backups
mkdir -p "$BACKUP_DIR"

STAMP=$(date +%Y-%m-%d_%H%M)
FILE="$BACKUP_DIR/tcg_tools-${STAMP}.sql.gz"

docker compose exec -T db sh -c \
  'mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers "$MYSQL_DATABASE"' \
  | gzip > "$FILE"

find "$BACKUP_DIR" -name 'tcg_tools-*.sql.gz' -mtime +14 -delete

echo "Backup OK: $FILE ($(du -h "$FILE" | cut -f1))"

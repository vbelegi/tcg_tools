#!/bin/sh
# Upload MySQL dumps to offsite storage via rclone (run from /opt/tcg_tools).
# Prerequisite: rclone remote configured on the VPS (e.g. Google Drive).
set -eu

DEPLOY_PATH="${TCGTOOLS_DEPLOY_PATH:-/opt/tcg_tools}"

cd "$DEPLOY_PATH"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

BACKUP_DIR="${TCGTOOLS_BACKUP_DIR:-$DEPLOY_PATH/backups}"
RCLONE_REMOTE="${BACKUP_RCLONE_REMOTE:-tcg_backup}"
RCLONE_PATH="${BACKUP_RCLONE_PATH:-tcg_tools-backups}"

if ! command -v rclone >/dev/null 2>&1; then
  echo "rclone not found; install with: apt install rclone"
  exit 1
fi

if ! rclone listremotes | grep -Fx "${RCLONE_REMOTE}:" >/dev/null 2>&1; then
  echo "rclone remote not found: ${RCLONE_REMOTE}"
  exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup directory missing: $BACKUP_DIR"
  exit 1
fi

found=0
for _f in "$BACKUP_DIR"/tcg_tools-*.sql.gz; do
  if [ -e "$_f" ]; then
    found=1
    break
  fi
done
if [ "$found" -eq 0 ]; then
  echo "No local dumps in $BACKUP_DIR; run ./deploy/backup-db.sh first"
  exit 1
fi

DEST="${RCLONE_REMOTE}:${RCLONE_PATH}"
echo "Uploading dumps to ${DEST}..."
rclone copy "$BACKUP_DIR" "$DEST" \
  --include 'tcg_tools-*.sql.gz' \
  --no-update-modtime \
  --stats-one-line

count=$(rclone ls "$DEST" --include 'tcg_tools-*.sql.gz' | wc -l | tr -d ' ')
echo "Offsite backup OK: ${DEST} (${count} file(s) on remote)"

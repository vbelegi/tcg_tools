#!/bin/sh
# Deploy TCG Tools on the VPS (run from repo root, e.g. /opt/tcg_tools).
# Used by GitHub Actions (SSH) and can be run manually after git fetch.
set -eu

DEPLOY_PATH="${TCGTOOLS_DEPLOY_PATH:-/opt/tcg_tools}"
DEPLOY_REF="${DEPLOY_REF:-main}"
SKIP_BACKUP="${SKIP_BACKUP:-0}"
HEALTH_RETRIES="${HEALTH_RETRIES:-30}"
HEALTH_SLEEP_SEC="${HEALTH_SLEEP_SEC:-5}"

cd "$DEPLOY_PATH"

if [ "$SKIP_BACKUP" != "1" ]; then
  echo "Running pre-deploy backup..."
  ./deploy/backup-db.sh
else
  echo "Skipping pre-deploy backup (SKIP_BACKUP=1)."
fi

echo "Fetching origin and checking out ${DEPLOY_REF}..."
git fetch origin --tags

if git rev-parse -q --verify "refs/tags/${DEPLOY_REF}" >/dev/null 2>&1; then
  git checkout "$DEPLOY_REF"
elif git rev-parse -q --verify "refs/remotes/origin/${DEPLOY_REF}" >/dev/null 2>&1; then
  git checkout "$DEPLOY_REF"
  git pull --ff-only origin "$DEPLOY_REF"
elif git rev-parse -q --verify "${DEPLOY_REF}^{commit}" >/dev/null 2>&1; then
  git checkout "$DEPLOY_REF"
else
  echo "Unknown ref: ${DEPLOY_REF}"
  exit 1
fi

echo "Building and starting containers..."
docker compose up -d --build

echo "Waiting for health check..."
attempt=1
while [ "$attempt" -le "$HEALTH_RETRIES" ]; do
  if docker compose exec -T app curl -fsS http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    echo "Deploy OK: ${DEPLOY_REF} ($(git rev-parse --short HEAD))"
    exit 0
  fi
  echo "  attempt ${attempt}/${HEALTH_RETRIES}..."
  sleep "$HEALTH_SLEEP_SEC"
  attempt=$((attempt + 1))
done

echo "Health check failed after deploy."
docker compose ps
exit 1

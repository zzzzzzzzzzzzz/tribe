#!/usr/bin/env bash
# Invoked through SSH by GitHub Actions; GHCR_TOKEN arrives via stdin.
set -euo pipefail

cd /opt/tribe
test -f .env
test "$(stat -c %a .env)" = "600" || {
  echo "ERROR: /opt/tribe/.env must be chmod 600" >&2
  exit 1
}
if grep -Eq 'REPLACE_WITH_|YOUR_REAL_EMAIL_ADDRESS|YOUR_EMAIL_DOMAIN' .env; then
  echo "ERROR: edit placeholders in /opt/tribe/.env before deploying" >&2
  exit 1
fi
: "${GHCR_USER:?Missing GHCR_USER}"
: "${TAG:?Missing TAG}"

# Docker login reads the short-lived repository GITHUB_TOKEN from SSH stdin.
# It is not stored in GitHub repository files and is removed after the pull.
docker login ghcr.io -u "$GHCR_USER" --password-stdin
trap 'docker logout ghcr.io >/dev/null 2>&1 || true' EXIT

docker network inspect traefik-public >/dev/null 2>&1 || \
  docker network create traefik-public

docker compose -p tribe-proxy --env-file .env -f compose.proxy.yml config --quiet
docker compose -p tribe-proxy --env-file .env -f compose.proxy.yml up -d

docker compose -p tribe-prod --env-file .env -f compose.prod.yml config --quiet
docker compose -p tribe-prod --env-file .env -f compose.prod.yml pull
docker compose -p tribe-prod --env-file .env -f compose.prod.yml up -d --no-build --remove-orphans
docker compose -p tribe-prod --env-file .env -f compose.prod.yml ps

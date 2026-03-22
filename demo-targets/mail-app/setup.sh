#!/usr/bin/env bash
# -----------------------------------------------------------------------
# setup.sh — Provision test mail accounts in docker-mailserver
#
# Run AFTER: docker compose up -d (wait ~30s for mailserver to be healthy)
#
# Usage:
#   bash setup.sh
# -----------------------------------------------------------------------
set -euo pipefail

CONTAINER="mail-app-mailserver-1"

wait_for_container() {
  echo "Waiting for ${CONTAINER} to be healthy..."
  local retries=20
  while [[ $retries -gt 0 ]]; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${CONTAINER}" 2>/dev/null || echo "missing")
    if [[ "$STATUS" == "healthy" ]]; then
      echo "  Container is healthy."
      return 0
    fi
    echo "  Status: ${STATUS} — retrying in 5s... ($retries left)"
    sleep 5
    ((retries--))
  done
  echo "ERROR: Container did not become healthy in time."
  exit 1
}

add_account() {
  local email="$1"
  local password="$2"
  echo "  Adding account: ${email}"
  docker exec "${CONTAINER}" setup email add "${email}" "${password}"
}

# ── Wait for mailserver to be ready ─────────────────────────────────────
wait_for_container

# ── Create test accounts ─────────────────────────────────────────────────
echo ""
echo "Creating test mail accounts..."

add_account "alice@example.test"   "Alice1234!"
add_account "bob@example.test"     "Bob1234!"
add_account "admin@example.test"   "Admin1234!"

# ── List created accounts ────────────────────────────────────────────────
echo ""
echo "Current mail accounts:"
docker exec "${CONTAINER}" setup email list

echo ""
echo "Setup complete."
echo "  Webmail: http://localhost:8080"
echo "  Login:   alice@example.test / Alice1234!"

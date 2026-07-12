#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/scripts/lib.sh"
export ILIAS_PORTAL_HOME="$(cd "$SCRIPT_DIR" && pwd)"

echo "Starting ILIAS Portal Agent Kit..."

docker compose -f "$ILIAS_PORTAL_HOME/docker-compose.yml" up -d

"$ILIAS_PORTAL_HOME/scripts/start-backend.sh"

echo "Waiting for API on :8000..."
for i in $(seq 1 30); do
  if curl -sf "http://localhost:8000/api/auth/login/" -o /dev/null 2>/dev/null || \
     curl -sf "http://localhost:8000/admin/login/" -o /dev/null 2>/dev/null; then
    echo "API is up."
    exit 0
  fi
  sleep 1
done

echo "Warning: API did not respond within 30s. Check .run/backend.log" >&2
exit 1

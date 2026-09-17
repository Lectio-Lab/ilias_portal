#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/scripts/lib.sh"
export ILIAS_PORTAL_HOME="$(cd "$SCRIPT_DIR" && pwd)"

echo "Starting ILIAS Portal Agent Kit..."

BACKEND_PORT="${BACKEND_PORT:-8010}"

"$ILIAS_PORTAL_HOME/scripts/start-backend.sh"

echo "Waiting for API on :$BACKEND_PORT..."
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:$BACKEND_PORT/healthz" -o /dev/null 2>/dev/null; then
    echo "API is up."
    exit 0
  fi
  sleep 1
done

echo "Warning: API did not respond on :$BACKEND_PORT within 30s. Check .run/backend.log" >&2
exit 1

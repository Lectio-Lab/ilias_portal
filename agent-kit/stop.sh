#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/scripts/lib.sh"
KIT_HOME="$(resolve_kit_home)"

"$KIT_HOME/scripts/stop-backend.sh"
docker compose -f "$KIT_HOME/docker-compose.yml" down 2>/dev/null || true
echo "Stopped backend and Postgres."

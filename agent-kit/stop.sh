#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/scripts/lib.sh"
KIT_HOME="$(resolve_kit_home)"

"$KIT_HOME/scripts/stop-backend.sh"
echo "Stopped local ILIAS service."

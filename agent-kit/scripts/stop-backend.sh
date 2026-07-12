#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
KIT_HOME="$(resolve_kit_home)"
PID_FILE="$KIT_HOME/.run/backend.pid"

if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "Stopped backend (pid $pid)."
  fi
  rm -f "$PID_FILE"
else
  echo "Backend is not running."
fi

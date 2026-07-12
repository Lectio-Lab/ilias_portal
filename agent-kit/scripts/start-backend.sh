#!/usr/bin/env bash
# Start Django backend on the host (for reliable MFA browser on macOS).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
KIT_HOME="$(resolve_kit_home)"
BACKEND_DIR="$(resolve_backend_dir)"
VENV="$BACKEND_DIR/.venv"
RUN_DIR="$KIT_HOME/.run"
PID_FILE="$RUN_DIR/backend.pid"
LOG_FILE="$RUN_DIR/backend.log"

mkdir -p "$RUN_DIR"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Backend already running (pid $(cat "$PID_FILE"))."
  exit 0
fi

if [[ ! -d "$VENV" ]]; then
  echo "Virtualenv not found. Run ./install.sh first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

if [[ -f "$KIT_HOME/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$KIT_HOME/.env"
  set +a
elif [[ -f "$BACKEND_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$BACKEND_DIR/.env"
  set +a
fi

cd "$BACKEND_DIR"
nohup python manage.py runserver 0.0.0.0:8000 >"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"
echo "Backend started (pid $(cat "$PID_FILE")). Logs: $LOG_FILE"

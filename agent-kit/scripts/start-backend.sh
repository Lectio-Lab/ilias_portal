#!/usr/bin/env bash
# Start the localhost-only Python service on the host for visible MFA on macOS.
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

CREDS_FILE="$(resolve_agent_dir)/credentials/.env.local"
if [[ -f "$CREDS_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$CREDS_FILE"
  set +a
else
  echo "Credentials file not found. Run ./install.sh first." >&2
  exit 1
fi

cd "$BACKEND_DIR"
BACKEND_PORT="${BACKEND_PORT:-8010}"
# server.py hard-codes 127.0.0.1 rather than trusting a user-provided bind host.
if [[ -d "/Applications/Google Chrome.app" && -z "${PLAYWRIGHT_EXECUTABLE_PATH:-}" ]]; then
  export PLAYWRIGHT_BROWSER_CHANNEL=chrome
fi
nohup python server.py --port "$BACKEND_PORT" >"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"
echo "Local service started on 127.0.0.1:$BACKEND_PORT (pid $(cat "$PID_FILE")). Logs: $LOG_FILE"

#!/usr/bin/env bash
# ILIAS Portal Agent Kit — macOS installer (idempotent).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/scripts/lib.sh"
export ILIAS_PORTAL_HOME="$(cd "$SCRIPT_DIR" && pwd)"

echo "=== ILIAS Portal Agent Kit ==="
echo "Install directory: $ILIAS_PORTAL_HOME"
echo ""

INSTALL_BROWSER=false
if [[ "${1:-}" == "--install-browser" ]]; then
  INSTALL_BROWSER=true
elif [[ -n "${1:-}" ]]; then
  echo "Usage: ./install.sh [--install-browser]" >&2
  exit 1
fi

echo "Checking prerequisites..."
check_node
PY="$(check_python)"
echo "Using Python: $PY"
echo ""

CREDS_FILE="$(resolve_agent_dir)/credentials/.env.local"
if [[ ! -f "$CREDS_FILE" ]]; then
  "$SCRIPT_DIR/scripts/provision-interactive-auth.sh"
  echo ""
fi

BACKEND_DIR="$(resolve_backend_dir)"

echo "Setting up Python backend..."
BACKEND_DIR="$(resolve_backend_dir)"
VENV="$BACKEND_DIR/.venv"
if [[ ! -d "$VENV" ]]; then
  "$PY" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$BACKEND_DIR/requirements.txt"
if [[ -n "${PLAYWRIGHT_EXECUTABLE_PATH:-}" && -x "${PLAYWRIGHT_EXECUTABLE_PATH}" ]]; then
  echo "Using configured browser at $PLAYWRIGHT_EXECUTABLE_PATH for visible MFA."
elif [[ -d "/Applications/Google Chrome.app" ]]; then
  export PLAYWRIGHT_BROWSER_CHANNEL=chrome
  echo "Using installed Google Chrome for visible MFA; no Chromium download is needed."
elif [[ "$INSTALL_BROWSER" == true ]]; then
  echo "Google Chrome was not found; installing Playwright Chromium by explicit request."
  playwright install chromium
elif [[ -t 0 ]]; then
  read -r -p "Google Chrome was not found. Download Playwright Chromium for MFA now? [y/N] " reply
  if [[ "$reply" =~ ^[Yy]$ ]]; then
    playwright install chromium
  else
    echo "Install Google Chrome, or re-run ./install.sh --install-browser." >&2
    exit 1
  fi
else
  echo "Google Chrome was not found. Install it, or re-run ./install.sh --install-browser." >&2
  exit 1
fi

MCP_DIR="$(resolve_agent_dir)/mcp-server"
if [[ ! -d "$MCP_DIR/node_modules" ]]; then
  echo "Installing MCP server dependencies..."
  (cd "$MCP_DIR" && npm ci --omit=dev --ignore-scripts)
fi
if [[ ! -f "$MCP_DIR/dist/cli.js" ]]; then
  echo "Packaged MCP dist/ is missing. Re-extract a complete kit archive." >&2
  exit 1
else
  echo "MCP server dependencies and dist/ are present."
fi

chmod +x "$ILIAS_PORTAL_HOME"/install.sh \
  "$ILIAS_PORTAL_HOME"/start.sh \
  "$ILIAS_PORTAL_HOME"/stop.sh \
  "$ILIAS_PORTAL_HOME"/uninstall.sh \
  "$ILIAS_PORTAL_HOME"/scripts/*.sh \
  "$(resolve_agent_dir)/scripts/start-mcp.sh" 2>/dev/null || true

echo ""
echo "Generating MCP configs..."
"$SCRIPT_DIR/scripts/write-mcp-configs.sh"

echo ""
echo "Running health check..."
if "$ILIAS_PORTAL_HOME/start.sh"; then
  "$ILIAS_PORTAL_HOME/skill/ilias-portal/scripts/health-check.sh" || true
fi

echo ""
echo "=== Install complete ==="
echo "1. Run: ./start.sh (the local service is loopback-only)"
echo "2. Register MCP (see mcp-config/installed/ or INSTALL.md)"
echo "3. Install skill: copy skill/ilias-portal to your agent's skills folder"
echo "4. Refresh courses and complete university login/MFA in the browser"
echo ""
echo "Sample prompt: Check my ILIAS setup and list my courses."

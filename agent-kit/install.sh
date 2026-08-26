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

echo "Checking prerequisites..."
check_docker
check_node
PY="$(check_python)"
echo "Using Python: $PY"
echo ""

CREDS_FILE="$(resolve_agent_dir)/credentials/.env.local"
if [[ ! -f "$CREDS_FILE" ]]; then
  "$SCRIPT_DIR/scripts/provision-interactive-auth.sh"
  echo ""
fi

# Backend .env
if [[ ! -f "$ILIAS_PORTAL_HOME/.env" ]]; then
  cp "$ILIAS_PORTAL_HOME/.env.example" "$ILIAS_PORTAL_HOME/.env"
fi
if [[ -d "/Applications/Google Chrome.app" ]]; then
  if ! grep -q '^PLAYWRIGHT_BROWSER_CHANNEL=' "$ILIAS_PORTAL_HOME/.env" 2>/dev/null; then
    echo "PLAYWRIGHT_BROWSER_CHANNEL=chrome" >>"$ILIAS_PORTAL_HOME/.env"
    echo "Configured Playwright to use Google Chrome for MFA."
  fi
fi
BACKEND_DIR="$(resolve_backend_dir)"
if [[ ! -f "$BACKEND_DIR/.env" ]]; then
  cp "$ILIAS_PORTAL_HOME/.env" "$BACKEND_DIR/.env"
fi

echo "Starting Postgres (Docker)..."
docker compose -f "$ILIAS_PORTAL_HOME/docker-compose.yml" up -d

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
playwright install chromium

echo "Running database migrations..."
cd "$BACKEND_DIR"
python manage.py migrate --noinput

MCP_DIR="$(resolve_agent_dir)/mcp-server"
if [[ ! -d "$MCP_DIR/node_modules" ]]; then
  echo "Installing MCP server dependencies..."
  if [[ -f "$MCP_DIR/dist/cli.js" ]]; then
    (cd "$MCP_DIR" && npm ci --omit=dev)
  else
    (cd "$MCP_DIR" && npm ci)
  fi
fi
if [[ ! -f "$MCP_DIR/dist/cli.js" ]]; then
  echo "Building MCP server..."
  (cd "$MCP_DIR" && npm run build)
else
  echo "MCP server dependencies and dist/ are present."
fi

chmod +x "$ILIAS_PORTAL_HOME"/install.sh \
  "$ILIAS_PORTAL_HOME"/start.sh \
  "$ILIAS_PORTAL_HOME"/stop.sh \
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
echo "1. Run: ./start.sh"
echo "2. Register MCP (see mcp-config/installed/ or INSTALL.md)"
echo "3. Install skill: copy skill/ilias-portal to your agent's skills folder"
echo "4. Refresh courses and complete university login/MFA in the browser"
echo ""
echo "Sample prompt: Check my ILIAS setup and list my courses."

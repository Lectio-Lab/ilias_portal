#!/usr/bin/env bash
# Verify kit runtime: API, credentials file, MCP binary.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KIT_HOME="$(cd "$SKILL_ROOT/../.." && pwd)"

if [[ -f "$KIT_HOME/install.sh" ]]; then
  :
elif [[ -f "$KIT_HOME/../agent-kit/install.sh" ]]; then
  KIT_HOME="$(cd "$KIT_HOME/.." && pwd)"
fi

CREDS="$KIT_HOME/agent/credentials/.env.local"
MCP_CLI="$KIT_HOME/agent/mcp-server/dist/cli.js"
FAIL=0

BACKEND_PORT="${BACKEND_PORT:-8010}"

echo "Kit home: $KIT_HOME"

if [[ ! -f "$CREDS" ]]; then
  echo "FAIL: missing $CREDS"
  FAIL=1
else
  echo "OK: credentials file exists"
fi

if [[ ! -f "$MCP_CLI" ]]; then
  echo "FAIL: missing MCP binary at $MCP_CLI"
  FAIL=1
else
  echo "OK: MCP server built"
fi

if curl -sf "http://127.0.0.1:$BACKEND_PORT/healthz" -o /dev/null 2>/dev/null; then
  echo "OK: API responding on :$BACKEND_PORT"
else
  echo "WARN: API not reachable on :$BACKEND_PORT (run ./start.sh)"
  FAIL=1
fi

exit $FAIL

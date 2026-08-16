#!/usr/bin/env bash
# Loads agent credentials and starts the ILIAS Portal MCP server (stdio).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

resolve_home() {
  if [[ -n "${ILIAS_PORTAL_HOME:-}" ]]; then
    echo "$ILIAS_PORTAL_HOME"
    return
  fi
  local candidate
  candidate="$(cd "$SCRIPT_DIR/../.." && pwd)"
  if [[ -f "$candidate/install.sh" ]] || [[ -f "$candidate/agent/credentials/.env.local.example" ]]; then
    echo "$candidate"
    return
  fi
  candidate="$(cd "$SCRIPT_DIR/.." && pwd)"
  if [[ -f "$candidate/agent/credentials/.env.local.example" ]]; then
    echo "$candidate"
    return
  fi
  echo "$candidate"
}

KIT_HOME="$(resolve_home)"
CREDS_FILE="${DOTENV_PATH:-$KIT_HOME/agent/credentials/.env.local}"
MCP_DIR="$KIT_HOME/agent/mcp-server"

export ILIAS_PORTAL_HOME="$KIT_HOME"

REQUIRED_VARS=(
  PORTAL_EMAIL
  PORTAL_PASSWORD
)

if [[ ! -f "$CREDS_FILE" ]]; then
  echo "ilias-portal MCP: credentials file not found at $CREDS_FILE" >&2
  echo "Copy agent/credentials/.env.local.example to agent/credentials/.env.local and fill in all fields." >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$CREDS_FILE"
set +a

missing=()
for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    missing+=("$var")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "ilias-portal MCP: missing required variables in .env.local: ${missing[*]}" >&2
  exit 1
fi

if [[ ! -f "$MCP_DIR/dist/cli.js" ]]; then
  echo "ilias-portal MCP: building server..." >&2
  (cd "$MCP_DIR" && npm install && npm run build)
fi

exec node "$MCP_DIR/dist/cli.js"

#!/usr/bin/env bash
# Loads agent credentials and starts the ILIAS Portal MCP server (stdio).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CREDS_FILE="$REPO_ROOT/agent/credentials/.env.local"
MCP_DIR="$REPO_ROOT/agent/mcp-server"

REQUIRED_VARS=(
  PORTAL_EMAIL
  PORTAL_PASSWORD
  ILIAS_USERNAME
  ILIAS_PASSWORD
  ILIAS_COURSE_ID
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

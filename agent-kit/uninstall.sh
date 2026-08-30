#!/usr/bin/env bash
# Stop services and guide removal of the ILIAS Portal Agent Kit.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/scripts/lib.sh"
KIT_HOME="$(resolve_kit_home)"
PURGE=false

if [[ "${1:-}" == "--purge" ]]; then
  PURGE=true
elif [[ -n "${1:-}" ]]; then
  echo "Usage: ./uninstall.sh [--purge]" >&2
  exit 1
fi

echo "=== ILIAS Portal Agent Kit uninstall ==="
echo "Kit directory: $KIT_HOME"
echo ""

"$KIT_HOME/stop.sh"

if [[ "$PURGE" == true ]]; then
  echo "Purging local kit data (docker-data, .run, virtualenvs, node_modules)..."
  rm -rf \
    "$KIT_HOME/docker-data" \
    "$KIT_HOME/.run" \
    "$(resolve_backend_dir)/.venv" \
    "$(resolve_agent_dir)/mcp-server/node_modules" \
    "$KIT_HOME/mcp-config/installed" \
    "$KIT_HOME/.mcp.json"
  echo "Purged kit-local state."
else
  echo "Kept docker-data/, .venv, and node_modules. Re-run with --purge to delete them."
fi

cat <<EOF

Manual cleanup (outside this script):
1. Remove the ilias-portal MCP entry from your agent (Cursor, Claude Code, Codex, etc.).
2. Delete copied skills from your agent skills folder, if you installed them:
   - ilias-portal
   - find-teaching-content
   - hero-content-maker
3. Delete the extracted kit directory when you no longer need it:
   $KIT_HOME
4. Optional: remove shared caches if nothing else uses them:
   - Docker image postgres:16-alpine
   - Playwright Chromium cache (~/.cache/ms-playwright)

The kit does not install a system service or global npm package.
EOF

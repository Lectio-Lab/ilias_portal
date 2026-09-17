#!/usr/bin/env bash
# Write MCP config snippets with absolute paths for this install.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
KIT_HOME="$(resolve_kit_home)"
OUT_DIR="$KIT_HOME/mcp-config/installed"
AGENT_DIR="$(resolve_agent_dir)"
MCP_START="$AGENT_DIR/scripts/start-mcp.sh"

mkdir -p "$OUT_DIR"

write_json() {
  local file="$1"
  cat >"$file" <<EOF
{
  "mcpServers": {
    "ilias-portal": {
      "command": "/bin/bash",
      "args": ["$MCP_START"],
      "env": {
        "ILIAS_PORTAL_HOME": "$KIT_HOME"
      }
    }
  }
}
EOF
}

write_json "$OUT_DIR/cursor.mcp.json"
write_json "$OUT_DIR/claude-code.mcp.json"
cp "$OUT_DIR/claude-code.mcp.json" "$OUT_DIR/claude-desktop.mcp.json"

# Project-level .mcp.json for Claude Code in kit directory
cp "$OUT_DIR/claude-code.mcp.json" "$KIT_HOME/.mcp.json"

cat >"$OUT_DIR/README.txt" <<EOF
Generated MCP configs for: $KIT_HOME

Cursor: merge mcp-config/installed/cursor.mcp.json into your project's .cursor/mcp.json
Claude Code: .mcp.json is already in the kit root, or use:
  claude mcp add --scope project ilias-portal -- env ILIAS_PORTAL_HOME="$KIT_HOME" /bin/bash $MCP_START
Claude Desktop: merge claude-desktop.mcp.json into:
  ~/Library/Application Support/Claude/claude_desktop_config.json
EOF

echo "Wrote MCP configs to $OUT_DIR"

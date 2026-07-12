# Installation guide

## Architecture

- **Postgres** — Docker
- **Django API + Playwright MFA** — runs on your Mac (host)
- **MCP server** — Node.js stdio process
- **Skill** — `skill/ilias-portal/` (agentskills.io format)

## Per-agent setup

### Cursor

1. Open this kit folder as your Cursor project (or merge MCP into your project)
2. Copy `mcp-config/installed/cursor.mcp.json` into `.cursor/mcp.json`
3. Copy `skill/ilias-portal/` to `.cursor/skills/ilias-portal/` or `.agents/skills/ilias-portal/`
4. Restart Cursor

### Claude Code

1. `cd` into the kit directory
2. `.mcp.json` is written at kit root by `./install.sh`
3. Copy skill: `cp -r skill/ilias-portal ~/.claude/skills/`
4. Or: `claude mcp add --scope project ilias-portal -- env ILIAS_PORTAL_HOME="$(pwd)" node agent/mcp-server/dist/cli.js`

### Claude Desktop

1. Merge `mcp-config/installed/claude-desktop.mcp.json` into:
   `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Restart Claude Desktop
3. Upload `ilias-portal-skill.zip` under Settings → Skills (optional; Desktop uses MCP for tools)

### OpenAI Codex

1. Copy `skill/ilias-portal/` to `~/.agents/skills/ilias-portal/`
2. Configure MCP per `mcp-config/codex.mcp.json.example`

### Gemini CLI

1. Copy skill to `~/.agents/skills/ilias-portal/`
2. Configure MCP per `mcp-config/gemini.mcp.json.example`

## MFA

When `ilias_refresh_courses` runs, a browser window opens on your desktop (Chrome if installed). Complete university login and MFA there.

Logs: `.run/backend.log`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Docker not running | Start Docker Desktop |
| API not on :8000 | `./start.sh` and check `.run/backend.log` |
| MCP won't start | Fill `agent/credentials/.env.local`, rebuild with `cd agent/mcp-server && npm ci && npm run build` |
| No browser for MFA | Install Google Chrome or run `playwright install chromium` in backend venv |
| Health check | `skill/ilias-portal/scripts/health-check.sh` |

## Using with Claude (outside Cursor)

1. `./start.sh`
2. Install skill + MCP as above for Claude Code or Desktop
3. Chat: "Check my ILIAS setup" → complete MFA if prompted → publish or browse courses

Note: Claude.ai web chat alone cannot run local MCP; use Claude Code or Claude Desktop for tools.

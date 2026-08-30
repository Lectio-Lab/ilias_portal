# Installation guide

## Architecture

- **Postgres** — Docker
- **Django API + Playwright MFA** — runs on your Mac (host)
- **MCP server** — Node.js stdio process
- **Skills** — `skill/ilias-portal/`, `skill/find-teaching-content/`, and
  `skill/hero-content-maker/` (agentskills.io format)

## Per-agent setup

### Cursor

1. Open this kit folder as your Cursor project (or merge MCP into your project)
2. Copy `mcp-config/installed/cursor.mcp.json` into `.cursor/mcp.json`
3. Copy all three folders under `skill/` to `.cursor/skills/` or `.agents/skills/`
4. Restart Cursor

### Claude Code

1. `cd` into the kit directory
2. `.mcp.json` is written at kit root by `./install.sh`
3. Copy skills: `cp -r skill/ilias-portal skill/find-teaching-content skill/hero-content-maker ~/.claude/skills/`
4. Or: `claude mcp add --scope project ilias-portal -- env ILIAS_PORTAL_HOME="$(pwd)" node agent/mcp-server/dist/cli.js`

### Claude Desktop

1. Merge `mcp-config/installed/claude-desktop.mcp.json` into:
   `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Restart Claude Desktop
3. Upload `ilias-portal-skill.zip`, `find-teaching-content-skill.zip`, and
   `hero-content-maker-skill.zip` under Settings → Skills (optional; Desktop
   uses MCP for tools)

### OpenAI Codex

1. Copy `skill/ilias-portal/`, `skill/find-teaching-content/`, and
   `skill/hero-content-maker/` to `~/.agents/skills/`
2. Configure MCP per `mcp-config/codex.mcp.json.example`

### Gemini CLI

1. Copy all three folders under `skill/` to `~/.agents/skills/`
2. Configure MCP per `mcp-config/gemini.mcp.json.example`

## MFA

Run `scripts/provision-interactive-auth.sh` once. When `ilias_refresh_courses`
runs, a browser window opens on your desktop (Chrome if installed). Enter your
university credentials and complete MFA only there; they are not stored in the
agent credential file or in Postgres (only session cookies are kept).

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

## Uninstall

```bash
./uninstall.sh
./uninstall.sh --purge
```

`--purge` removes `docker-data/`, local virtualenvs, `node_modules`, and generated
`mcp-config/installed/` files. You still need to remove the MCP entry and any
copied skills from your agent manually.

## Security

Read [SECURITY.md](SECURITY.md) before installing on a shared machine. The kit binds
API and Postgres to localhost by default and rejects non-Ovidius download URLs.

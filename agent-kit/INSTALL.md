# Installation guide

## Architecture

- **Local ILIAS service** — small Python service bound only to `127.0.0.1:8010`
- **State** — owner-only JSON session cache in `agent/credentials/`
- **MCP server** — Node.js stdio process authenticated with one local bearer secret
- **MFA** — visible installed Google Chrome; Chromium is an explicit fallback only

There is no Docker, PostgreSQL, Django, or browser download in the normal install.

## Install

```bash
./install.sh
./start.sh
```

`install.sh` creates `agent/credentials/.env.local` with mode `0600`; it contains
only a generated local bearer token and optional course IDs. University credentials
are entered solely in the visible browser during MFA and are never stored.

If Chrome is absent, the installer asks before downloading Playwright Chromium. For
a non-interactive fallback use `./install.sh --install-browser`.

## Per-agent setup

Use the generated configuration under `mcp-config/installed/` for Cursor, Claude
Code, or Claude Desktop. For Codex and Gemini, follow the matching example in
`mcp-config/`. Copy the skill folders under `skill/` to the agent's skill directory.

## MFA and session

Run `ilias_refresh_courses` from the configured agent. Chrome opens for university
login and MFA if the saved session is missing or expired. The service then stores
only the returned `phpsessid` and `shibsession` cookies in its protected state file.

Logs are written to `.run/backend.log`.

## Troubleshooting

| Problem | Fix |
|---|---|
| Service not on `:8010` | Run `./start.sh`, then inspect `.run/backend.log` |
| MCP will not start | Run `./install.sh`; it provisions `.env.local` and core dependencies |
| No browser for MFA | Install Google Chrome or explicitly run `./install.sh --install-browser` |
| Health check | `skill/ilias-portal/scripts/health-check.sh` |

## Uninstall

```bash
./uninstall.sh
./uninstall.sh --purge
```

`--purge` removes local session state, virtual environments, `node_modules`, and
generated MCP config files. Remove MCP registrations and copied skills manually.

Read [SECURITY.md](SECURITY.md) before installing on a shared machine.

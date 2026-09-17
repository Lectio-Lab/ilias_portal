# ILIAS Portal Agent Integration

The shipped agent kit uses a Node MCP stdio server and a small Python localhost
service. `./install.sh` creates the local token, installs core dependencies without
install scripts, and uses Google Chrome for visible MFA without downloading Chromium.

## Credentials

`agent/credentials/.env.local` is generated with mode `0600`:

| Variable | Purpose |
|---|---|
| `PORTAL_LOCAL_TOKEN` | Bearer secret for the local Python service |
| `ILIAS_COURSE_ID` / `ILIAS_COURSE_IDS` | Optional default course IDs |
| `API_BASE_URL` | Loopback service URL, default `http://127.0.0.1:8010` |

University passwords are never stored. Refreshing courses opens visible MFA and
persists only session cookies in `agent/credentials/ilias-state.json`.

## Architecture

```text
Agent → MCP (stdio) → local bearer-authenticated service :8010 → ILIAS
```

`ilias_publish_slides` uploads existing files in the core kit. Markdown-to-PDF is
an optional authoring add-on; its tool gives installation guidance when unavailable.

## Testing

```bash
cd agent/mcp-server
npm ci
npm test
npm run smoke
```

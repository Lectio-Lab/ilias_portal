# ILIAS Portal Agent Integration

Agent-only ILIAS publishing from Cursor chat. No frontend required.

## Quick start

```bash
# 1. Generate a unique local API identity (university credentials stay blank)
./scripts/provision-interactive-auth.sh

# 2. Start backend + database
docker compose up -d

# 3. Restart Cursor (MCP ilias-portal enabled)

# 4. In Agent Mode:
# "Publish agent/samples/what-is-machine-learning.md to ILIAS as lecture slides"
```

## Credentials (`agent/credentials/.env.local`)

| Variable | Purpose |
|----------|---------|
| `PORTAL_EMAIL` | Django portal API login |
| `PORTAL_PASSWORD` | Django portal API password |
| `ILIAS_USERNAME` | Your zx account (7 characters) |
| `ILIAS_PASSWORD` | University ILIAS password |
| `ILIAS_COURSE_ID` | Default 7-digit course ref ID |
| `ILIAS_COURSE_IDS` | Optional comma-separated course IDs |
| `API_BASE_URL` | Default `http://localhost:8000` |

MCP never stores university credentials in interactive mode. Refreshing courses
opens a visible university login/MFA browser and stores only the resulting session cookies.

## Architecture

```
Cursor Agent → MCP (stdio) → Django API :8000 → ILIAS
                  ↑
         agent/credentials/.env.local
```

## MCP tools

| Tool | Description |
|------|-------------|
| `ilias_check_setup` | Env + session readiness |
| `ilias_publish_markdown_as_slides` | **Demo:** md → PDF → publish |
| `ilias_refresh_courses` | Establish ILIAS session (MFA) |
| `ilias_publish_slides` | Upload PDF/files |
| `ilias_publish_assignment` | Create exercise |
| `ilias_publish_announcement` | Post news |
| `ilias_get_course_contents` | Browse course |
| `ilias_find_course_items` | Find live items and fetch current exercise content |
| `ilias_edit_exercise` | Edit and verify an exact exercise URL |
| `ilias_download_file` | Download from ILIAS |

Exercise edits use a guarded two-step flow: find candidates first, resolve any
ambiguity, then edit the exact returned URL. The edit endpoint verifies that the
exercise still belongs to the requested course and that its title has not
changed, applies the requested fields once, re-fetches ILIAS, and returns the
verified URL.

## Demo sample

Committed sample markdown: [`agent/samples/what-is-machine-learning.md`](samples/what-is-machine-learning.md)

## Testing

```bash
cd agent/mcp-server
npm install
npm test
npm run smoke
```

## MFA note

`ilias_refresh_courses` may open Chromium inside Docker for university MFA. Complete login in the browser window, then retry publish.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| MCP won't start | Fill all required vars in `.env.local` |
| `ready_for_publish: false` | Run `ilias_refresh_courses`, complete MFA |
| Publish fails after retries | Check `docker compose logs backend` |
| Markdown not found | Use `agent/samples/what-is-machine-learning.md` |

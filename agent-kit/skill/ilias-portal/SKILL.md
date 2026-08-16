---
name: ilias-portal
description: >-
  Operate ILIAS courses via the ILIAS Portal API: publish markdown as PDF slides,
  upload files, post announcements, and manage course content. Use when the user
  mentions ILIAS, Ovidius, university courses, lecture slides, exercises,
  Übungen, course announcements, or academic platform tasks.
compatibility: >-
  Requires ILIAS Portal Agent Kit running (./start.sh), ilias-portal MCP server,
  Node 18+, Docker Desktop, and a generated local Portal API identity.
metadata:
  mcp-server: ilias-portal
  version: 1.2.0
---

# ILIAS Portal Agent Skill

Agent-only workflow. No frontend. Configuration lives in `agent/credentials/.env.local` inside the kit directory (`ILIAS_PORTAL_HOME`).

## Prerequisites

1. Unzip the agent kit and run `./install.sh` then `./start.sh`
2. Register the `ilias-portal` MCP server (see `INSTALL.md` or `mcp-config/installed/`)
3. Install this skill in your agent (Cursor, Claude Code, Codex, Gemini CLI, or upload zip to Claude.ai)

## Authentication

Run `scripts/provision-interactive-auth.sh` once to generate a unique local API
identity. University credentials remain blank and must be entered only in the
visible university browser window opened by `ilias_refresh_courses`.

Never ask the user to send a university password in chat.

## Quickstart

1. User runs `./start.sh` in the kit directory
2. Call `ilias_check_setup`
3. If the session is invalid → call `ilias_refresh_courses`; the user completes login and MFA in the visible browser
4. For demo publish → `ilias_publish_markdown_as_slides` with `agent/samples/what-is-machine-learning.md`
5. End with **"Successfully published ..."** or **"Unable to publish ..."** plus URL or error

## Tool selection

| User intent | Tool |
|-------------|------|
| Check if ready | `ilias_check_setup` |
| List courses | `ilias_refresh_courses` for interactive login, then `ilias_list_courses` |
| Publish markdown as PDF slides | `ilias_publish_markdown_as_slides` |
| Refresh ILIAS session (MFA) | `ilias_refresh_courses` |
| Upload existing PDF/files | `ilias_publish_slides` |
| Create assignment | `ilias_publish_assignment` |
| Post announcement | `ilias_publish_announcement` |
| Browse course contents | `ilias_get_course_contents` |

## Course selection

After interactive login, use the returned course list and ask the user to select a course when needed.

```
1. Course ID returned by ILIAS
2. Another returned course
3. Enter a different course ID
```

## Publish markdown workflow

1. `ilias_check_setup`
2. If session invalid → `ilias_refresh_courses` once
3. `ilias_publish_markdown_as_slides` with:
   - `markdown_path`: user path or `agent/samples/what-is-machine-learning.md` (relative to kit root)
   - `course_id`: optional, defaults to env
4. Report outcome clearly

## MFA recovery

If ILIAS auth fails:
1. Stop retrying after tool exhausts retries
2. Run `ilias_refresh_courses` once
3. The user completes university login and MFA in the browser window (Chrome on macOS if installed)
4. Retry publish once

See [references/mfa-setup.md](references/mfa-setup.md).

## Never do

- Mention frontend or website credential pages
- Pass or request passwords in chat or tool arguments
- Retry auth failures blindly in a loop

## Additional resources

- [workflows.md](references/workflows.md)
- [api-errors.md](references/api-errors.md)
- [mfa-setup.md](references/mfa-setup.md)

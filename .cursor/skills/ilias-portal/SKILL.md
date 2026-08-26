---
name: ilias-portal
description: >-
  Operate ILIAS courses via the ILIAS Portal API: publish markdown as PDF slides,
  upload files, post announcements, and manage course content. Use when the user
  mentions ILIAS, Ovidius, university courses, lecture slides, exercises,
  Übungen, course announcements, or academic platform tasks.
compatibility: Requires ilias-portal MCP server, backend at localhost:8000, and agent/credentials/.env.local with all fields.
metadata:
  mcp-server: ilias-portal
  version: 1.1.0
---

# ILIAS Portal Agent Skill (Agent-Only)

No frontend. No website. All configuration lives in `agent/credentials/.env.local`.

## Required env vars

| Variable | Example | Hint |
|----------|---------|------|
| `PORTAL_EMAIL` | you@example.com | Portal API login |
| `PORTAL_PASSWORD` | ... | Portal API password |
| `ILIAS_USERNAME` | zxofp67 | Starts with `zx`, 7 characters |
| `ILIAS_PASSWORD` | ... | University ILIAS password |
| `ILIAS_COURSE_ID` | 5658784 | 7-digit course ref ID |
| `ILIAS_COURSE_IDS` | (optional) | Comma-separated extra courses |

If any are missing, tell the user to fill `agent/credentials/.env.local` and restart MCP. Never send them to a website.

## Demo quickstart

1. User runs `docker compose up -d`
2. Call `ilias_check_setup`
3. If `ready_for_publish` is false and session invalid → call `ilias_refresh_courses` (MFA may open Chromium)
4. For markdown upload demo → call `ilias_publish_markdown_as_slides` with `agent/samples/what-is-machine-learning.md`
5. End with **"Successfully published ..."** or **"Unable to publish ..."** plus URL or error

## Tool selection

| User intent | Tool |
|-------------|------|
| Check if ready | `ilias_check_setup` |
| Publish markdown as PDF slides | `ilias_publish_markdown_as_slides` |
| Refresh ILIAS session (MFA) | `ilias_refresh_courses` |
| Upload existing PDF/files | `ilias_publish_slides` |
| Create assignment | `ilias_publish_assignment` |
| Post announcement | `ilias_publish_announcement` |
| Browse course contents | `ilias_get_course_contents` |

Do **not** use `ilias_list_courses` for the demo path. Use `ILIAS_COURSE_ID` from env.

## Course selection menu

When multiple courses in `ILIAS_COURSE_IDS`, present:

```
1. Course 5658784 (default)
2. Course 5658785
3. Enter a different course ID
```

User can reply with a number or natural language.

## Publish markdown workflow

1. `ilias_check_setup`
2. If session invalid → `ilias_refresh_courses` once
3. `ilias_publish_markdown_as_slides` with:
   - `markdown_path`: user path or `agent/samples/what-is-machine-learning.md`
   - `course_id`: optional, defaults to env
4. Report outcome clearly

## MFA recovery

If ILIAS auth fails:
1. Stop retrying after tool exhausts retries
2. Tell user to run `ilias_refresh_courses`
3. Complete MFA in Chromium if window opens
4. Retry publish once

See [references/mfa-setup.md](references/mfa-setup.md).

## Never do

- Mention frontend, Angular, or `/credentials` page
- Use cached course list for demo publish
- Pass passwords in chat or tool arguments
- Retry auth failures blindly

## Additional resources

- [workflows.md](references/workflows.md)
- [api-errors.md](references/api-errors.md)
- [mfa-setup.md](references/mfa-setup.md)

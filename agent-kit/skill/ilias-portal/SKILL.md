---
name: ilias-portal
description: >-
  Operate ILIAS courses via the ILIAS Portal API: publish markdown as PDF slides,
  upload files, post announcements, find course items, and safely edit existing
  exercise content. Use when the user mentions ILIAS, Ovidius, university
  courses, lecture slides, exercises, Übungen, editing an exercise, changing an
  assignment deadline or instructions, editing the last/latest assignment or
  course content, course announcements, or academic platform tasks.
compatibility: >-
  Requires ILIAS Portal Agent Kit running (./start.sh), ilias-portal MCP server,
  Node 18+, Docker Desktop, and a generated local Portal API identity.
metadata:
  mcp-server: ilias-portal
  version: 1.4.0
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
| Find an item from a title/query | `ilias_find_course_items` |
| Edit an existing exercise | `ilias_edit_exercise` |
| Edit the last/latest content | Resolve the exact item, then `ilias_edit_exercise` |

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

## Edit existing exercise workflow

1. Call `ilias_find_course_items` with the course ID, the user's identifying
   words, and `item_type: "Exercise"`.
2. If there are no matches, report that and ask for a different title or course.
3. If multiple plausible matches remain, show their titles, sections, and URLs;
   ask the user which one they mean. Never select the first result silently.
4. Show the selected exercise's current content and exact URL. If it has multiple
   assignment units, resolve the exact `assignment_id`.
5. Confirm the concrete before/after changes with the user.
6. Call `ilias_edit_exercise` once with the exact returned URL and current exact
   title as `expected_title`. For each changed content field, also pass its
   current value from discovery (`expected_description`,
   `expected_assignment_title`, `expected_instruction`, or
   `expected_deadline`). Do not retry this write automatically.
7. Only report success when the tool returns `verified: true`. Include the
   returned updated URL. Otherwise state that the update was not verified and
   include the actionable error and URL.

## Edit last/latest content workflow

When the user says "last", "latest", "most recent", or "the assignment we just
created/edited":

1. Prefer an exact exercise URL from the current request, the open ILIAS page,
   or the immediately preceding successful find, publish, or edit result.
2. If there is no known URL, resolve the course and fetch live contents. Use a
   server-provided creation/start timestamp when available. Never infer recency
   from visual page order, search ranking, title numbering, or a stale cache.
3. If recency cannot be proved or multiple candidates remain, show their titles
   and URLs and ask the user to select one. Do not write yet.
4. Re-fetch the chosen item's current title, instructions, deadline, and
   assignment IDs immediately before editing.
5. Follow the existing exercise-edit workflow, including current `expected_*`
   values, one write attempt, post-update verification, and the returned URL.

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
- Guess an item URL, silently resolve an ambiguous match, or report an edit
  before the post-update verification succeeds

## Additional resources

- [workflows.md](references/workflows.md)
- [api-errors.md](references/api-errors.md)
- [mfa-setup.md](references/mfa-setup.md)

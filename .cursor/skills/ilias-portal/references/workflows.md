# Agent-Only Workflows

## Workflow 1: First-time setup (no website)

1. `cp agent/credentials/.env.local.example agent/credentials/.env.local`
2. Fill all required fields (portal + ILIAS + course ID)
3. `docker compose up -d`
4. Restart Cursor with MCP `ilias-portal` enabled
5. Agent calls `ilias_check_setup`
6. If session invalid → `ilias_refresh_courses` (complete MFA if prompted)

## Workflow 2: Demo publish markdown as PDF

User prompt example:

> Publish agent/samples/what-is-machine-learning.md to ILIAS as lecture slides.

Agent steps:

1. `ilias_check_setup`
2. `ilias_refresh_courses` if `ready_for_publish` is false
3. `ilias_publish_markdown_as_slides` with default sample path
4. Return success message + ILIAS URL

## Workflow 3: Publish custom markdown

1. User provides path to `.md` file
2. Optional: user picks course from numbered menu if multiple `ILIAS_COURSE_IDS`
3. `ilias_publish_markdown_as_slides` with `markdown_path` and optional `course_id`
4. User verifies on ILIAS manually

## Workflow 4: Publish existing PDF

1. `ilias_check_setup`
2. `ilias_publish_slides` with `course_id` from env and `file_paths` pointing to PDF

## Course ID resolution

- Default: `ILIAS_COURSE_ID` from `.env.local`
- Multiple courses: show numbered menu from `ILIAS_COURSE_IDS`
- User override: pass explicit `course_id` to publish tool

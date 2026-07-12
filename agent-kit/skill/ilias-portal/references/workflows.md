# Agent-Only Workflows

Paths are relative to the kit root (`ILIAS_PORTAL_HOME`).

## Workflow 1: First-time setup

1. `cp agent/credentials/.env.local.example agent/credentials/.env.local`
2. Fill all required fields (portal + ILIAS + course ID)
3. `./install.sh` then `./start.sh`
4. Register MCP server for your agent (see `INSTALL.md`)
5. Agent calls `ilias_check_setup`
6. If session invalid → `ilias_refresh_courses` (complete MFA in browser if prompted)

## Workflow 2: Demo publish markdown as PDF

User prompt example:

> Publish agent/samples/what-is-machine-learning.md to ILIAS as lecture slides.

Agent steps:

1. `ilias_check_setup`
2. `ilias_refresh_courses` if `ready_for_publish` is false
3. `ilias_publish_markdown_as_slides` with default sample path
4. Return success message + ILIAS URL

## Workflow 3: Browse courses

1. `ilias_check_setup`
2. `ilias_refresh_courses` if session invalid
3. Report courses from refresh result or call `ilias_get_course_contents` for a specific course

## Workflow 4: Publish existing PDF

1. `ilias_check_setup`
2. `ilias_publish_slides` with `course_id` from env and `file_paths` pointing to PDF

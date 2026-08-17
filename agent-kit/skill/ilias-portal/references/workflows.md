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

## Workflow 5: Find and edit an existing exercise

User prompt example:

> Edit the instructions in exercise CNN Homework so students must also submit a confusion matrix.

Agent steps:

1. Resolve the course ID from the current conversation or course list.
2. Call `ilias_find_course_items` with the identifying words and
   `item_type: "Exercise"`.
3. Resolve safely:
   - Zero candidates: ask for a different title or course.
   - One clear candidate: present its current title, content, and URL.
   - Multiple plausible candidates: present titles, sections, and URLs, then ask
     the user to choose. Do not edit yet.
4. If the candidate has multiple assignment units, present their IDs and titles
   and resolve the exact `assignment_id`.
5. Confirm the exact before/after fields. Preserve fields the user did not ask to
   change.
6. Call `ilias_edit_exercise` once with:
   - `course_id`
   - exact `exercise_url` from the find result
   - exact current exercise title as `expected_title`
   - current value for each content field being replaced, using the matching
     `expected_*` argument from the find result
   - only requested replacement fields
   - `assignment_id` when required
7. Treat only `verified: true` as success. Return the updated title/content
   summary and the tool's `url`.
8. If the server reports a stale title, missing course membership, ambiguity, or
   failed verification, stop. Re-run discovery only after explaining the issue;
   never blindly retry the edit.

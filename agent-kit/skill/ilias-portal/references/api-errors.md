# API Error Recovery Guide

## Missing env vars

**Symptom:** `ilias_check_setup` returns `missing_env_vars`

**Action:**
1. Edit `agent/credentials/.env.local`
2. Fill every missing field
3. Restart MCP in your agent

## Portal login / registration failed

**Symptom:** MCP server fails to start with portal login error.

**Action:**
1. Verify `PORTAL_EMAIL` and `PORTAL_PASSWORD` in `.env.local`
2. MCP auto-registers on first run if account does not exist
3. Restart MCP after fixing credentials

## ILIAS session expired (401)

**Symptom:** `ready_for_publish: false` or publish returns ILIAS auth error.

**Action:**
1. Call `ilias_refresh_courses` once
2. Complete MFA in the browser window
3. Retry publish

## ILIAS service errors (502/503)

**Symptom:** `Unable to publish` after retries.

**Action:**
1. Check `.run/backend.log`
2. Wait 10 seconds and retry once
3. Verify ILIAS is reachable

## Markdown file not found

**Symptom:** `markdown file not found at ...`

**Action:**
1. Use path relative to kit root or absolute path
2. Default sample: `agent/samples/what-is-machine-learning.md`

## Permission errors (422)

**Symptom:** `ILIAS rejected the operation`

**Action:**
1. Verify tutor/moderator role on `ILIAS_COURSE_ID`
2. Confirm course ID is correct

## Grade target not found or ambiguous (422)

**Symptom:** `ilias_find_grade_target` cannot resolve one participant or grade form.

**Action:**
1. Use the exact participant login supplied by the instructor, never a partial name
2. Verify the assignment ID belongs to the resolved exercise
3. Verify the current ILIAS role has `edit submissions and grades` permission

## Grade target changed (422)

**Symptom:** `ilias_post_grade` reports that an expected field is stale.

**Action:**
1. Do not retry the write
2. Run `ilias_find_grade_target` again
3. Show the new current values and obtain fresh instructor confirmation

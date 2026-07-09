# API Error Recovery Guide

## Missing env vars

**Symptom:** `ilias_check_setup` returns `missing_env_vars: ["ILIAS_USERNAME", ...]`

**Action:**
1. Edit `agent/credentials/.env.local`
2. Fill every missing field:
   - `ILIAS_USERNAME`: zx account, 7 chars (e.g. `zxofp67`)
   - `ILIAS_PASSWORD`: university password
   - `ILIAS_COURSE_ID`: 7-digit course ref ID
3. Restart MCP (restart Cursor)

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
2. Complete MFA in Chromium if window opens
3. Retry publish

## ILIAS service errors (502/503)

**Symptom:** `Unable to publish` after retries.

**Action:**
1. Check `docker compose logs backend`
2. Wait 10 seconds and retry once
3. Verify ILIAS is reachable

## Markdown file not found

**Symptom:** `markdown file not found at ...`

**Action:**
1. Verify path is correct relative to repo root or use absolute path
2. Default sample: `agent/samples/what-is-machine-learning.md`

## Permission errors (422)

**Symptom:** `ILIAS rejected the operation`

**Action:**
1. Verify you have tutor/moderator role on `ILIAS_COURSE_ID`
2. Confirm course ID is correct

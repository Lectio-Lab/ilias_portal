# API Error Recovery Guide

## Missing env vars

**Symptom:** `ilias_check_setup` returns `missing_env_vars: ["PORTAL_EMAIL", ...]`

**Action:**
1. Run `scripts/provision-interactive-auth.sh` (or copy `.env.local.example`)
2. Ensure only the local portal identity is set (`PORTAL_EMAIL` / `PORTAL_PASSWORD`)
3. Leave `ILIAS_USERNAME` / `ILIAS_PASSWORD` blank
4. Restart MCP (restart Cursor)

University passwords are never stored in `.env.local` or Postgres. Enter them only
in the interactive browser MFA window opened by `ilias_refresh_courses`.

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
1. Check `docker compose logs backend` or `.run/backend.log`
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
1. Verify you have tutor/moderator role on the target course
2. Confirm course ID is correct

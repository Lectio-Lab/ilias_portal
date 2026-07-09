# MFA and ILIAS Session (Docker)

## How it works

On MCP startup, credentials from `agent/credentials/.env.local` are synced to the backend API. ILIAS session cookies are established when you call `ilias_refresh_courses`.

## When MFA is required

University Shibboleth login may require MFA. The backend launches **Chromium** via Playwright inside the Docker backend container.

### What you should do

1. Run `docker compose up -d`
2. In Cursor Agent Mode, ask to refresh courses or publish
3. If Chromium opens, complete MFA login
4. If no window appears, check `docker compose logs backend -f`

## Docker on Mac

Display forwarding from Docker can be flaky. If MFA window does not appear:

1. Check backend logs for Playwright/MFA messages
2. Retry `ilias_refresh_courses` once
3. Ensure Docker Desktop has sufficient resources

## After MFA succeeds

Session cookies are cached server-side. Subsequent publish calls should work until session expiry.

## Agent behavior

- Call `ilias_refresh_courses` at most once per failed publish attempt
- Do not loop MFA retries automatically
- Tell user clearly when manual MFA is needed

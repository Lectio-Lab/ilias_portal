# MFA and ILIAS Session (Host Browser)

## How it works

On MCP startup, credentials from `agent/credentials/.env.local` are synced to the backend API. ILIAS session cookies are established when you call `ilias_refresh_courses`.

The backend runs **on your Mac** (not inside Docker). Postgres runs in Docker.

## When MFA is required

University Shibboleth login may require MFA. The backend opens a **visible browser window** via Playwright:

- **Google Chrome** if installed (`PLAYWRIGHT_BROWSER_CHANNEL=chrome`)
- Otherwise Playwright's bundled Chromium on your desktop

### What you should do

1. Run `./start.sh` in the kit directory
2. Ask your agent to refresh courses or publish
3. When the browser opens, complete login and MFA
4. If no window appears, check `.run/backend.log`

## After MFA succeeds

Session cookies are cached server-side. Subsequent publish calls should work until session expiry.

## Agent behavior

- Call `ilias_refresh_courses` at most once per failed publish attempt
- Do not loop MFA retries automatically
- Tell user clearly when manual MFA is needed

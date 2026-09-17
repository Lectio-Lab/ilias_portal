# MFA and ILIAS Session

The local Python service runs on your Mac and is reachable only at `127.0.0.1:8010`.
It loads one generated local bearer token and opens visible Google Chrome for
university login when `ilias_refresh_courses` needs MFA.

University credentials are typed only into the browser. After successful login the
service stores only ILIAS session cookies in the owner-only local state file.

If Chrome is not installed, `./install.sh` asks before downloading Playwright
Chromium. Use `./install.sh --install-browser` only when you explicitly want that
fallback.

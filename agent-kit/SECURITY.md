# Agent Kit Security Notes

This kit is a **local macOS instructor tool**, not a multi-tenant cloud service.

## Network exposure

- The local Python service binds only to `127.0.0.1:8010`.
- Every API request requires the generated local bearer secret.

The service does not expose a bind-host option and must not be placed behind a proxy.

## Credentials and sessions

- University passwords are never stored (see issue #12).
- ILIAS session cookies (`phpsessid`, `shibsession`) are stored in
  `agent/credentials/ilias-state.json`. The directory is mode `0700`, the JSON and
  bearer secret are mode `0600`, and writes are atomic and locked. This is for one
  local instructor account; run `./uninstall.sh --purge` before decommissioning.

## Download proxy

`GET /api/ilias/download/` only accepts HTTPS URLs on `ovidius.uni-tuebingen.de`
with ILIAS asset paths. Arbitrary hosts and private-network targets are rejected.

## Packaging

- Generated MCP configs live in `mcp-config/installed/` and are created by
  `./install.sh` for the current machine. They are gitignored and excluded from
  the shipped zip.

## Platform

macOS only. Bash, a host Python venv, and Google Chrome are the supported path.
Playwright Chromium is downloaded only after explicit consent.

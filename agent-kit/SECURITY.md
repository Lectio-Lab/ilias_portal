# Agent Kit Security Notes

This kit is a **local macOS instructor tool**, not a multi-tenant cloud service.

## Network exposure

- Django binds to `127.0.0.1` by default (`BACKEND_BIND_HOST`).
- PostgreSQL publishes on `127.0.0.1:5434` only.
- `ALLOWED_HOSTS` defaults to `localhost,127.0.0.1`.
- CORS defaults to local frontend origins only.

Do not rebind the API or database to `0.0.0.0` on shared or untrusted networks.

## Credentials and sessions

- University passwords are never stored (see issue #12).
- ILIAS session cookies (`phpsessid`, `shibsession`) are stored as plain text in the
  local Postgres volume under `docker-data/`. This is acceptable for a single-user
  laptop install but not for shared machines. Run `./uninstall.sh --purge` before
  decommissioning a machine.

## Download proxy

`GET /api/ilias/download/` only accepts HTTPS URLs on `ovidius.uni-tuebingen.de`
with ILIAS asset paths. Arbitrary hosts and private-network targets are rejected.

## Packaging

- Generated MCP configs live in `mcp-config/installed/` and are created by
  `./install.sh` for the current machine. They are gitignored and excluded from
  the shipped zip.

## Platform

macOS only. Bash, Docker Desktop, host Python venv, and Playwright Chrome paths
are not supported natively on Windows in this release.

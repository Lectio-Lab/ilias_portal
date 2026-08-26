#!/usr/bin/env bash
# Provision a unique local Portal API account without storing university credentials.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
CREDS_FILE="$KIT_HOME/agent/credentials/.env.local"

umask 077
portal_id="$(uuidgen | tr '[:upper:]' '[:lower:]' | tr -d '-')"
portal_secret="$(openssl rand -hex 32)"
temp_file="$(mktemp "$KIT_HOME/agent/credentials/.env.local.XXXXXX")"

printf '%s\n' \
  '# Local API identity generated for this installation.' \
  '# University credentials are intentionally blank; enter them only in the browser.' \
  "PORTAL_EMAIL=ilias-agent-$portal_id@localhost.invalid" \
  "PORTAL_PASSWORD=$portal_secret" \
  'ILIAS_USERNAME=' \
  'ILIAS_PASSWORD=' \
  'ILIAS_COURSE_ID=' \
  'ILIAS_COURSE_IDS=' \
  'API_BASE_URL=http://localhost:8010' >"$temp_file"

mv "$temp_file" "$CREDS_FILE"
chmod 600 "$CREDS_FILE"
echo "Provisioned a unique local API identity; no university credentials were stored."

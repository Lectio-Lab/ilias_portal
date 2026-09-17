#!/usr/bin/env bash
# Provision one bearer secret for the localhost-only service; never university credentials.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
CREDS_FILE="$KIT_HOME/agent/credentials/.env.local"

umask 077
mkdir -p "$KIT_HOME/agent/credentials"
chmod 700 "$KIT_HOME/agent/credentials"
portal_secret="$(openssl rand -base64 48 | tr -d '\n')"
temp_file="$(mktemp "$KIT_HOME/agent/credentials/.env.local.XXXXXX")"

printf '%s\n' \
  '# Local bearer secret generated for this installation.' \
  '# University credentials are intentionally blank; enter them only in the browser.' \
  "PORTAL_LOCAL_TOKEN=$portal_secret" \
  'ILIAS_COURSE_ID=' \
  'ILIAS_COURSE_IDS=' \
  'API_BASE_URL=http://127.0.0.1:8010' >"$temp_file"

mv "$temp_file" "$CREDS_FILE"
chmod 600 "$CREDS_FILE"
echo "Provisioned a local bearer secret; no university credentials were stored."

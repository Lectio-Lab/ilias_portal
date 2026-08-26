#!/usr/bin/env bash
# Assert build-zip staging rules for issue #13 (no venv / node_modules in kit).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD="$SCRIPT_DIR/build-zip.sh"
STAGE="$REPO_ROOT/dist/stage/ilias-portal-agent-kit"
ZIP_KIT="$REPO_ROOT/dist/ilias-portal-agent-kit-1.0.0-macos.zip"

echo "Running lean zip packaging checks..."
"$BUILD" 1.0.0

if [[ ! -f "$ZIP_KIT" ]]; then
  echo "FAIL: expected $ZIP_KIT" >&2
  exit 1
fi

leak="$(
  find "$STAGE" \( \
    -path '*/venv' -o -path '*/venv/*' -o \
    -path '*/.venv' -o -path '*/.venv/*' -o \
    -path '*/node_modules' -o -path '*/node_modules/*' \
  \) -print 2>/dev/null | head -5 || true
)"
if [[ -n "$leak" ]]; then
  echo "FAIL: stage still contains venv/node_modules:" >&2
  echo "$leak" >&2
  exit 1
fi

zip_leak="$(
  unzip -Z1 "$ZIP_KIT" | grep -E '(^|/)(\.?venv|node_modules)(/|$)' || true
)"
if [[ -n "$zip_leak" ]]; then
  echo "FAIL: zip still lists venv/node_modules:" >&2
  echo "$zip_leak" | head -20 >&2
  exit 1
fi

# Catch regressions where the archive balloons again from a local Python env.
size_bytes="$(wc -c <"$ZIP_KIT" | tr -d ' ')"
max_bytes=$((15 * 1024 * 1024)) # 15 MiB ceiling; source kit should stay well under this
if (( size_bytes > max_bytes )); then
  echo "FAIL: kit zip is ${size_bytes} bytes (max ${max_bytes}). venv likely leaked back in." >&2
  ls -lh "$ZIP_KIT" >&2
  exit 1
fi

echo "PASS: lean kit zip at $(ls -lh "$ZIP_KIT" | awk '{print $5}') with no venv/node_modules."

#!/usr/bin/env bash
# Packaging regression test for issue #13 (lean kit zip, enforced by build-zip.sh).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD="$SCRIPT_DIR/build-zip.sh"
VERSION="$(read_kit_version "$REPO_ROOT")"
ZIP_KIT="$REPO_ROOT/dist/ilias-portal-agent-kit-${VERSION}-macos.zip"

echo "Running lean zip packaging checks (version $VERSION)..."
"$BUILD"

if [[ ! -f "$ZIP_KIT" ]]; then
  echo "FAIL: expected $ZIP_KIT" >&2
  exit 1
fi

size_bytes="$(wc -c <"$ZIP_KIT" | tr -d ' ')"
echo "PASS: lean kit zip at $(ls -lh "$ZIP_KIT" | awk '{print $5}') (${size_bytes} bytes)."

#!/usr/bin/env bash
# Packaging regression test for issue #13 (lean kit zip, enforced by build-zip.sh).
#
# Uses a detached git worktree so sentinel venv/node_modules directories exercise
# the rsync exclusion rules without touching the developer's local environments.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD="$SCRIPT_DIR/build-zip.sh"
SENTINEL_NAME="SENTINEL_SHOULD_NOT_SHIP"

WORKTREE_ROOT=""
cleanup() {
  if [[ -n "$WORKTREE_ROOT" && -d "$WORKTREE_ROOT" ]]; then
    git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_ROOT" 2>/dev/null || rm -rf "$WORKTREE_ROOT"
  fi
}
trap cleanup EXIT

echo "Creating isolated worktree for packaging regression test..."
WORKTREE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ilias-kit-zip-test.XXXXXX")"
git -C "$REPO_ROOT" worktree add --detach "$WORKTREE_ROOT" HEAD >/dev/null

VERSION="$(read_kit_version "$WORKTREE_ROOT")"
ZIP_KIT="$WORKTREE_ROOT/dist/ilias-portal-agent-kit-${VERSION}-macos.zip"

echo "Planting sentinel files in excluded directories (version $VERSION)..."
mkdir -p \
  "$WORKTREE_ROOT/backend/.venv" \
  "$WORKTREE_ROOT/backend/venv" \
  "$WORKTREE_ROOT/agent/mcp-server/node_modules"
touch \
  "$WORKTREE_ROOT/backend/.venv/$SENTINEL_NAME" \
  "$WORKTREE_ROOT/backend/venv/$SENTINEL_NAME" \
  "$WORKTREE_ROOT/agent/mcp-server/node_modules/$SENTINEL_NAME"

echo "Running build in worktree..."
"$WORKTREE_ROOT/agent-kit/scripts/build-zip.sh"

if [[ ! -f "$ZIP_KIT" ]]; then
  echo "FAIL: expected $ZIP_KIT" >&2
  exit 1
fi

if unzip -Z1 "$ZIP_KIT" | grep -q "$SENTINEL_NAME"; then
  echo "FAIL: excluded environment files leaked into the archive:" >&2
  unzip -Z1 "$ZIP_KIT" | grep "$SENTINEL_NAME" >&2
  exit 1
fi

zip_leak="$(
  unzip -Z1 "$ZIP_KIT" | grep -E '(^|/)(\.?venv|node_modules)(/|$)' || true
)"
if [[ -n "$zip_leak" ]]; then
  echo "FAIL: zip still lists venv or node_modules paths:" >&2
  echo "$zip_leak" | head -20 >&2
  exit 1
fi

size_bytes="$(wc -c <"$ZIP_KIT" | tr -d ' ')"
max_bytes=$((15 * 1024 * 1024))
if (( size_bytes > max_bytes )); then
  echo "FAIL: kit zip is ${size_bytes} bytes (max ${max_bytes})." >&2
  exit 1
fi

echo "PASS: lean kit zip at $(ls -lh "$ZIP_KIT" | awk '{print $5}') (${size_bytes} bytes); sentinels excluded."

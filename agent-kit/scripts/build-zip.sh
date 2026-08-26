#!/usr/bin/env bash
# Build shippable zip archives for macOS distribution.
# Ships source + lockfiles + prebuilt MCP dist — never local venvs or node_modules.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="${1:-1.0.0}"
STAGE="$REPO_ROOT/dist/stage/ilias-portal-agent-kit"
DIST="$REPO_ROOT/dist"
KIT_SRC="$REPO_ROOT/agent-kit"

echo "Building ILIAS Portal Agent Kit v$VERSION"

# Build MCP server
echo "Building MCP server..."
(cd "$REPO_ROOT/agent/mcp-server" && npm ci && npm run build)

rm -rf "$STAGE"
mkdir -p "$STAGE"

# Kit scaffolding (install, compose, scripts, skill, mcp-config)
cp "$KIT_SRC/README.md" "$KIT_SRC/INSTALL.md" "$KIT_SRC/QUICKSTART.md" "$KIT_SRC/install.sh" \
  "$KIT_SRC/start.sh" "$KIT_SRC/stop.sh" "$KIT_SRC/docker-compose.yml" \
  "$KIT_SRC/.env.example" "$STAGE/"
mkdir -p "$STAGE/scripts"
cp "$KIT_SRC/scripts/"*.sh "$STAGE/scripts/"
chmod +x "$STAGE"/install.sh "$STAGE"/start.sh "$STAGE"/stop.sh "$STAGE"/scripts/*.sh

cp -R "$KIT_SRC/skill" "$STAGE/"
cp -R "$KIT_SRC/mcp-config" "$STAGE/"
chmod +x "$STAGE/skill/ilias-portal/scripts/health-check.sh"

# Backend source only (recipients create .venv during ./install.sh)
mkdir -p "$STAGE/backend"
rsync -a \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude '.mypy_cache/' \
  --exclude '*.egg-info/' \
  --exclude '.env' \
  --exclude '.env.local' \
  --exclude '*.log' \
  "$REPO_ROOT/backend/" "$STAGE/backend/"

# Agent source + prebuilt mcp-server/dist (recipients run npm ci during install)
mkdir -p "$STAGE/agent"
rsync -a \
  --exclude 'node_modules/' \
  --exclude '.env' \
  --exclude 'credentials/.env.local' \
  --exclude 'credentials/*.local' \
  --exclude 'tests/eval/results/' \
  "$REPO_ROOT/agent/" "$STAGE/agent/"
chmod +x "$STAGE/agent/scripts/start-mcp.sh"

# Fail closed if local environments leaked into the stage (#13).
leak="$(
  find "$STAGE" \( \
    -path '*/venv' -o -path '*/venv/*' -o \
    -path '*/.venv' -o -path '*/.venv/*' -o \
    -path '*/node_modules' -o -path '*/node_modules/*' \
  \) -print 2>/dev/null | head -5 || true
)"
if [[ -n "$leak" ]]; then
  echo "ERROR: staged kit contains venv or node_modules (must not ship):" >&2
  echo "$leak" >&2
  exit 1
fi

if [[ ! -f "$STAGE/agent/mcp-server/package-lock.json" ]]; then
  echo "ERROR: missing agent/mcp-server/package-lock.json in stage" >&2
  exit 1
fi
if [[ ! -f "$STAGE/backend/requirements.txt" ]]; then
  echo "ERROR: missing backend/requirements.txt in stage" >&2
  exit 1
fi
if [[ ! -f "$STAGE/agent/mcp-server/dist/cli.js" ]]; then
  echo "ERROR: missing prebuilt agent/mcp-server/dist/cli.js in stage" >&2
  exit 1
fi

echo "Staged kit size (no venv/node_modules):"
du -sh "$STAGE"

mkdir -p "$DIST"
ZIP_KIT="$DIST/ilias-portal-agent-kit-${VERSION}-macos.zip"
ZIP_SKILL="$DIST/ilias-portal-skill.zip"
ZIP_TEACHING_SKILL="$DIST/find-teaching-content-skill.zip"
ZIP_HERO_SKILL="$DIST/hero-content-maker-skill.zip"

(
  cd "$(dirname "$STAGE")"
  rm -f "$ZIP_KIT"
  zip -rq "$ZIP_KIT" "$(basename "$STAGE")"
)

(
  cd "$STAGE/skill"
  rm -f "$ZIP_SKILL"
  zip -rq "$ZIP_SKILL" ilias-portal

  rm -f "$ZIP_TEACHING_SKILL"
  zip -rq "$ZIP_TEACHING_SKILL" find-teaching-content

  rm -f "$ZIP_HERO_SKILL"
  zip -rq "$ZIP_HERO_SKILL" hero-content-maker
)

# Verify the kit zip itself (not just the stage).
zip_leak="$(
  unzip -Z1 "$ZIP_KIT" | grep -E '(^|/)(\.?venv|node_modules)(/|$)' || true
)"
if [[ -n "$zip_leak" ]]; then
  echo "ERROR: built zip still lists venv or node_modules entries:" >&2
  echo "$zip_leak" | head -20 >&2
  exit 1
fi

echo ""
echo "Created:"
echo "  $ZIP_KIT"
echo "  $ZIP_SKILL"
echo "  $ZIP_TEACHING_SKILL"
echo "  $ZIP_HERO_SKILL"
ls -lh "$ZIP_KIT" "$ZIP_SKILL" "$ZIP_TEACHING_SKILL" "$ZIP_HERO_SKILL"

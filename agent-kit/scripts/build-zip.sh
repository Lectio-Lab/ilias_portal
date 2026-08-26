#!/usr/bin/env bash
# Build shippable zip archives for macOS distribution.
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

# Backend (exclude venvs, caches, secrets)
mkdir -p "$STAGE/backend"
rsync -a --exclude '.venv' --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
  --exclude '.env' --exclude '.env.local' --exclude '*.log' \
  "$REPO_ROOT/backend/" "$STAGE/backend/"

# Agent (exclude node_modules; include dist)
mkdir -p "$STAGE/agent"
rsync -a --exclude 'node_modules' --exclude '.env' \
  --exclude 'credentials/.env.local' --exclude 'credentials/*.local' \
  "$REPO_ROOT/agent/" "$STAGE/agent/"
chmod +x "$STAGE/agent/scripts/start-mcp.sh"

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

echo ""
echo "Created:"
echo "  $ZIP_KIT"
echo "  $ZIP_SKILL"
echo "  $ZIP_TEACHING_SKILL"
echo "  $ZIP_HERO_SKILL"
ls -lh "$ZIP_KIT" "$ZIP_SKILL" "$ZIP_TEACHING_SKILL" "$ZIP_HERO_SKILL"

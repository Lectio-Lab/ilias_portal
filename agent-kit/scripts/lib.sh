#!/usr/bin/env bash
# Shared helpers for agent kit scripts.
set -euo pipefail

resolve_kit_home() {
  if [[ -n "${ILIAS_PORTAL_HOME:-}" ]]; then
    echo "$ILIAS_PORTAL_HOME"
    return
  fi
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
  if [[ "$(basename "$script_dir")" == "scripts" ]]; then
    cd "$script_dir/.." && pwd
    return
  fi
  pwd
}

resolve_backend_dir() {
  local kit
  kit="$(resolve_kit_home)"
  if [[ -d "$kit/backend" ]]; then
    echo "$kit/backend"
  elif [[ -d "$kit/../backend" ]]; then
    echo "$(cd "$kit/../backend" && pwd)"
  else
    echo "$kit/backend"
  fi
}

resolve_agent_dir() {
  local kit
  kit="$(resolve_kit_home)"
  if [[ -d "$kit/agent" ]]; then
    echo "$kit/agent"
  elif [[ -d "$kit/../agent" ]]; then
    echo "$(cd "$kit/../agent" && pwd)"
  else
    echo "$kit/agent"
  fi
}

require_cmd() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "Missing required command: $name" >&2
    return 1
  fi
}

version_ge() {
  # usage: version_ge 22.12.0 v22.12.1
  local minimum="${1#v}"
  local current="${2#v}"
  local min_major min_minor min_patch cur_major cur_minor cur_patch
  IFS=. read -r min_major min_minor min_patch <<<"$minimum"
  IFS=. read -r cur_major cur_minor cur_patch <<<"$current"
  min_minor="${min_minor:-0}"
  min_patch="${min_patch:-0}"
  cur_minor="${cur_minor:-0}"
  cur_patch="${cur_patch%%[^0-9]*}"
  cur_patch="${cur_patch:-0}"
  (( cur_major > min_major )) ||
    (( cur_major == min_major && cur_minor > min_minor )) ||
    (( cur_major == min_major && cur_minor == min_minor && cur_patch >= min_patch ))
}

check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is not installed."
    echo "Install Docker Desktop: https://docs.docker.com/desktop/install/mac-install/"
    if command -v brew >/dev/null 2>&1; then
      echo "Or run: brew install --cask docker"
    fi
    return 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "Docker is installed but not running. Start Docker Desktop and retry."
    return 1
  fi
}

check_node() {
  if ! command -v node >/dev/null 2>&1; then
    echo "Node.js is not installed (need 22.12+)."
    if command -v brew >/dev/null 2>&1; then
      echo "Run: brew install node@22"
    fi
    return 1
  fi
  local ver
  ver="$(node -v)"
  if ! version_ge 22.12.0 "$ver"; then
    echo "Node.js $ver is too old (need 22.12+)."
    return 1
  fi
}

check_python() {
  local py=""
  if command -v python3.12 >/dev/null 2>&1; then
    py="python3.12"
  elif command -v python3 >/dev/null 2>&1; then
    py="python3"
  else
    echo "Python 3.12+ is not installed."
    if command -v brew >/dev/null 2>&1; then
      echo "Run: brew install python@3.12"
    fi
    return 1
  fi
  local minor
  minor="$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  local major minor_only
  major="$(echo "$minor" | cut -d. -f1)"
  minor_only="$(echo "$minor" | cut -d. -f2)"
  if [[ "$major" -lt 3 ]] || [[ "$major" -eq 3 && "$minor_only" -lt 12 ]]; then
    echo "Python $minor is too old (need 3.12+)."
    return 1
  fi
  echo "$py"
}

load_dotenv() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    return 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "$file"
  set +a
}

read_kit_version() {
  # Agent-kit release version tracks agent/mcp-server/package.json (MCP semver).
  local repo_root="$1"
  node -p "require('${repo_root}/agent/mcp-server/package.json').version"
}

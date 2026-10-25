#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
game_user_root="${GAME_USER_DIR:-$PWD/.local}"
export XDG_DATA_HOME="$game_user_root/share"
export XDG_CONFIG_HOME="$game_user_root/config"
export XDG_CACHE_HOME="$game_user_root/cache"
mkdir -p "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
backend_pid=$!
trap 'kill "$backend_pid" 2>/dev/null || true' EXIT
for attempt in {1..50}; do
  if curl --fail --silent http://127.0.0.1:8000/health >/dev/null; then
    godot --path client "$@"
    exit $?
  fi
  kill -0 "$backend_pid"
  sleep 0.2
done
printf 'Backend startup timed out\n' >&2
exit 1

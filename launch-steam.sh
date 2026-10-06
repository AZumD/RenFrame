#!/usr/bin/env bash
# Steam-friendly wrapper: resolves game dir from this script, passes basedir explicitly.
set -euo pipefail
GAME_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$GAME_DIR"
exec "$GAME_DIR/summertimesaga.sh" "$GAME_DIR" "$@"

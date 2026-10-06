#!/usr/bin/env bash
# Register this Ren'Py Linux ARM build as a non-Steam game.
# Run on the ARM device AFTER unpacking (Steam must be running).
set -euo pipefail

GAME_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$GAME_DIR"

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# Prefer launch-steam.sh; fall back to the Ren'Py .sh launcher.
LAUNCH=""
if [[ -x "$GAME_DIR/launch-steam.sh" ]]; then
  LAUNCH="$GAME_DIR/launch-steam.sh"
else
  for f in "$GAME_DIR"/*.sh; do
    [[ -e "$f" ]] || continue
    base=$(basename "$f")
    case "$base" in
      make-linux-arm.sh|add-to-steam.sh|launch-steam.sh) continue ;;
    esac
    if grep -q 'RENPY_PLATFORM' "$f" 2>/dev/null; then
      LAUNCH="$f"
      break
    fi
  done
fi
[[ -n "$LAUNCH" ]] || die "No launch-steam.sh or Ren'Py .sh launcher found in $GAME_DIR"
LAUNCH=$(readlink -f "$LAUNCH" 2>/dev/null || realpath "$LAUNCH" 2>/dev/null || echo "$LAUNCH")

GAME_NAME=$(basename "$LAUNCH" .sh)
[[ "$GAME_NAME" == "launch-steam" ]] && GAME_NAME=$(basename "$GAME_DIR")

DESKTOP="$GAME_DIR/${GAME_NAME}.desktop"
# If name still weird, pick any game .desktop beside us or create one.
if [[ ! -f "$DESKTOP" ]]; then
  for d in "$GAME_DIR"/*.desktop; do
    [[ -e "$d" ]] || continue
    DESKTOP="$d"
    break
  done
fi

# Refresh .desktop with absolute paths for THIS unpack location.
NAME="$GAME_NAME"
if [[ -f "$DESKTOP" ]]; then
  # Keep Name= from existing file when present
  old_name=$(grep -E '^Name=' "$DESKTOP" | head -1 | cut -d= -f2- || true)
  [[ -n "$old_name" ]] && NAME="$old_name"
fi
cat > "$DESKTOP" <<EOD
[Desktop Entry]
Name=$NAME
Comment=$NAME (native Linux ARM Ren'Py)
Exec=$LAUNCH
Path=$GAME_DIR
Icon=applications-games
Terminal=false
Type=Application
Categories=Game;
StartupNotify=false
EOD
chmod +x "$DESKTOP" 2>/dev/null || true
DESKTOP=$(readlink -f "$DESKTOP" 2>/dev/null || realpath "$DESKTOP" 2>/dev/null || echo "$DESKTOP")
log "Desktop entry: $DESKTOP"
log "Launch target: $LAUNCH"

steam_is_running() {
  pgrep -x steam >/dev/null 2>&1 \
    || pgrep -f '[/]steamrt.*/steam' >/dev/null 2>&1 \
    || pgrep -f '[.]local/share/Steam/.*/steam$' >/dev/null 2>&1
}

if command -v steamos-add-to-steam >/dev/null 2>&1; then
  log "Adding via steamos-add-to-steam…"
  steamos-add-to-steam "$DESKTOP"
  log "Done. Check your Steam library for \"$NAME\"."
  log "Properties → Compatibility: Steam Linux Runtime / native (not Proton)."
  exit 0
fi

command -v steam >/dev/null 2>&1 || die "Neither steamos-add-to-steam nor steam found.
Add manually: Steam → Add a Non-Steam Game → $DESKTOP"

steam_is_running || die "Steam does not appear to be running. Start Steam, then re-run:
  $0"

py=$(command -v python3 || command -v python || true)
if [[ -n "$py" ]]; then
  encoded=$("$py" -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$DESKTOP")
else
  encoded=${DESKTOP// /%20}
fi

touch /tmp/addnonsteamgamefile 2>/dev/null || true
log "Adding via steam://addnonsteamgame/…"
steam "steam://addnonsteamgame/${encoded}"
log "Done. Check your Steam library for \"$NAME\"."
log "Properties → Compatibility: Steam Linux Runtime / native (not Proton)."

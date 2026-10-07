#!/usr/bin/env bash
# make-linux-arm.sh — graft official Ren'Py Linux aarch64 runtime into a PC build.
#
# Put this next to the game's .sh launcher (e.g. MyGame.sh), then:
#   chmod +x make-linux-arm.sh && ./make-linux-arm.sh
#
# What it does:
#   1. Detects Ren'Py version from renpy/vc_version.py or .pyc (or --version / RENPY_VERSION)
#   2. Downloads renpy-<ver>-sdkarm.tar.bz2 from renpy.org
#   3. Installs lib/py3-linux-aarch64/ (or py2-… if that is what the game uses)
#   4. Names the launcher binary after the game .sh
#   5. Patches the .sh so aarch64/arm64 map to linux-aarch64
#   6. Writes launch-steam.sh + add-to-steam.sh (+ .desktop) into the game folder
#   7. Packs a portable archive (.zip or .7z) to copy to an ARM device (e.g. Frame)
#
# On the ARM device: unpack, then run ./add-to-steam.sh (Steam must be running).
#
# Requirements: bash, curl, tar; python3 recommended; zip or 7z for the archive.
set -euo pipefail

SCRIPT_PATH=$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")
GAME_DIR=$(cd "$(dirname "$SCRIPT_PATH")" && pwd)
CACHE_DIR="${RENPY_ARM_CACHE:-$GAME_DIR/.renpy-arm-cache}"
FORCE=0
SKIP_STEAM_SCRIPTS=0
SKIP_ARCHIVE=0
FULL_ARCHIVE=0
VERSION_OVERRIDE="${RENPY_VERSION:-}"
KEEP_CACHE=1
ARCHIVE_PATH=""

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --version X.Y.Z     Ren'Py version (default: auto-detect from renpy/)
  --force             Re-download / re-install even if aarch64 libs exist
  --no-steam-scripts  Do not write launch-steam.sh / add-to-steam.sh / .desktop
  --no-archive        Do not create a .zip/.7z package
  --full-archive      Include Windows/x86_64 libs and caches in the archive
  --cache-dir DIR     Download cache (default: $CACHE_DIR)
  --clean-cache       Delete downloaded SDK after install
  -h, --help          Show this help
EOF
}

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION_OVERRIDE=${2:?}; shift 2 ;;
    --force) FORCE=1; shift ;;
    --no-steam-scripts) SKIP_STEAM_SCRIPTS=1; shift ;;
    --no-archive) SKIP_ARCHIVE=1; shift ;;
    --full-archive) FULL_ARCHIVE=1; shift ;;
    --cache-dir) CACHE_DIR=${2:?}; shift 2 ;;
    --clean-cache) KEEP_CACHE=0; shift ;;
    # Back-compat aliases (ignored / remapped)
    --no-desktop|--no-steam-wrap|--no-add-to-steam|--add-to-steam)
      warn "Option $1 is obsolete; Steam registration is now ./add-to-steam.sh on the device"
      shift
      ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
done

need_cmd curl
need_cmd tar
# bzip2 is preferred; Python's tarfile can decompress .bz2 if bzip2 is missing
HAVE_BZIP2=0
if command -v bzip2 >/dev/null 2>&1 || command -v lbzip2 >/dev/null 2>&1; then
  HAVE_BZIP2=1
elif command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
  warn "bzip2 not found — will use Python tarfile for .bz2 extraction"
else
  die "Need bzip2 or python3 to extract .tar.bz2"
fi

# --- locate game launcher ---------------------------------------------------
find_launcher_sh() {
  local f base
  # Prefer a .sh that is not this installer / helpers
  for f in "$GAME_DIR"/*.sh; do
    [[ -e "$f" ]] || continue
    base=$(basename "$f")
    case "$base" in
      make-linux-arm.sh|launch-steam.sh|add-to-steam.sh|diagnose-frame.sh) continue ;;
    esac
    # Ren'Py launchers usually contain RENPY_PLATFORM
    if grep -q 'RENPY_PLATFORM' "$f" 2>/dev/null; then
      echo "$f"
      return 0
    fi
  done
  # Fallback: any non-helper .sh
  for f in "$GAME_DIR"/*.sh; do
    [[ -e "$f" ]] || continue
    base=$(basename "$f")
    case "$base" in
      make-linux-arm.sh|launch-steam.sh|add-to-steam.sh) continue ;;
    esac
    echo "$f"
    return 0
  done
  return 1
}

LAUNCHER_SH=$(find_launcher_sh) || die "No Ren'Py .sh launcher found in $GAME_DIR"
GAME_NAME=$(basename "$LAUNCHER_SH" .sh)
log "Game dir:     $GAME_DIR"
log "Launcher:     $LAUNCHER_SH"
log "Game name:    $GAME_NAME"

[[ -d "$GAME_DIR/renpy" ]] || die "No renpy/ directory — is this a Ren'Py game?"
[[ -d "$GAME_DIR/lib" ]] || die "No lib/ directory — is this a Ren'Py game?"

# Detect py2 vs py3 from existing platform libs
PYTHON_TAG=py3
if compgen -G "$GAME_DIR/lib/py2-*" >/dev/null; then
  if ! compgen -G "$GAME_DIR/lib/py3-*" >/dev/null; then
    PYTHON_TAG=py2
  fi
fi
log "Python tag:   $PYTHON_TAG"

DEST="$GAME_DIR/lib/${PYTHON_TAG}-linux-aarch64"
if [[ -d "$DEST" && "$FORCE" -eq 0 ]]; then
  if [[ -f "$DEST/librenpython.so" || -f "$DEST/librenpython.dylib" ]]; then
    log "Already installed: $DEST (use --force to redo)"
    ALREADY=1
  else
    ALREADY=0
  fi
else
  ALREADY=0
fi

# --- version detection ------------------------------------------------------
detect_version() {
  if [[ -n "$VERSION_OVERRIDE" ]]; then
    echo "$VERSION_OVERRIDE"
    return 0
  fi

  local py out
  py=$(command -v python3 || command -v python || true)
  if [[ -n "$py" ]]; then
    if out=$(GAME_DIR="$GAME_DIR" "$py" - <<'PY'
import os, pathlib, marshal, re, sys

root = pathlib.Path(os.environ["GAME_DIR"])
ver_re = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\.\d+)?$")

def normalize(s: str):
    m = ver_re.match(s.strip().strip("'\""))
    if m:
        return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    return None

def from_py_source(path: pathlib.Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    # vc_version.py: version = '8.3.7.25031702'
    for pat in (
        r"""(?m)^version\s*=\s*['\"]([^'\"]+)['\"]""",
        r"""(?m)^vc_version\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)""",
    ):
        m = re.search(pat, text)
        if not m:
            continue
        if m.lastindex == 1:
            n = normalize(m.group(1))
            if n:
                return n
        else:
            return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    # versions.py sometimes embeds Version("8.3.7", ...)
    for m in re.finditer(r"""['\"](\d+\.\d+\.\d+(?:\.\d+)?)['\"]""", text):
        n = normalize(m.group(1))
        if n:
            return n
    return None

def load_code(path: pathlib.Path):
    data = path.read_bytes()
    for skip in (16, 12, 8):
        try:
            return marshal.loads(data[skip:])
        except Exception:
            continue
    return None

def from_pyc(path: pathlib.Path):
    code = load_code(path)
    if code is None:
        return None
    found = []
    def walk(c):
        for x in c.co_consts:
            if isinstance(x, str):
                n = normalize(x)
                if n:
                    found.append(n)
            elif hasattr(x, "co_consts"):
                walk(x)
    walk(code)
    return found[0] if found else None

# Prefer source (sdk-style / unpacked games), then bytecode.
candidates_py = [
    root / "renpy" / "vc_version.py",
    root / "renpy" / "versions.py",
]
for path in candidates_py:
    if path.is_file():
        n = from_py_source(path)
        if n:
            print(n)
            sys.exit(0)

candidates_pyc = [
    root / "renpy" / "vc_version.pyc",
    root / "renpy" / "versions.pyc",
]
# Also __pycache__/vc_version.cpython-XX.pyc
pycache = root / "renpy" / "__pycache__"
if pycache.is_dir():
    candidates_pyc.extend(sorted(pycache.glob("vc_version.cpython-*.pyc")))
    candidates_pyc.extend(sorted(pycache.glob("versions.cpython-*.pyc")))

for path in candidates_pyc:
    if path.is_file():
        n = from_pyc(path)
        if n:
            print(n)
            sys.exit(0)

sys.exit(1)
PY
); then
      echo "$out"
      return 0
    fi
  fi

  # Grep fallback on vc_version.py
  if [[ -f "$GAME_DIR/renpy/vc_version.py" ]]; then
    local v
    v=$(grep -E "^version[[:space:]]*=" "$GAME_DIR/renpy/vc_version.py" | head -1 \
      | grep -oE '[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || true)
    if [[ -n "$v" ]]; then
      echo "$v" | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+'
      return 0
    fi
  fi

  # strings fallback on bytecode
  if command -v strings >/dev/null 2>&1; then
    local f v
    for f in \
      "$GAME_DIR/renpy/vc_version.pyc" \
      "$GAME_DIR/renpy/versions.pyc" \
      "$GAME_DIR/renpy/__pycache__"/vc_version.cpython-*.pyc
    do
      [[ -f "$f" ]] || continue
      v=$(strings "$f" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?$' | head -1 || true)
      if [[ -n "$v" ]]; then
        echo "$v" | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+'
        return 0
      fi
    done
  fi

  return 1
}

VERSION=$(detect_version) || die "Could not detect Ren'Py version. Pass --version X.Y.Z"
# Normalize 8.5.3.26051504 → 8.5.3
VERSION=$(echo "$VERSION" | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+')
log "Ren'Py ver:   $VERSION"

SDK_NAME="renpy-${VERSION}-sdkarm.tar.bz2"
SDK_URL="https://www.renpy.org/dl/${VERSION}/${SDK_NAME}"
SDK_FILE="$CACHE_DIR/$SDK_NAME"
CHECKSUMS_URL="https://www.renpy.org/dl/${VERSION}/checksums.txt"

mkdir -p "$CACHE_DIR"

download_sdk() {
  if [[ -f "$SDK_FILE" && "$FORCE" -eq 0 ]]; then
    log "Using cached SDK: $SDK_FILE"
    return 0
  fi
  log "Downloading $SDK_URL"
  curl -fL --progress-bar -o "$SDK_FILE.partial" "$SDK_URL" \
    || die "Download failed. Check version $VERSION exists at https://www.renpy.org/dl/${VERSION}/"
  mv -f "$SDK_FILE.partial" "$SDK_FILE"
}

verify_checksum() {
  local py sums expected got
  py=$(command -v python3 || command -v python || true)
  if [[ -z "$py" ]]; then
    warn "No python3 — skipping checksum verification"
    return 0
  fi
  log "Fetching checksums.txt"
  sums=$(curl -fsSL "$CHECKSUMS_URL" || true)
  if [[ -z "$sums" ]]; then
    warn "No checksums.txt for $VERSION — skipping verify"
    return 0
  fi
  expected=$(
    GAME_SDK="$SDK_NAME" CHECKSUMS_TEXT="$sums" "$py" - <<'PY'
import os, re
name = os.environ["GAME_SDK"]
text = os.environ["CHECKSUMS_TEXT"]
# Prefer the # sha256 section
section = None
sha = None
for line in text.splitlines():
    s = line.strip()
    if s.lower().startswith("# sha256"):
        section = "sha256"
        continue
    if s.startswith("#"):
        section = s.lower().lstrip("#").strip() or section
        continue
    if name not in s:
        continue
    m = re.match(r"^([a-fA-F0-9]+)\s+\S+", s)
    if not m:
        continue
    digest = m.group(1).lower()
    if section == "sha256" and len(digest) == 64:
        sha = digest
        break
    if sha is None and len(digest) == 64:
        sha = digest
print(sha or "")
PY
  )
  if [[ -z "$expected" ]]; then
    warn "Could not parse SHA256 for $SDK_NAME — skipping verify"
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    got=$(sha256sum "$SDK_FILE" | awk '{print $1}')
  elif command -v shasum >/dev/null 2>&1; then
    got=$(shasum -a 256 "$SDK_FILE" | awk '{print $1}')
  else
    got=$(SDK_FILE="$SDK_FILE" "$py" - <<'PY'
import hashlib, os, pathlib
print(hashlib.sha256(pathlib.Path(os.environ["SDK_FILE"]).read_bytes()).hexdigest())
PY
)
  fi
  if [[ "$got" != "$expected" ]]; then
    die "SHA256 mismatch for $SDK_NAME
  expected: $expected
  got:      $got"
  fi
  log "Checksum OK ($got)"
}

extract_aarch64() {
  local tmp src py
  tmp=$(mktemp -d "$CACHE_DIR/extract.XXXXXX")

  log "Extracting ${PYTHON_TAG}-linux-aarch64 from SDK…"

  if [[ "$HAVE_BZIP2" -eq 1 ]]; then
    if ! tar -tjf "$SDK_FILE" | grep -q "/lib/${PYTHON_TAG}-linux-aarch64"; then
      rm -rf "$tmp"
      die "SDK does not contain lib/${PYTHON_TAG}-linux-aarch64 — ARM runtime missing for this version?"
    fi
    tar -tjf "$SDK_FILE" | grep "/lib/${PYTHON_TAG}-linux-aarch64" > "$tmp/list.txt"
    tar -xjf "$SDK_FILE" -C "$tmp" -T "$tmp/list.txt"
  else
    py=$(command -v python3 || command -v python)
    SDK_FILE="$SDK_FILE" DEST_TMP="$tmp" PYTHON_TAG="$PYTHON_TAG" "$py" - <<'PY'
import os, tarfile, sys
sdk = os.environ["SDK_FILE"]
tmp = os.environ["DEST_TMP"]
tag = os.environ["PYTHON_TAG"]
needle = f"/lib/{tag}-linux-aarch64"
with tarfile.open(sdk, "r:bz2") as tf:
    members = [m for m in tf.getmembers() if needle in m.name]
    if not members:
        sys.exit(f"SDK missing {needle}")
    tf.extractall(tmp, members=members)
print("extracted", len(members), "members")
PY
  fi

  src=$(find "$tmp" -type d -path "*/lib/${PYTHON_TAG}-linux-aarch64" | head -1)
  if [[ -z "$src" ]]; then
    rm -rf "$tmp"
    die "Extract failed — platform dir not found"
  fi
  rm -rf "$DEST"
  mkdir -p "$(dirname "$DEST")"
  mv "$src" "$DEST"
  rm -rf "$tmp"

  # Game-named launcher beside renpy (matches stock linux-x86_64 layout)
  if [[ -f "$DEST/renpy" ]]; then
    cp -f "$DEST/renpy" "$DEST/$GAME_NAME"
  elif [[ -f "$DEST/python" ]]; then
    cp -f "$DEST/python" "$DEST/$GAME_NAME"
  else
    warn "No renpy/python binary in aarch64 lib — launcher may need manual fix"
  fi
  chmod +x "$DEST"/* 2>/dev/null || true
  log "Installed: $DEST"
  ls -la "$DEST"
}

# --- patch launcher .sh for arm64 alias -------------------------------------
patch_launcher_sh() {
  if grep -q 'linux-aarch64' "$LAUNCHER_SH" && grep -Eq '\*-aarch64\|\*-arm64|arm64\)' "$LAUNCHER_SH"; then
    log "Launcher already maps aarch64/arm64"
    return 0
  fi
  if grep -q 'linux-aarch64' "$LAUNCHER_SH"; then
    log "Launcher mentions aarch64 already"
    return 0
  fi

  # Insert arm64 case before Linux-* fallback if present
  if grep -q 'Linux-\*)' "$LAUNCHER_SH"; then
    local bak
    bak="$LAUNCHER_SH.bak-before-arm"
    cp -f "$LAUNCHER_SH" "$bak"
    # Use python for safe edit
    local py
    py=$(command -v python3 || command -v python || true)
    [[ -n "$py" ]] || { warn "Cannot patch launcher without python3 — add arm64 case manually"; return 0; }
    LAUNCHER_SH="$LAUNCHER_SH" "$py" - <<'PY'
import os, pathlib, re
path = pathlib.Path(os.environ["LAUNCHER_SH"])
text = path.read_text(encoding="utf-8", errors="replace")
snippet = """        *-aarch64|*-arm64)
            RENPY_PLATFORM=\"linux-aarch64\"
            ;;
"""
if "linux-aarch64" in text and "arm64" in text:
    raise SystemExit(0)
# Insert before Linux-*) line inside the case
new, n = re.subn(
    r"(^[ \t]*Linux-\*\)[ \t]*\n)",
    snippet + r"\1",
    text,
    count=1,
    flags=re.M,
)
if n == 0:
    # fallback: before final *) in platform case — best effort
    print("WARN: could not find Linux-*) to patch", flush=True)
    raise SystemExit(0)
path.write_text(new, encoding="utf-8")
print("patched", path)
PY
    log "Patched $LAUNCHER_SH (backup: $bak)"
  else
    warn "Unexpected launcher format — not auto-patching $LAUNCHER_SH"
  fi
}

write_steam_scripts() {
  [[ "$SKIP_STEAM_SCRIPTS" -eq 1 ]] && return 0

  local wrap="$GAME_DIR/launch-steam.sh"
  local add="$GAME_DIR/add-to-steam.sh"
  local desk="$GAME_DIR/${GAME_NAME}.desktop"
  local launcher_base
  launcher_base=$(basename "$LAUNCHER_SH")

  cat > "$wrap" <<EOF
#!/usr/bin/env bash
# Steam-friendly wrapper. The stock Ren'Py launcher resolves its own basedir.
set -euo pipefail
GAME_DIR=\$(cd "\$(dirname "\$0")" && pwd)
cd "\$GAME_DIR"

for runtime in \
  "\$GAME_DIR"/lib/*-linux-aarch64/renpy \
  "\$GAME_DIR"/lib/*-linux-aarch64/python \
  "\$GAME_DIR"/lib/*-linux-aarch64/${GAME_NAME}; do
  [[ -f "\$runtime" ]] && chmod +x "\$runtime" 2>/dev/null || true
done

exec "\$GAME_DIR/${launcher_base}" "\$@"
EOF
  chmod +x "$wrap"
  log "Wrote $wrap"

  # Portable add-to-steam: rewrite .desktop paths for the unpack location, then register.
  cat > "$add" <<'EOF'
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
EOF
  chmod +x "$add"
  log "Wrote $add"

  cat > "$desk" <<EOF
[Desktop Entry]
Name=$GAME_NAME
Comment=$GAME_NAME (native Linux ARM / Ren'Py $VERSION)
Exec=$GAME_DIR/launch-steam.sh
Path=$GAME_DIR
Icon=applications-games
Terminal=false
Type=Application
Categories=Game;
StartupNotify=false
EOF
  # Note: Exec/Path are rewritten by add-to-steam.sh after unpack on the device.
  chmod +x "$desk" 2>/dev/null || true
  log "Wrote $desk"

  local readme="$GAME_DIR/README for adding games to steam.txt"
  cat > "$readme" <<EOF
================================================================================
  README — Adding this game to Steam (Linux ARM / Steam Frame)
================================================================================

This folder is a Ren'Py game already patched to run natively on Linux ARM64
(aarch64). You do NOT need to run make-linux-arm.sh on this device.

WHAT TO DO (on the Frame / ARM machine)
---------------------------------------
1. Make sure Steam is running (Big Picture / Game Mode / Desktop — any is fine).

2. Open a terminal in THIS folder (the one that contains add-to-steam.sh).

3. Run:

     chmod +x add-to-steam.sh launch-steam.sh *.sh
     ./add-to-steam.sh

4. Open your Steam library and look for "$GAME_NAME" (non-Steam shortcut).

5. Optional but recommended — game Properties → Compatibility:
     use "Steam Linux Runtime" or force native Linux
     do NOT use Proton for this build


IF SOMETHING GOES WRONG
-----------------------
- "Steam does not appear to be running"
    Start Steam, then run ./add-to-steam.sh again.

- Game appears but won't launch
    Check Compatibility (native / Steam Linux Runtime, not Proton).
    Or try from a terminal:

      ./launch-steam.sh

- You would rather add it by hand
    Steam → Games → Add a Non-Steam Game to My Library
    Browse to:  launch-steam.sh   (or the .desktop file in this folder)


FILES IN THIS FOLDER (Steam-related)
------------------------------------
  add-to-steam.sh     ← run this on the Frame to register with Steam
  launch-steam.sh     ← what Steam should launch
  ${GAME_NAME}.desktop
  README for adding games to steam.txt  ← this file


PLAY WITHOUT STEAM
------------------
  ./$(basename "$LAUNCHER_SH")
  or
  ./launch-steam.sh

================================================================================
EOF
  log "Wrote $readme"
}

create_archive() {
  [[ "$SKIP_ARCHIVE" -eq 1 ]] && return 0

  local parent out_base out excludes=()
  parent=$(dirname "$GAME_DIR")
  out_base="${parent}/${GAME_NAME}-linux-aarch64"

  # Always omit SDK cache / experiment junk / installer backups
  excludes+=(
    --exclude='.renpy-arm-cache'
    --exclude='_arm_experiment'
    --exclude='*.bak-before-arm'
    --exclude="${GAME_NAME}-linux-aarch64.zip"
    --exclude="${GAME_NAME}-linux-aarch64.7z"
  )
  if [[ "$FULL_ARCHIVE" -eq 0 ]]; then
    excludes+=(
      --exclude='lib/py3-windows-*'
      --exclude='lib/py2-windows-*'
      --exclude='*.exe'
    )
  fi

  # Prefer zip (universal); fall back to 7z; then tar.gz
  if command -v zip >/dev/null 2>&1; then
    out="${out_base}.zip"
    rm -f "$out"
    log "Creating archive $out"
    (
      cd "$parent"
      # zip exclude syntax is different — build file list via tar stream instead for portability
      true
    )
    # Use Python zip for consistent excludes across platforms
    local py
    py=$(command -v python3 || command -v python || true)
    if [[ -n "$py" ]]; then
      GAME_DIR="$GAME_DIR" OUT="$out" FULL="$FULL_ARCHIVE" GAME_NAME="$GAME_NAME" "$py" - <<'PY'
import os, zipfile
from pathlib import Path

root = Path(os.environ["GAME_DIR"]).resolve()
out = Path(os.environ["OUT"])
full = os.environ.get("FULL", "0") == "1"
game_name = os.environ["GAME_NAME"]
skip_dirs = {".renpy-arm-cache", "_arm_experiment"}
skip_suffixes = {".bak-before-arm"}
skip_names = {f"{game_name}-linux-aarch64.zip", f"{game_name}-linux-aarch64.7z", f"{game_name}-linux-aarch64.tar.gz"}

def wanted(p: Path) -> bool:
    rel = p.relative_to(root)
    parts = rel.parts
    if parts and parts[0] in skip_dirs:
        return False
    if rel.name in skip_names:
        return False
    if any(str(rel).endswith(suf) for suf in skip_suffixes):
        return False
    if not full:
        if parts[:1] == ("lib",) and len(parts) > 1 and parts[1].startswith(("py3-windows-", "py2-windows-")):
            return False
        if rel.suffix.lower() == ".exe":
            return False
    return True

with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if not wanted(path):
            continue
        arc = Path(game_name) / path.relative_to(root)
        zf.write(path, arcname=str(arc).replace("\\", "/"))
print(out)
PY
      ARCHIVE_PATH="$out"
      log "Archive ready: $ARCHIVE_PATH ($(du -h "$ARCHIVE_PATH" | awk '{print $1}'))"
      return 0
    fi
  fi

  if command -v 7z >/dev/null 2>&1 || command -v 7zz >/dev/null 2>&1; then
    local seven
    seven=$(command -v 7z || command -v 7zz)
    out="${out_base}.7z"
    rm -f "$out"
    log "Creating archive $out"
    # 7z: copy to temp list is painful; archive folder with -xr exclusions
    local xargs_7z=(-xr'!'.renpy-arm-cache -xr'!'_arm_experiment -xr'!'*.bak-before-arm)
    if [[ "$FULL_ARCHIVE" -eq 0 ]]; then
      xargs_7z+=(-xr'!'lib/py3-windows-* -xr'!'lib/py2-windows-* -xr'!'*.exe)
    fi
    (cd "$parent" && "$seven" a -t7z "${xargs_7z[@]}" "$out" "$(basename "$GAME_DIR")")
    ARCHIVE_PATH="$out"
    log "Archive ready: $ARCHIVE_PATH"
    return 0
  fi

  out="${out_base}.tar.gz"
  rm -f "$out"
  log "Creating archive $out (tar.gz fallback)"
  local tar_ex=(--exclude='.renpy-arm-cache' --exclude='_arm_experiment' --exclude='*.bak-before-arm')
  if [[ "$FULL_ARCHIVE" -eq 0 ]]; then
    tar_ex+=(--exclude='lib/py3-windows-*' --exclude='lib/py2-windows-*' --exclude='*.exe')
  fi
  tar -czf "$out" "${tar_ex[@]}" -C "$parent" "$(basename "$GAME_DIR")"
  ARCHIVE_PATH="$out"
  log "Archive ready: $ARCHIVE_PATH"
}

# --- main -------------------------------------------------------------------
if [[ "$ALREADY" -eq 0 ]]; then
  download_sdk
  verify_checksum
  extract_aarch64
else
  # Still ensure game-named binary exists
  if [[ -f "$DEST/renpy" && ! -f "$DEST/$GAME_NAME" ]]; then
    cp -f "$DEST/renpy" "$DEST/$GAME_NAME"
    chmod +x "$DEST/$GAME_NAME"
  fi
fi

patch_launcher_sh
chmod +x "$LAUNCHER_SH" 2>/dev/null || true
write_steam_scripts

if [[ "$KEEP_CACHE" -eq 0 ]]; then
  rm -f "$SDK_FILE"
  log "Cleaned cache file"
fi

create_archive

cat <<EOF

Done. Native Linux ARM64 runtime is ready in:
  $GAME_DIR

Next steps:
  1) Copy the archive to your ARM device (Frame, etc.)
$(if [[ -n "$ARCHIVE_PATH" ]]; then echo "       $ARCHIVE_PATH"; else echo "       (no archive — tree was patched in place; --no-archive was set or pack failed)"; fi)
  2) Unpack it on the device
  3) Run:  chmod +x add-to-steam.sh launch-steam.sh *.sh
           ./add-to-steam.sh

Direct play without Steam:
  ./$(basename "$LAUNCHER_SH")
  or ./launch-steam.sh
EOF

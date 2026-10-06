"""Ren'Py → Linux aarch64 conversion core (pure Python)."""
from __future__ import annotations

import hashlib
import marshal
import os
import re
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .profiles import (
    ProfileError,
    detect_legacy_version,
    detect_profile,
    is_legacy_renpy_game,
    migrate_profile,
)

LogFn = Callable[[str], None]

HELPER_SH = {
    "make-linux-arm.sh",
    "launch-steam.sh",
    "add-to-steam.sh",
    "make-rpgmaker-arm.sh",
}

VER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:\.\d+)?")


@dataclass
class ConvertResult:
    game_dir: Path
    game_name: str
    version: str
    archive_path: Optional[Path]
    messages: list[str] = field(default_factory=list)


class ConvertError(Exception):
    pass


def _log(log: Optional[LogFn], msg: str) -> None:
    if log:
        log(msg)


def normalize_version(s: str) -> Optional[str]:
    m = VER_RE.search(s.strip().strip("'\""))
    if m:
        return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    return None


def find_launcher_sh(game_dir: Path) -> Path:
    sh_files = sorted(game_dir.glob("*.sh"))
    preferred = []
    fallback = []
    for f in sh_files:
        if f.name in HELPER_SH:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "RENPY_PLATFORM" in text:
            preferred.append(f)
        else:
            fallback.append(f)
    if preferred:
        return preferred[0]
    if fallback:
        return fallback[0]
    raise ConvertError("No Ren'Py .sh launcher found (expected a script with RENPY_PLATFORM).")


def detect_python_tag(game_dir: Path) -> str:
    lib = game_dir / "lib"
    has_py2 = any(lib.glob("py2-*")) if lib.is_dir() else False
    has_py3 = any(lib.glob("py3-*")) if lib.is_dir() else False
    if has_py2 and not has_py3:
        return "py2"
    return "py3"


def _from_py_source(path: Path) -> Optional[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"""(?m)^version\s*=\s*['\"]([^'\"]+)['\"]""", text)
    if m:
        n = normalize_version(m.group(1))
        if n:
            return n
    m = re.search(
        r"""(?m)^vc_version\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)""",
        text,
    )
    if m:
        return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    for m in re.finditer(r"""['\"](\d+\.\d+\.\d+(?:\.\d+)?)['\"]""", text):
        n = normalize_version(m.group(1))
        if n:
            return n
    return None


def _load_pyc_code(path: Path):
    data = path.read_bytes()
    for skip in (16, 12, 8):
        try:
            return marshal.loads(data[skip:])
        except Exception:
            continue
    return None


def _from_pyc(path: Path) -> Optional[str]:
    code = _load_pyc_code(path)
    if code is None:
        return None
    found: list[str] = []

    def walk(c):
        for x in c.co_consts:
            if isinstance(x, str):
                n = normalize_version(x)
                if n:
                    found.append(n)
            elif hasattr(x, "co_consts"):
                walk(x)

    walk(code)
    return found[0] if found else None


def detect_version(game_dir: Path, override: Optional[str] = None) -> str:
    if override:
        n = normalize_version(override)
        if not n:
            raise ConvertError(f"Invalid version override: {override}")
        return n

    for path in (
        game_dir / "renpy" / "vc_version.py",
        game_dir / "renpy" / "versions.py",
        game_dir / "renpy" / "__init__.py",
    ):
        if path.is_file():
            n = _from_py_source(path)
            if n:
                return n

    candidates = [
        game_dir / "renpy" / "vc_version.pyc",
        game_dir / "renpy" / "versions.pyc",
    ]
    pycache = game_dir / "renpy" / "__pycache__"
    if pycache.is_dir():
        candidates.extend(sorted(pycache.glob("vc_version.cpython-*.pyc")))
        candidates.extend(sorted(pycache.glob("versions.cpython-*.pyc")))
    for path in candidates:
        if path.is_file():
            n = _from_pyc(path)
            if n:
                return n

    raise ConvertError(
        "Could not detect Ren'Py version from renpy/vc_version.py or .pyc. "
        "Set the version manually."
    )


def is_modern_renpy_game(game_dir: Path) -> bool:
    return (game_dir / "renpy").is_dir() and (game_dir / "lib").is_dir()


def is_renpy_game(game_dir: Path) -> bool:
    """Recognize both modern distributions and supported legacy layouts."""
    return is_modern_renpy_game(game_dir) or is_legacy_renpy_game(game_dir)


def _safe_extract_zip(zf: zipfile.ZipFile, destination: Path) -> None:
    destination = destination.resolve()
    for member in zf.infolist():
        target = (destination / member.filename).resolve()
        try:
            target.relative_to(destination)
        except ValueError as exc:
            raise ConvertError(f"Unsafe path in zip archive: {member.filename}") from exc
    zf.extractall(destination)


def _safe_extract_tar(tf: tarfile.TarFile, destination: Path) -> None:
    destination = destination.resolve()
    for member in tf.getmembers():
        target = (destination / member.name).resolve()
        try:
            target.relative_to(destination)
        except ValueError as exc:
            raise ConvertError(f"Unsafe path in tar archive: {member.name}") from exc
    tf.extractall(destination)


def default_cache_dir() -> Path:
    """Return a persistent per-user cache for SDKs and compatibility assets."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "RenFrame" / "cache"
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / "renframe"
    return Path.home() / ".cache" / "renframe"


def resolve_input(path: Path, work_root: Path, log: Optional[LogFn] = None) -> Path:
    """Return a game directory. Archives are extracted under work_root."""
    path = path.resolve()
    if path.is_dir():
        if is_renpy_game(path):
            return path
        # nested single folder
        kids = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if len(kids) == 1 and is_renpy_game(kids[0]):
            return kids[0]
        raise ConvertError(f"Not a recognizable Ren'Py game folder: {path}")

    if not path.is_file():
        raise ConvertError(f"Path not found: {path}")

    suffix = path.suffix.lower()
    extract_dir = work_root / f"extract-{path.stem}"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True)

    _log(log, f"Extracting archive {path.name}…")
    if suffix == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            _safe_extract_zip(zf, extract_dir)
    elif suffix in {".gz", ".bz2", ".xz"} or path.name.endswith((".tar.gz", ".tar.bz2", ".tgz")):
        with tarfile.open(path, "r:*") as tf:
            _safe_extract_tar(tf, extract_dir)
    elif suffix == ".7z":
        raise ConvertError("`.7z` input is not supported yet — use .zip or a folder.")
    else:
        raise ConvertError(f"Unsupported archive type: {path.name}")

    if is_renpy_game(extract_dir):
        return extract_dir
    # common: archive contains one top-level folder
    kids = [p for p in extract_dir.iterdir() if p.is_dir()]
    for kid in kids:
        if is_renpy_game(kid):
            return kid
    raise ConvertError("Archive did not contain a recognizable Ren'Py game.")


def download_sdk(version: str, cache_dir: Path, force: bool, log: Optional[LogFn] = None) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    name = f"renpy-{version}-sdkarm.tar.bz2"
    url = f"https://www.renpy.org/dl/{version}/{name}"
    dest = cache_dir / name
    if dest.is_file() and not force:
        _log(log, f"Using cached SDK: {dest.name}")
        return dest
    _log(log, f"Downloading {url}")
    partial = dest.with_suffix(dest.suffix + ".partial")
    try:
        urllib.request.urlretrieve(url, partial)
    except Exception as e:
        raise ConvertError(
            f"Failed to download SDK for Ren'Py {version}.\n{e}\n"
            f"Check https://www.renpy.org/dl/{version}/"
        ) from e
    partial.replace(dest)
    return dest


def verify_sdk_checksum(sdk_file: Path, version: str, log: Optional[LogFn] = None) -> None:
    url = f"https://www.renpy.org/dl/{version}/checksums.txt"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except Exception:
        _log(log, "No checksums.txt — skipping verify")
        return

    section = None
    expected = None
    name = sdk_file.name
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
            expected = digest
            break
        if expected is None and len(digest) == 64:
            expected = digest
    if not expected:
        _log(log, "Could not parse SHA256 — skipping verify")
        return
    got = hashlib.sha256(sdk_file.read_bytes()).hexdigest()
    if got != expected:
        raise ConvertError(f"SHA256 mismatch for {name}\nexpected: {expected}\ngot: {got}")
    _log(log, "Checksum OK")


def extract_aarch64(
    sdk_file: Path,
    game_dir: Path,
    python_tag: str,
    game_name: str,
    log: Optional[LogFn] = None,
) -> Path:
    dest = game_dir / "lib" / f"{python_tag}-linux-aarch64"
    needle = f"/lib/{python_tag}-linux-aarch64"
    _log(log, f"Extracting {python_tag}-linux-aarch64 from SDK…")
    with tempfile.TemporaryDirectory(prefix="renpy-sdk-") as tmp:
        tmp_path = Path(tmp)
        with tarfile.open(sdk_file, "r:bz2") as tf:
            members = [m for m in tf.getmembers() if needle in m.name.replace("\\", "/")]
            if not members:
                raise ConvertError(
                    f"SDK missing lib/{python_tag}-linux-aarch64 — "
                    "this Ren'Py version may not ship ARM."
                )
            tf.extractall(tmp_path, members=members)
        found = list(tmp_path.rglob(f"{python_tag}-linux-aarch64"))
        found = [p for p in found if p.is_dir()]
        if not found:
            raise ConvertError("Extract failed — platform directory not found")
        src = found[0]
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))

    renpy_bin = dest / "renpy"
    py_bin = dest / "python"
    named = dest / game_name
    if renpy_bin.is_file():
        shutil.copy2(renpy_bin, named)
    elif py_bin.is_file():
        shutil.copy2(py_bin, named)
    else:
        _log(log, "WARNING: No renpy/python binary in aarch64 lib")
    for p in dest.iterdir():
        try:
            p.chmod(p.stat().st_mode | 0o111)
        except OSError:
            pass
    _log(log, f"Installed: {dest}")
    return dest


def patch_launcher_sh(launcher: Path, log: Optional[LogFn] = None) -> None:
    text = launcher.read_text(encoding="utf-8", errors="replace")
    if "linux-aarch64" in text and re.search(r"aarch64|arm64", text):
        _log(log, "Launcher already maps aarch64/arm64")
        return
    snippet = (
        '        *-aarch64|*-arm64)\n'
        '            RENPY_PLATFORM="linux-aarch64"\n'
        "            ;;\n"
    )
    new, n = re.subn(
        r"(^[ \t]*Linux-\*\)[ \t]*\n)",
        snippet + r"\1",
        text,
        count=1,
        flags=re.M,
    )
    if n == 0:
        _log(log, "WARNING: Could not auto-patch launcher — unexpected format")
        return
    bak = launcher.with_suffix(launcher.suffix + ".bak-before-arm")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    launcher.write_text(new, encoding="utf-8")
    _log(log, f"Patched {launcher.name}")


def write_steam_helpers(game_dir: Path, game_name: str, version: str, launcher: Path, log: Optional[LogFn] = None) -> None:
    launcher_base = launcher.name
    wrap = game_dir / "launch-steam.sh"
    wrap.write_text(
        f"""#!/usr/bin/env bash
# Steam-friendly wrapper: resolves game dir from this script, passes basedir explicitly.
set -euo pipefail
GAME_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$GAME_DIR"
exec "$GAME_DIR/{launcher_base}" "$GAME_DIR" "$@"
""",
        encoding="utf-8",
        newline="\n",
    )

    add = game_dir / "add-to-steam.sh"
    add.write_text(
        r'''#!/usr/bin/env bash
# Register this Ren'Py Linux ARM build as a non-Steam game.
# Run on the ARM device AFTER unpacking (Steam must be running).
set -euo pipefail

GAME_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$GAME_DIR"

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

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
if [[ ! -f "$DESKTOP" ]]; then
  for d in "$GAME_DIR"/*.desktop; do
    [[ -e "$d" ]] || continue
    DESKTOP="$d"
    break
  done
fi

NAME="$GAME_NAME"
if [[ -f "$DESKTOP" ]]; then
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
''',
        encoding="utf-8",
        newline="\n",
    )

    desk = game_dir / f"{game_name}.desktop"
    desk.write_text(
        f"""[Desktop Entry]
Name={game_name}
Comment={game_name} (native Linux ARM / Ren'Py {version})
Exec={game_dir.as_posix()}/launch-steam.sh
Path={game_dir.as_posix()}
Icon=applications-games
Terminal=false
Type=Application
Categories=Game;
StartupNotify=false
""",
        encoding="utf-8",
        newline="\n",
    )

    readme = game_dir / "README for adding games to steam.txt"
    readme.write_text(
        f"""================================================================================
  README — Adding this game to Steam (Linux ARM / Steam Frame)
================================================================================

This folder is a Ren'Py game already patched to run natively on Linux ARM64
(aarch64). You do NOT need to run the converter again on this device.

WHAT TO DO (on the Frame / ARM machine)
---------------------------------------
1. Make sure Steam is running (Big Picture / Game Mode / Desktop — any is fine).

2. Open a terminal in THIS folder (the one that contains add-to-steam.sh).

3. Run:

     chmod +x add-to-steam.sh launch-steam.sh *.sh
     ./add-to-steam.sh

4. Open your Steam library and look for "{game_name}" (non-Steam shortcut).

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
  {game_name}.desktop
  README for adding games to steam.txt  ← this file


PLAY WITHOUT STEAM
------------------
  ./{launcher_base}
  or
  ./launch-steam.sh

================================================================================
""",
        encoding="utf-8",
        newline="\n",
    )

    for p in (wrap, add):
        try:
            p.chmod(p.stat().st_mode | 0o111)
        except OSError:
            pass
    _log(log, "Wrote launch-steam.sh, add-to-steam.sh, desktop, Steam README")


def create_zip_archive(
    game_dir: Path,
    game_name: str,
    out_path: Path,
    full: bool = False,
    log: Optional[LogFn] = None,
) -> Path:
    skip_dirs = {".renpy-arm-cache", "_arm_experiment", ".git"}
    skip_names = {
        f"{game_name}-linux-aarch64.zip",
        f"{game_name}-linux-aarch64.7z",
        f"{game_name}-linux-aarch64.tar.gz",
        out_path.name,
    }

    def wanted(p: Path) -> bool:
        rel = p.relative_to(game_dir)
        parts = rel.parts
        if parts and parts[0] in skip_dirs:
            return False
        if rel.name in skip_names:
            return False
        if str(rel).endswith(".bak-before-arm"):
            return False
        if not full:
            if len(parts) > 1 and parts[0] == "lib" and parts[1].startswith(("py3-windows-", "py2-windows-")):
                return False
            if parts[:1] == ("lib",) and len(parts) > 1 and "linux-x86_64" in parts[1]:
                return False
            if rel.suffix.lower() == ".exe":
                return False
        return True

    if out_path.exists():
        out_path.unlink()
    _log(log, f"Creating archive {out_path.name}…")
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in game_dir.rglob("*"):
            if not path.is_file():
                continue
            if not wanted(path):
                continue
            arc = Path(game_name) / path.relative_to(game_dir)
            zf.write(path, arcname=str(arc).replace("\\", "/"))
    _log(log, f"Archive ready: {out_path}")
    return out_path


FRAME_INSTRUCTIONS = """On your Steam Frame (after copying the zip):

1. Unpack the zip somewhere convenient (e.g. ~/Games/).
2. Start Steam.
3. In a terminal inside the unpacked game folder:

     chmod +x add-to-steam.sh launch-steam.sh *.sh
     ./add-to-steam.sh

4. Find the game in your Steam library (non-Steam shortcut).
5. Properties → Compatibility: Steam Linux Runtime / native — not Proton.

Play without Steam: ./launch-steam.sh
"""


def convert_game(
    source: Path,
    *,
    output_zip: Optional[Path] = None,
    version_override: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    force: bool = False,
    work_dir: Optional[Path] = None,
    full_archive: bool = False,
    log: Optional[LogFn] = None,
) -> ConvertResult:
    """
    Convert a Ren'Py PC game folder or archive into a Linux aarch64 zip.

    By default the game is patched in a working copy under work_dir when the
    source is an archive; folders are patched in place then zipped beside them.
    """
    messages: list[str] = []

    def emit(msg: str) -> None:
        messages.append(msg)
        _log(log, msg)

    work = work_dir or Path(tempfile.mkdtemp(prefix="renpy-arm-work-"))
    work.mkdir(parents=True, exist_ok=True)
    cache = cache_dir or default_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)

    game_dir = resolve_input(source, work, log=emit)

    profile_match = detect_profile(game_dir)
    if profile_match is not None:
        try:
            game_dir = migrate_profile(
                profile_match,
                game_dir,
                work_root=work,
                cache_dir=cache,
                force=force,
                log=emit,
            )
        except ProfileError as exc:
            raise ConvertError(str(exc)) from exc

    if not is_modern_renpy_game(game_dir):
        legacy_version = detect_legacy_version(game_dir)
        if legacy_version:
            raise ConvertError(
                f"Legacy Ren'Py {legacy_version} detected, but RenFrame has no "
                "compatibility profile for this game yet."
            )
        raise ConvertError(
            "Ren'Py game detected, but this distribution does not contain the "
            "modern lib/ runtime layout and no compatibility profile matched."
        )

    launcher = find_launcher_sh(game_dir)
    game_name = launcher.stem
    python_tag = detect_python_tag(game_dir)
    version = detect_version(game_dir, version_override)
    emit(f"Game: {game_name}")
    emit(f"Ren'Py {version} ({python_tag})")

    dest = game_dir / "lib" / f"{python_tag}-linux-aarch64"
    need_extract = force or not (dest / "librenpython.so").is_file()
    if need_extract:
        sdk = download_sdk(version, cache, force=force, log=emit)
        verify_sdk_checksum(sdk, version, log=emit)
        extract_aarch64(sdk, game_dir, python_tag, game_name, log=emit)
    else:
        emit(f"Already have {dest.name} (use force to re-download)")
        named = dest / game_name
        renpy_bin = dest / "renpy"
        if renpy_bin.is_file() and not named.exists():
            shutil.copy2(renpy_bin, named)

    patch_launcher_sh(launcher, log=emit)
    write_steam_helpers(game_dir, game_name, version, launcher, log=emit)

    if output_zip is None:
        output_zip = game_dir.parent / f"{game_name}-linux-aarch64.zip"
    output_zip = output_zip.resolve()
    create_zip_archive(game_dir, game_name, output_zip, full=full_archive, log=emit)

    emit("Done.")
    return ConvertResult(
        game_dir=game_dir,
        game_name=game_name,
        version=version,
        archive_path=output_zip,
        messages=messages,
    )

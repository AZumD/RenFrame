"""Shared path and filesystem helpers."""

from __future__ import annotations

from pathlib import Path


def normalize_path(path: Path | str) -> Path:
    """Return a resolved absolute path without requiring the target to exist."""
    return Path(path).expanduser().resolve(strict=False)


_FORBIDDEN_OUTPUT_ROOTS = frozenset(
    {
        Path("/"),
        Path("/root"),
        Path("/home"),
        Path("/usr"),
        Path("/etc"),
        Path("/var"),
        Path("/tmp"),
        Path("/opt"),
        Path("/boot"),
        Path("/dev"),
        Path("/proc"),
        Path("/sys"),
    }
)


def is_dangerous_output_path(path: Path) -> bool:
    """Return True for paths that must never be used as build output."""
    resolved = normalize_path(path)
    return resolved in _FORBIDDEN_OUTPUT_ROOTS


def paths_conflict(source: Path, output: Path) -> bool:
    """True if output equals source or is nested under source (self-copy risk)."""
    src = normalize_path(source)
    out = normalize_path(output)
    if out == src:
        return True
    try:
        out.relative_to(src)
        return True
    except ValueError:
        pass
    try:
        src.relative_to(out)
        return True
    except ValueError:
        return False


def guess_game_name(source: Path) -> str:
    """Best-effort display name from directory name."""
    name = source.name.strip()
    return name or "Unknown Game"


RUNTIME_DIR_NAMES = frozenset(
    {
        "renpy",
        "lib",
        "rapt",
        "renios",
        "update",
    }
)

RUNTIME_FILE_NAMES = frozenset(
    {
        "renpy.py",
        "renpy.sh",
        "renpy.app",
    }
)


def is_runtime_owned_path(relative: Path) -> bool:
    """
    Classify a path relative to the game root as stock Ren'Py runtime.

    Game content lives primarily under game/. Stock runtime binaries live under
    renpy/, lib/, and top-level launcher wrappers.
    """
    parts = relative.parts
    if not parts:
        return False

    first = parts[0].lower()
    if first in RUNTIME_DIR_NAMES:
        return True

    name = relative.name.lower()
    if len(parts) == 1 and (
        name in RUNTIME_FILE_NAMES
        or name.endswith(".sh")
        or name.endswith(".exe")
        or name.endswith(".app")
        or name.endswith(".py")
    ):
        # Top-level launchers and renpy.py are runtime/distribution wrappers.
        return True

    return False

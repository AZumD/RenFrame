"""Build ARM64-ready game directories (stub; not part of the inspection MVP)."""

from __future__ import annotations

from pathlib import Path


class BuildError(RuntimeError):
    """Raised when a build cannot proceed."""


def build_game(
    source: Path,
    *,
    output: Path | None = None,
    runtime: Path | None = None,
    force: bool = False,
) -> Path:
    """
    Create an ARM64 Ren'Py game directory.

    Not implemented in the inspection-only milestone.
    """
    raise BuildError(
        "renframe build is not implemented yet. "
        "Use `renframe inspect` for compatibility scanning first."
    )

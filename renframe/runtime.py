"""ARM64 Ren'Py runtime cache/manager abstraction (stub for later build work)."""

from __future__ import annotations

from pathlib import Path


class RuntimeManager:
    """
    Manage cached ARM64 Ren'Py runtimes.

    The inspection MVP does not download or install runtimes. Build support will
    call into this manager once implemented.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        home = Path.home()
        self.cache_dir = cache_dir or (home / ".cache" / "renframe" / "runtimes")

    def find_runtime(self, version: str | None = None) -> Path | None:
        """Locate a cached runtime directory, optionally matching a version."""
        if not self.cache_dir.is_dir():
            return None
        candidates = sorted(p for p in self.cache_dir.iterdir() if p.is_dir())
        if version:
            version_key = version.lower()
            for path in candidates:
                if version_key in path.name.lower():
                    return path
            return None
        return candidates[0] if candidates else None

    def install_runtime(self, source: Path, *, name: str | None = None) -> Path:
        """Install/copy a user-provided runtime into the cache (not yet implemented)."""
        raise NotImplementedError(
            "Runtime installation is not implemented in the inspection MVP. "
            "Pass --runtime explicitly once build support lands."
        )

    def list_cached_runtimes(self) -> list[Path]:
        """List cached runtime directories."""
        if not self.cache_dir.is_dir():
            return []
        return sorted(p for p in self.cache_dir.iterdir() if p.is_dir())

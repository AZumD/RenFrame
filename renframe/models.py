"""Typed models for RenFrame inspection results."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Compatibility(str, Enum):
    """High-level compatibility verdict for ARM64 runtime replacement."""

    LIKELY_COMPATIBLE = "LIKELY_COMPATIBLE"
    NEEDS_TESTING = "NEEDS_TESTING"
    INCOMPATIBLE_NATIVE_CODE = "INCOMPATIBLE_NATIVE_CODE"
    UNKNOWN_RENPY_VERSION = "UNKNOWN_RENPY_VERSION"
    NOT_A_RENPY_GAME = "NOT_A_RENPY_GAME"


class Ownership(str, Enum):
    """Whether a native artifact belongs to the stock runtime or the game."""

    RUNTIME = "runtime"
    GAME = "game"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class NativeDependency:
    """A native/binary artifact found during scanning."""

    path: Path
    kind: str
    architecture: str | None
    ownership: Ownership
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "kind": self.kind,
            "architecture": self.architecture,
            "ownership": self.ownership.value,
            "notes": self.notes,
        }


@dataclass
class VersionHint:
    """One modular Ren'Py version detection result."""

    version: str | None
    generation: int | None
    source: str
    confidence: str = "medium"
    details: str = ""


@dataclass
class GameInspection:
    """Full inspection result for a candidate Ren'Py game directory."""

    source_path: Path
    is_renpy: bool
    game_name: str | None = None
    renpy_version: str | None = None
    generation: int | None = None
    version_source: str | None = None
    detected_architectures: list[str] = field(default_factory=list)
    has_game_dir: bool = False
    has_renpy_dir: bool = False
    has_lib_dir: bool = False
    native_dependencies: list[NativeDependency] = field(default_factory=list)
    windows_executables: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    potential_issues: list[str] = field(default_factory=list)
    version_hints: list[VersionHint] = field(default_factory=list)
    compatibility: Compatibility = Compatibility.NOT_A_RENPY_GAME

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "is_renpy": self.is_renpy,
            "game_name": self.game_name,
            "renpy_version": self.renpy_version,
            "generation": self.generation,
            "version_source": self.version_source,
            "detected_architectures": list(self.detected_architectures),
            "has_game_dir": self.has_game_dir,
            "has_renpy_dir": self.has_renpy_dir,
            "has_lib_dir": self.has_lib_dir,
            "native_dependencies": [n.to_dict() for n in self.native_dependencies],
            "windows_executables": list(self.windows_executables),
            "warnings": list(self.warnings),
            "potential_issues": list(self.potential_issues),
            "version_hints": [asdict(h) for h in self.version_hints],
            "compatibility": self.compatibility.value,
        }

"""Human-readable and JSON inspection reports."""

from __future__ import annotations

import json
from typing import Any

from renframe.models import Compatibility, GameInspection, Ownership


def format_human_report(inspection: GameInspection) -> str:
    """Render a compatibility scan as plain text."""
    lines: list[str] = []
    lines.append("RenFrame compatibility scan")
    lines.append("")
    lines.append(f"Game: {inspection.game_name or 'Unknown'}")
    lines.append(
        f"Ren'Py installation detected: {'yes' if inspection.is_renpy else 'no'}"
    )
    lines.append(
        f"Detected Ren'Py version: {inspection.renpy_version or 'unknown'}"
    )
    if inspection.generation is not None:
        lines.append(f"Detected Ren'Py generation: {inspection.generation}.x")
    if inspection.version_source:
        lines.append(f"Version source: {inspection.version_source}")

    arch = ", ".join(inspection.detected_architectures) or "unknown"
    lines.append(f"Detected architecture: {arch}")
    lines.append(
        f"Game directory: {'./game' if inspection.has_game_dir else 'not found'}"
    )
    lines.append("")

    lines.append("Native libraries:")
    game_libs = [
        d
        for d in inspection.native_dependencies
        if d.kind in {"shared_library", "python_extension"}
        and d.ownership == Ownership.GAME
    ]
    if not game_libs:
        lines.append("  none found")
    else:
        for dep in game_libs:
            arch_s = dep.architecture or "unknown"
            lines.append(f"  {arch_s}: {dep.path}")

    lines.append("")
    lines.append("Windows executables:")
    if not inspection.windows_executables:
        lines.append("  none found")
    else:
        for item in inspection.windows_executables:
            lines.append(f"  {item}")

    lines.append("")
    lines.append("Potential issues:")
    issues = inspection.potential_issues or ["none"]
    for issue in issues:
        lines.append(f"  {issue}")

    if inspection.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in inspection.warnings:
            lines.append(f"  {warning}")

    lines.append("")
    lines.append("Verdict:")
    lines.append(f"  {_verdict_blurb(inspection.compatibility)}")
    lines.append(f"  ({inspection.compatibility.value})")
    return "\n".join(lines) + "\n"


def _verdict_blurb(compatibility: Compatibility) -> str:
    return {
        Compatibility.LIKELY_COMPATIBLE: (
            "likely compatible with ARM runtime replacement"
        ),
        Compatibility.NEEDS_TESTING: (
            "possibly compatible, but needs testing on ARM64"
        ),
        Compatibility.INCOMPATIBLE_NATIVE_CODE: (
            "game-specific native code appears incompatible with ARM64 replacement"
        ),
        Compatibility.UNKNOWN_RENPY_VERSION: (
            "Ren'Py game detected, but version/generation could not be determined"
        ),
        Compatibility.NOT_A_RENPY_GAME: (
            "not recognized as a Ren'Py game"
        ),
    }.get(compatibility, compatibility.value)


def format_json_report(inspection: GameInspection) -> str:
    """Serialize inspection result as indented JSON."""
    payload: dict[str, Any] = inspection.to_dict()
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"

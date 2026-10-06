# MODELS.md

Equivalent script: `renframe/models.py`

## Purpose

Typed dataclasses and enums for inspection and build results.

## Types

- `Compatibility` — verdict enum
- `Ownership` — runtime vs game
- `NativeDependency` — one binary artifact
- `VersionHint` — one detector strategy result
- `GameInspection` — full source report (`to_dict()` for JSON)
- `RuntimeInspection` — supplied ARM/SDK runtime report
- `BuildResult` — build / dry-run outcome (`to_dict()` for JSON)

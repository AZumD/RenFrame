# MODELS.md

Equivalent script: `renframe/models.py`

## Purpose

Typed dataclasses and enums for inspection results.

## Types

- `Compatibility` — verdict enum
- `Ownership` — runtime vs game
- `NativeDependency` — one binary artifact
- `VersionHint` — one detector strategy result
- `GameInspection` — full report (`to_dict()` for JSON)

# UTILS.md

Equivalent script: `renframe/utils.py`

## Purpose

Path normalization and safety helpers used by inspection and (later) build.

## Key helpers

- `normalize_path`
- `is_dangerous_output_path` — refuse `/`, `/usr`, `/tmp`, etc.
- `paths_conflict` — source/output equality or nesting
- `is_runtime_owned_path` — classify relative paths as stock runtime

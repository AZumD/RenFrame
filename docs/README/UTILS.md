# UTILS.md

Equivalent script: `renframe/utils.py`

## Purpose

Path normalization and safety helpers used by inspection and build.

## Key helpers

- `normalize_path`
- `is_dangerous_output_path` — refuse `/`, `/usr`, `/tmp`, drive roots, etc.
- `is_path_inside` / `is_ancestor` — nesting checks
- `paths_conflict` — source/output equality or nesting either way
- `sanitize_fs_name` — launcher / filesystem-safe name
- `is_runtime_owned_path` — classify relative paths as stock runtime

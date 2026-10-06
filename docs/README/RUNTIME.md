# RUNTIME.md

Equivalent script: `renframe/runtime.py`

## Purpose

Inspect and describe a user-supplied Ren'Py SDK/runtime, plus a stub cache
manager for a future download milestone.

## Runtime inspection

```python
inspect_runtime(path) -> RuntimeInspection
```

Fields include: `is_renpy_runtime`, `architecture`, `version`, `generation`,
`warnings`, launcher flags, and `lib_architectures`.

Architecture detection reuses `detect_runtime_architectures` (lib folder names)
and ELF sampling under `lib/` via `read_elf_architecture`. Clearly x86-only
runtimes are rejected by the builder; unusual layouts without a detectable arch
warn but are not hard-failed.

## Layout

```python
detect_runtime_layout(path) -> RuntimeLayout
```

Captures `root`, `game_dir`, `launcher` (`renpy.sh` when present), `renpy_py`,
`python_bin`, and `arm_lib_dir`. Used when generating the Frame launcher.

## Cache manager

`RuntimeManager` still only lists/finds directories under
`~/.cache/renframe/runtimes/`. `install_runtime` remains unimplemented;
builds require explicit `--runtime`.

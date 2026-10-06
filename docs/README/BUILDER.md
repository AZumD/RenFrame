# BUILDER.md

Equivalent script: `renframe/builder.py`

## Purpose

Create a self-contained ARM64 Ren'Py game directory by combining a
user-supplied ARM runtime/template with the source game's `game/` payload.

## Strategy

```text
ARM64 Ren'Py runtime/template
         +
  source game/ payload
         =
    Frame build output
```

The builder does **not** surgically rewrite the source x86 runtime. It copies
the supplied ARM runtime, replaces any template `game/` directory, copies the
source `game/` tree intact, and generates a game-specific launcher.

## Entry point

```python
build_game(
    source,
    output=None,
    runtime=None,
    force=False,
    dry_run=False,
    allow_version_mismatch=False,
) -> BuildResult
```

## Default output

```text
<source-parent>/<source-name>-frame
```

## Pre-build validation

1. Inspect the source via `inspect_game`
2. Refuse non-Ren'Py sources
3. Refuse `INCOMPATIBLE_NATIVE_CODE`
4. Allow `LIKELY_COMPATIBLE`
5. Allow `NEEDS_TESTING` (warning)
6. Inspect/validate the supplied runtime (`inspect_runtime`)
7. Refuse clearly x86-only runtimes
8. Compare Ren'Py generations (fail on 7↔8 unless `--allow-version-mismatch`)
9. Path safety (no source/runtime/output overlap; refuse dangerous roots)

## Staging

Builds into `.<output-name>.tmp-<token>` beside the destination, then renames
into place. Failures clean the temp tree and leave source (and existing output,
until `--force` replacement begins) untouched.

## Launcher

Generates `<GameName>.sh` that resolves its own directory and `exec`s the
runtime's `renpy.sh` (preferred) or ARM `python` + `renpy.py`, forwarding args.

## Limitations (MVP)

- Only the source `game/` directory is injected (conservative; no blind copy of
  source `lib/` / `renpy/`)
- No automatic runtime download
- No `.desktop` / Steam shortcut generation

# CLI.md

Equivalent script: `renframe/cli.py`

## Purpose

Argparse entrypoint for the `renframe` console command.

## Commands

### inspect

```bash
renframe inspect <directory> [--json]
```

### build

```bash
renframe build <directory> --runtime <arm64-renpy> \
    [--output PATH] [--force] [--dry-run] \
    [--allow-version-mismatch] [--json]
```

Default output: `<source-parent>/<source-name>-frame`.

`--runtime` is required (enforced by the builder; no auto-download yet).

## Exit codes

- `0` success / likely compatible (inspect) / successful build
- `1` tool error
- `2` invalid / non-Ren'Py game
- `3` compatibility issue

## Notes

`main(argv=None)` is import-safe for unit tests.

# CLI.md

Equivalent script: `renframe/cli.py`

## Purpose

Argparse entrypoint for the `renframe` console command.

## Commands

- `renframe inspect <directory> [--json]`
- `renframe build <directory> [--output PATH] [--runtime PATH] [--force]` (stub)

## Exit codes

- `0` success / likely compatible
- `1` tool error
- `2` invalid / non-Ren'Py game
- `3` compatibility issue

## Notes

`main(argv=None)` is import-safe for unit tests.

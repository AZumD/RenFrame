# FIXTURES.md

Equivalent script: `tests/fixtures.py`

## Purpose

Shared fake Ren'Py game and ARM/x86 runtime trees for unit tests. No
copyrighted game content.

## Helpers

- `write_elf(path, machine)` — minimal ELF header
- `make_game(...)` — fake distributed x86-style Ren'Py game
- `make_runtime(...)` — fake SDK/runtime (`aarch64` or `x86_64`)

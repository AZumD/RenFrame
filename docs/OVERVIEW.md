# RenFrame Overview

RenFrame helps move Ren'Py visual novels from x86_64 desktop distributions onto native Linux ARM64 (Steam Frame) by **replacing the Ren'Py runtime**, not by emulating game binaries.

## Current state

Milestone 1 focuses on the inspection layer:

| Area | Status |
|------|--------|
| CLI skeleton (`inspect`, stub `build`) | Done |
| Ren'Py directory detection | Done |
| Version / generation detection | Done |
| Native dependency + ELF scanning | Done |
| Human + JSON reports | Done |
| Unit tests | Done |
| ARM runtime install / cache | Stub only |
| `renframe build` output tree + launcher | Not started |

## Compatibility verdicts

- `LIKELY_COMPATIBLE` — Ren'Py game with known 7/8 generation and no game-owned incompatible natives
- `NEEDS_TESTING` — plausible, but soft risks remain (e.g. Ren'Py 7.x runtime matching)
- `INCOMPATIBLE_NATIVE_CODE` — game-owned x86/Windows native modules under `game/`
- `UNKNOWN_RENPY_VERSION` — looks like Ren'Py, version/generation unclear
- `NOT_A_RENPY_GAME` — layout does not match Ren'Py

Stock x86 files under `lib/` / `renpy/` are expected and are **not** treated as blockers.

## Next milestone

Implement `renframe build`:

1. Validate source via inspection
2. Accept a user-supplied ARM64 Ren'Py SDK (`--runtime`)
3. Copy game data into a new output directory
4. Attach ARM64 runtime files
5. Generate a Linux launcher script
6. Enforce output path safety (`--force`, no source mutation)

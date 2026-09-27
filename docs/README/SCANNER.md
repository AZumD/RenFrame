# SCANNER.md

Equivalent script: `renframe/scanner.py`

## Purpose

Find native/binary artifacts and classify ARM64 compatibility.

## Recognized extensions

`.so`, `.dll`, `.exe`, `.pyd` (plus versioned `.so.*`)

## Ownership

- **runtime** — under `renpy/`, `lib/`, or top-level launcher wrappers
- **game** — primarily under `game/` (and other non-runtime paths)

Runtime x86 libraries are expected and do not alone mark a game incompatible.

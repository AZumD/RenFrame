# DETECTOR.md

Equivalent script: `renframe/detector.py`

## Purpose

Recognize Ren'Py game layouts and gather version hints.

## Key functions

- `looks_like_renpy_game(path)` — layout heuristics (`game/`, `renpy/`, scripts, launchers)
- `collect_version_hints(path)` — runs modular strategies
- `select_best_version(hints)` — confidence-ranked pick

## Version strategies

1. `renpy/versions.py`
2. `renpy/__init__.py`
3. `game/script_version*.txt` / similar
4. Top-level `.sh` launcher strings
5. `lib/py3-*` vs `lib/py2-*` generation inference

Distinguishes Ren'Py **7.x** (Python 2 era) from **8.x** (Python 3).

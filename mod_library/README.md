# RenFrame Mod Library

This directory is the machine-readable side of RenFrame's mod-library research. It is intentionally boring data: one JSON file per game and one JSON file per mod, plus a generated `catalog.json` index.

The maintainer-facing **RenFrame Library Manager** is the preferred way to edit these files:

```bash
pip install -e .
renframe-library
```

You can also run it directly from a checkout:

```bash
python -m renframe.library_manager
```

## Manager workflow

1. Choose **Mods** or **Games** in the sidebar. Existing records are searchable and editable.
2. Add a game manually, or point the game editor at a clean Ren'Py directory to seed launcher/path/hash fingerprint evidence.
3. Add a mod, select its game, and provide the upstream source/download URL.
4. Optionally choose a downloaded ZIP/RPA/folder. For RAR/7z packages, extract them first and select the folder. The manager inspects it and suggests one of the common install shapes:
   - single RPA → `game/`
   - packaged `game/` → merge into `game/`
   - archive contents → `game/`
   - full archive → game-root overlay
5. Review the generated install operations and flags. Packages touching `lib/`, `renpy/`, `update/`, or native binaries are marked runtime-sensitive; executable/script entries are surfaced for review.
6. Click **Update library**. The manager writes the JSON record, regenerates `catalog.json`, and validates the whole library.
7. Use **Git diff** to review what changed. Commit and push normally when satisfied.

The manager never commits or pushes on its own.

## Safety model

Only declarative operations are accepted: `copy_file`, `copy_tree`, `overlay_archive`, `delete`, `rename`, `mkdir`, `verify_exists`, and `verify_missing`. Relative paths are validated and archive traversal such as `../` is rejected. Arbitrary shell/Python/PowerShell/batch installer hooks are not part of the schema.

A SHA-256 generated from a locally inspected package is useful provenance, but it does not prove the package is trustworthy. Prefer author-maintained upstream sources and keep redistribution link-only when licensing is unclear.

## Status

The current JSON files are seed records transcribed from `docs/MOD_LIBRARY.md`. Low-confidence research candidates intentionally have empty/custom install rules rather than guessed automation.

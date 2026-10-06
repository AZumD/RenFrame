# RenFrame Mod Library Research

> **Status:** research catalog, not yet an automated package database  
> **Last reviewed:** 2026-10-06  
> **Scope:** Ren'Py games and mods that may be useful to RenFrame's future optional mod-patching flow

RenFrame currently converts Ren'Py PC builds into Linux ARM64 packages. This document is the seed for a future mod library: after RenFrame identifies a game, it could offer compatible upstream mods and apply safe, declarative file operations to the temporary working copy before the ARM64 runtime conversion.

This is deliberately a **link-and-metadata catalog**, not a mirror of third-party mod files. RenFrame should prefer downloading from the mod author's official release/source at conversion time. Do not bundle third-party game assets or mod archives unless their license and redistribution terms clearly permit it.

## Ground rules

1. **Upstream is authoritative.** Installation, compatibility, licensing, and version claims must be backed by the author's repository, release page, or official project page.
2. **Never modify the user's source copy.** Apply mods only to RenFrame's temporary working copy.
3. **Prefer declarative file operations.** Copy, overlay, delete, rename, mkdir, and verification are reasonable. RenFrame should not execute arbitrary shell scripts, Python installers, EXEs, or other third-party installer code just because a catalog entry asks it to.
4. **Re-inspect after patching.** A mod can replace `lib/`, launchers, update code, or other runtime-sensitive files. RenFrame must inspect the patched tree again before choosing/installing the ARM64 Ren'Py runtime.
5. **Verify downloads.** A future machine-readable catalog should pin release/tag plus SHA-256 where possible. Do not fabricate hashes. Collect them from release metadata or verified downloads.
6. **Conflicts are first-class data.** Large DDLC character/route mods are often complete transformations and should generally be treated as mutually exclusive unless upstream explicitly says otherwise.
7. **Link-only by default.** When redistribution rights are unclear or restrictive, RenFrame may point to/fetch the official upstream artifact for the user but should not re-host it.

## Status and confidence taxonomy

### Maintenance status

| Status | Meaning |
|---|---|
| **Active** | Recent releases or development activity; project appears currently maintained. |
| **Maintained** | Still usable and supported, but releases may be infrequent. |
| **Stale** | No recent maintenance signal; may still work on the documented target. |
| **Archived** | Upstream repository is archived/read-only or project declares a final release. |
| **Unknown** | Not enough evidence to classify safely. |

### Automation confidence

| Confidence | Meaning |
|---|---|
| **High** | Official instructions map cleanly to safe file operations and target matching is understood. |
| **Medium** | Install is automatable, but archive layout, version matching, or verification still needs a fixture/test. |
| **Low** | Important details are ambiguous, installer-driven, or insufficiently documented. Keep as research only. |

## Seed catalog

| Mod | Scope / target | Type | Status | Automation confidence | Runtime-sensitive? |
|---|---|---|---|---|---|
| Universal Ren'Py Mod (URM) | Most Ren'Py games | Utility / debugging / choice inspection | Maintained | High | No known runtime replacement |
| Universal Ren'Py Walkthrough | Ren'Py games | Walkthrough / choice consequence UI | Active | High | No known runtime replacement |
| Neuro Ren'Py Implementation | Most standard Ren'Py games | Accessibility / external-control integration | Active | High | Python/package compatibility should be rechecked |
| Monika After Story | Doki Doki Literature Club | Transformation / character-after-story | Active | Medium | Yes, treat as full transformation |
| Just Natsuki | Doki Doki Literature Club | Transformation / character-after-story | Maintained | High | **Yes: installs `lib/` and `update/`** |
| Forever & Ever | Doki Doki Literature Club | Transformation / character-after-story | Archived | High for file ops, low for support | Yes, full transformation |
| DDLC: The Normal Visual Novel! | Doki Doki Literature Club | Story transformation | Archived | Medium | Potentially |
| Chronology Mod | Ren'Py game(s), exact target still to document | Utility / chronology | Active/Unknown | Low | Unknown |
| The Clown Mod | Slay the Princess | Game-specific content mod | Active/Unknown | Low | Unknown |
| Katawa Shoujo HD Upscale | Katawa Shoujo | Visual / resolution overhaul | Unknown | Low | Likely, project includes engine/runtime files |

The first seven entries are the best current candidates for a v1 document-backed library. The final three are useful research leads but should **not** become one-click options until their target/version/install semantics are verified.

---

## Universal mods

### Universal Ren'Py Mod (URM)

- **Author/source:** 0x52
- **Official page:** https://0x52.dev/mods/Universal-Ren-Py-Mod-1000
- **Type:** utility, variable inspection/editing, scene/choice/path tools, save management
- **Target:** most Ren'Py games
- **Documented engine compatibility:** Ren'Py 6.99.14 and later; the author's release history also documents Ren'Py 8 compatibility
- **Maintenance:** Maintained
- **Automation confidence:** High
- **Redistribution:** not assumed. Prefer official-source download/linking.

The author's site describes URM as supporting almost any Ren'Py game and explicitly emphasizes an approach that does not modify original game files. Public installation references consistently describe extracting the download and placing the URM `.rpa` file in the game's `game/` directory.

**Published install shape**

```text
download official URM archive
extract 0x52_URM.rpa
copy -> <game-root>/game/0x52_URM.rpa
```

**RenFrame application**

- Safe operation: `copy_file` into `game/`.
- No reason to run an installer.
- Verify that the expected `.rpa` exists after copy.
- Universal matching should still require a confirmed Ren'Py game and a compatible detected engine version.
- The catalog should resolve the current stable release from the official page rather than relying on stale search-engine version snapshots.

**Evidence**

- Official project page: https://0x52.dev/mods/Universal-Ren-Py-Mod-1000
- Author overview and design notes: https://0x52.dev/

---

### Universal Ren'Py Walkthrough

- **Repository:** https://github.com/BCassO/universal-renpy-walkthrough
- **Releases:** https://github.com/BCassO/universal-renpy-walkthrough/releases
- **Type:** walkthrough / automatic choice-consequence analysis
- **Target:** Ren'Py games
- **Latest observed release:** v2.0.1, released 2026-06-27
- **Maintenance:** Active
- **Automation confidence:** High
- **License:** MIT

The official installation guide says to copy the entire `__urw` directory into the target game's `game/` directory. The v2.0.1 release includes an in-game updater, dynamic text resizing, and choice-menu changes.

**Published install shape**

```text
<game-root>/
  game/
    __urw/
      urw_core.rpy
      urw_processor.rpy
      urw_screens.rpy
      urw_utils.rpy
      ...
```

**RenFrame application**

- Safe operation: `copy_tree` of release `__urw/` to `game/__urw/`.
- Verify the core files exist after install.
- Do not invoke the mod's updater during conversion.
- Because this injects `.rpy` files, RenFrame should test against representative Ren'Py 7 and 8 games before advertising broad compatibility.
- A future catalog entry should pin a release asset/tag and checksum.

**Evidence**

- Installation guide: https://github.com/BCassO/universal-renpy-walkthrough/blob/main/installation.md
- Changelog: https://github.com/BCassO/universal-renpy-walkthrough/blob/main/CHANGELOG.md
- License: https://github.com/BCassO/universal-renpy-walkthrough/blob/main/LICENSE

---

### Neuro Ren'Py Implementation

- **Repository:** https://github.com/caheuer/neuro-renpy-implementation
- **Releases:** https://github.com/caheuer/neuro-renpy-implementation/releases
- **Type:** Neuro Game API integration / external control / context
- **Target:** almost all standard Ren'Py games, with game-specific limitations
- **Latest release observed during research:** v0.2.0
- **Maintenance:** Active
- **Automation confidence:** High for file installation; compatibility remains game-dependent
- **License:** MIT for project code, with bundled third-party components under their own licenses

Upstream says to download the general release or a game-specific integration, extract it, copy the contents into the game's `game/` directory, and edit `neuroconfig.py`. Upstream specifically reports testing on DDLC, Milk Inside a Bag of Milk Inside a Bag of Milk, and Slay the Princess: The Pristine Cut. It also notes that the integration is desktop-only because of its WebSocket dependency.

**Published install shape**

```text
download official release
extract
copy release contents -> <game-root>/game/
optionally configure game/neuroconfig.py
```

**RenFrame application**

- Safe operation: overlay release contents into `game/`.
- Prefer the general release unless a catalog entry explicitly matches a tested game-specific package.
- Configuration should be opt-in UI/data, not an arbitrary post-install script.
- Re-inspect after installation because bundled Python modules can interact with the game's Python/Ren'Py generation.
- Verification should check for the integration's expected entry files and `neuroconfig.py`.

**Evidence**

- README/install/testing notes: https://github.com/caheuer/neuro-renpy-implementation
- License: https://github.com/caheuer/neuro-renpy-implementation/blob/main/LICENSE

---

## Doki Doki Literature Club ecosystem

DDLC has one of the largest open Ren'Py mod ecosystems, but it also demonstrates why RenFrame needs careful matching. Several popular mods are not small add-ons. They replace major portions of the game and may ship their own `lib/`, `update/`, launcher, or script archives.

For RenFrame, these should be treated as **transformations**, not stackable plugins.

### Base-game identification notes

A future DDLC fingerprint should use multiple signals rather than the folder name alone:

- known launcher names and base layout
- presence of characteristic archives/files such as `game/scripts.rpa`
- Ren'Py version/runtime layout
- file sizes and cryptographic hashes from verified clean DDLC builds
- mod-specific absence/presence markers

**Do not add hashes to the catalog until they have been collected from verified clean builds.** Hashes themselves are fine to store; copyrighted game assets are not.

DDLC+ is a different product and is explicitly unsupported by several of the mods below. It must not match the original DDLC fingerprint.

### Conflict policy

Until upstream evidence proves otherwise, treat these transformation mods as mutually exclusive:

- Monika After Story
- Just Natsuki
- Forever & Ever
- DDLC: The Normal Visual Novel!

A RenFrame UI should present them as "replace/transform the base game" choices, not ordinary checkboxes that can all be enabled at once.

---

### Monika After Story (MAS)

- **Repository:** https://github.com/Monika-After-Story/MonikaModDev
- **Releases:** https://github.com/Monika-After-Story/MonikaModDev/releases
- **Target:** original Doki Doki Literature Club
- **Type:** transformation / persistent character-after-story
- **Latest observed release:** v0.12.19, released 2026-09-07
- **Maintenance:** Active
- **Automation confidence:** Medium
- **Redistribution:** do not assume redistribution rights; use official releases

The current README recommends OS-specific installers but provides a manual ZIP path when the installer cannot be used. The manual method says to use a release ZIP and extract it into the DDLC installation. The FAQ further stresses using a fresh/unaltered DDLC copy and warns that repository source files are development files, not release packages.

This is a strong fit for RenFrame's **manual-release equivalent**, not for running the upstream installer.

**RenFrame application**

- Source must be an official release ZIP, never the GitHub source archive.
- Apply only to a verified clean/original DDLC working copy.
- Inspect the selected release ZIP's top-level layout before encoding the exact overlay rule. Upstream documentation has changed over time and currently describes both base-directory extraction and placement of release contents under `game/` depending on package context.
- Treat MAS as conflicting with other DDLC transformation mods.
- Re-inspect the game after overlay before ARM64 conversion.
- Preserve user saves/persistent data outside the converted game tree. RenFrame should not delete persistent data.

**Evidence**

- README/manual install: https://github.com/Monika-After-Story/MonikaModDev
- FAQ: https://github.com/Monika-After-Story/MonikaModDev/blob/master/FAQ.md
- Releases: https://github.com/Monika-After-Story/MonikaModDev/releases

**Open work before automation**

- Record the exact current release asset name(s) and archive root layout.
- Verify whether any shipped native modules require special ARM64 handling.
- Collect clean-DDLC fingerprint hashes and post-install verification markers.

---

### Just Natsuki

- **Repository:** https://github.com/Just-Natsuki-Team/NatsukiModDev
- **Releases:** https://github.com/Just-Natsuki-Team/NatsukiModDev/releases
- **Target:** original Doki Doki Literature Club; upstream explicitly says DDLC+ is unsupported
- **Type:** transformation / persistent character-after-story
- **Latest observed release:** v1.3.5, released 2025-05-01
- **Maintenance:** Maintained
- **Automation confidence:** High for the documented manual path
- **Runtime-sensitive:** **Yes**

Upstream recommends its installer, but also documents a manual installation. The manual path requires a fresh DDLC copy, then:

1. copy all contents of the mod's `game/` into DDLC's `game/`;
2. copy all contents of the mod's `lib/` into DDLC's `lib/`;
3. copy the mod's `update/` directory into the DDLC root.

That `lib/` replacement is exactly why mod application must happen **before** RenFrame makes its final ARM64 runtime decision.

**RenFrame application**

```text
overlay <mod>/game/*   -> <game-root>/game/
overlay <mod>/lib/*    -> <game-root>/lib/
copy    <mod>/update/  -> <game-root>/update/
re-inspect
perform ARM64 conversion
```

- Do not run the official installer inside RenFrame.
- Use only the official release ZIP beginning with the documented `jn-...` naming pattern, not the source-code archive.
- Treat as mutually exclusive with other DDLC transformation mods.
- Fail closed if expected `game/` and `lib/` roots are absent from the release archive.

**Evidence**

- Official README/manual installation: https://github.com/Just-Natsuki-Team/NatsukiModDev
- Release v1.3.5 and release history: https://github.com/Just-Natsuki-Team/NatsukiModDev/releases
- Official installer project, useful as reference but not something RenFrame should execute: https://github.com/Just-Natsuki-Team/NatsukiModInstaller

---

### Forever & Ever

- **Repository:** https://github.com/ForeverAndEverTeam/fae-mod
- **Releases:** https://github.com/ForeverAndEverTeam/fae-mod/releases
- **Target:** original Doki Doki Literature Club; DDLC+ unsupported
- **Type:** transformation / Sayori character-after-story
- **Final release:** V1.0, "The Curtain Call"
- **Maintenance:** Archived; repository archived 2023-09-08
- **Automation confidence:** High for file operations, low for ongoing support
- **Redistribution:** **link-only is safest**

Upstream's documented fresh install uses a fresh non-Steam copy of original DDLC, overlays the release files onto the DDLC folder, then deletes `game/scripts.rpa`. The project explicitly says mod-management installations are not officially supported. Its README also contains restrictive content-reuse language, while its LICENSE grants MIT-style terms to specified code and notes separate ownership/terms for other assets. Because the package mixes code and creative assets, RenFrame should not mirror or bundle the release.

**RenFrame application**

```text
overlay official release -> <game-root>/
delete <game-root>/game/scripts.rpa
verify expected FAE launcher/content markers
re-inspect
perform ARM64 conversion
```

- Show an "Archived / final release" badge.
- Use only the official upstream release.
- Do not redistribute the archive with RenFrame.
- Treat as mutually exclusive with other DDLC transformations.
- The project's statement that mod managers are unsupported should be visible in the catalog notes. RenFrame support would be community-maintained, not upstream-supported.

**Evidence**

- README/install/compatibility notice: https://github.com/ForeverAndEverTeam/fae-mod
- Releases/final release: https://github.com/ForeverAndEverTeam/fae-mod/releases
- License: https://github.com/ForeverAndEverTeam/fae-mod/blob/master/LICENSE

---

### Doki Doki Literature Club: The Normal Visual Novel!

- **Repository:** https://github.com/Skull220/DDLCtVN
- **Releases:** https://github.com/Skull220/DDLCtVN/releases
- **Target:** Doki Doki Literature Club
- **Type:** story transformation
- **Latest release:** 1.5.0, released 2018-09-09
- **Maintenance:** Archived; repository archived 2025-10-04
- **Automation confidence:** Medium
- **Redistribution:** not established; link to official release only

The 1.5 release says to download `ddlctvn.zip`, then copy the included `mod_assets` directory and `script.rpa` into the DDLC installation, overwriting existing files.

The release wording does not make the exact destination path sufficiently explicit for a zero-risk automated installer. Before this becomes a one-click RenFrame option, inspect the release archive and test a clean DDLC fixture to determine whether those objects are expected at the DDLC root or under `game/`.

**RenFrame application**

- Keep disabled-by-default in any automated catalog until archive layout is verified.
- Once verified, encode exact `copy_tree` / `copy_file` operations.
- Never infer the destination from filename alone.
- Treat as mutually exclusive with other DDLC transformations.

**Evidence**

- Release 1.5.0 installation text: https://github.com/Skull220/DDLCtVN/releases

---

## Additional research candidates

These projects are worth tracking, but they need another verification pass before RenFrame should offer them automatically.

### Chronology Mod

- **Repository:** https://github.com/cantunborn/renpy-chronology-mod
- **Releases:** https://github.com/cantunborn/renpy-chronology-mod/releases
- **Observed release channels:** `stable`, `stable-imperial-chronicles`, `stable-shutupanddance`
- **Status:** appears actively released in 2026
- **Confidence:** Low

The release automation is healthy enough to keep on the research list, but the exact supported games, install target, and conflict behavior need to be documented from upstream before creating a RenFrame rule.

### The Clown Mod

- **Repository:** https://github.com/manosrules/The-Clown-Mod
- **Target:** Slay the Princess
- **Observed release:** `demo_clown` in 2026
- **Status:** Active/Unknown
- **Confidence:** Low

This is a useful Slay the Princess ecosystem lead. Before automation, verify the official release/archive layout, supported Slay the Princess version, install instructions, and whether it changes engine/runtime files.

### Katawa Shoujo HD Upscale

- **Repository:** https://github.com/scoopgoop/Katawa-Shoujo-HD-Upscale
- **Target:** Katawa Shoujo
- **Type:** visual/resolution overhaul
- **Status:** Unknown
- **Confidence:** Low

The repository describes a 1080p upscale and contains files such as `renpy.code` and Python/runtime DLLs, which suggests it is not a simple `game/` overlay. This makes it interesting for RenFrame research but a poor candidate for blind automation. It needs exact install documentation and a clear separation between game content and legacy runtime components.

---

## Matching and fingerprint evidence

The future library should identify the **base game first**, then evaluate compatible mods. A display name alone is not enough.

A useful fingerprint record can combine:

```text
engine: renpy
canonical_game_id: ddlc-original
display_name: Doki Doki Literature Club
signals:
  launcher_names: [...]
  required_paths: [...]
  forbidden_paths: [...]
  renpy_version: ...
  file_hashes:
    - path: game/scripts.rpa
      sha256: <verified-clean-build hash>
confidence: exact | strong | weak
```

Recommended evidence order:

1. **Exact cryptographic hashes** of stable canonical files from verified clean builds.
2. Characteristic required/forbidden file sets.
3. Launcher/build names.
4. Ren'Py version and Python generation.
5. Human-readable game metadata when available.

Do not use a single `config.name` string or folder name as an exact match. Ren'Py games are easy to rename, and transformed mods may retain some base-game metadata.

### Hash collection policy

- Hashes must come from legally obtained, verified clean builds.
- Store only hashes, sizes, version identifiers, and path metadata, never proprietary game files.
- Keep separate fingerprints for materially different storefront/build versions where needed.
- Record provenance for every hash: game version, storefront/source, platform build, date collected.
- If no trustworthy hash exists, use a lower-confidence match and require user confirmation.

---

## How RenFrame should apply a catalog entry

This document is not the machine-readable format, but every automatable entry should eventually reduce to a small whitelist of operations:

- `copy_file`
- `copy_tree`
- `overlay_archive`
- `delete`
- `rename`
- `mkdir`
- `verify_exists`
- `verify_missing`

Potential later additions, only when there is a strong need and test coverage:

- `text_patch`
- `binary_patch`
- `rpa_extract` / `rpa_create`

A manifest should **not** contain `run:`, arbitrary shell commands, PowerShell, batch files, Python snippets, or executable installer hooks. If upstream only supports an installer, the catalog should either model the installer's safe file effects from documented evidence or mark the mod as manual-only.

### Safe extraction requirements

Any future downloader/installer must reject:

- absolute archive paths
- `..` path traversal
- files resolving outside the temporary game root
- symlinks/hardlinks escaping the temporary root
- unexpected device/special files

Apply changes transactionally to the temporary working copy. If verification fails, stop conversion rather than producing a half-modded build.

---

## Suggested future machine-readable fields

When this document graduates into data, a mod record will probably need at least:

```text
schema_version
id
name
author
homepage
kind
scope
maintenance_status
game_match
engine_compatibility
source
release
asset
sha256
install_steps
verify_steps
conflicts
requires
runtime_sensitive
license
redistribution
notes
evidence
last_verified
```

The catalog should be data-first so RenFrame can eventually support other engines without rebuilding the whole concept. A future record could use `engine: renpy` today and `engine: rpgmaker-mv`, `rpgmaker-mz`, or `godot` later, with engine-specific patch backends.

---

## Recommended first implementation set

If/when RenFrame moves from this document to code, start with the smallest, best-evidenced operations:

1. **Universal Ren'Py Mod**: single-file copy into `game/`.
2. **Universal Ren'Py Walkthrough**: copy one directory into `game/`.
3. **Neuro Ren'Py Implementation**: overlay into `game/` with explicit configuration.
4. **Just Natsuki**: first runtime-sensitive integration, useful for proving the "mod, then re-inspect, then ARM64-convert" pipeline.
5. **Forever & Ever**: proves overlay + delete and archived/link-only metadata.
6. **Monika After Story**: add after current release archive layout has a fixture test.
7. **DDLCtVN**: add only after its ambiguous release destination is verified.

This sequence deliberately starts with operations RenFrame can model without executing untrusted installers.

---

## How to contribute or update this document

When adding or changing an entry:

1. Link the **official upstream source**.
2. Record the date you verified it.
3. Prefer a release page and the author's installation documentation over forum reposts.
4. Quote as little as possible; summarize instructions and link the source.
5. State the supported game/version only when upstream documents it or RenFrame has a reproducible test.
6. Mark uncertainty explicitly. "Unknown" is better than a confident guess.
7. Do not add hashes unless you know exactly which clean game/mod artifact they identify.
8. Note whether the mod changes `lib/`, `renpy/`, launchers, native libraries, Python packages, or update code.
9. Note conflicts and prerequisites.
10. Record licensing/redistribution terms. If unclear, assume **link-only**.
11. For an automated candidate, describe the install as safe file operations and add a fixture/test plan.
12. Re-check stale entries periodically and when upstream publishes a new release.

Suggested review cadence:

- **Active projects:** check on each RenFrame release or every 2 to 3 months.
- **Maintained projects:** check every 6 months.
- **Archived/final projects:** re-check only when RenFrame's installer behavior changes or a fork/successor appears.
- **Unknown candidates:** promote only after someone completes the missing evidence.

---

## Research notes and limitations

This catalog was seeded from upstream GitHub repositories, release pages, official project pages, and project-authored installation documentation available on 2026-10-06.

It is intentionally conservative. A mod appearing here does **not** mean RenFrame currently supports it, that upstream supports RenFrame, or that combining it with an ARM64 runtime swap has been tested. The automation-confidence field is about how well the published installation can be represented as safe file operations, not a guarantee that the resulting game runs correctly on ARM64.

The next useful research pass is not "find hundreds more mods." It is:

- verify archive layouts for the medium-confidence entries;
- collect clean-game fingerprints without redistributing game assets;
- build tiny synthetic fixture archives that mimic install layouts;
- document native/Python dependencies that may fail on ARM64;
- expand beyond DDLC into other Ren'Py ecosystems only when there is enough upstream evidence to maintain the entry responsibly.

That keeps the library boring in the best possible way: reproducible, reviewable, and difficult to turn into a malware delivery mechanism.

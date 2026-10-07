"""Detection for non-Ren'Py engines and known cross-engine editions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ForeignEngineDetection:
    """A confident signal that the selected game uses another engine."""

    engine: str
    evidence: tuple[str, ...]
    known_edition: str | None = None
    advice: str | None = None


@dataclass(frozen=True)
class _KnownEdition:
    name: str
    aliases: tuple[str, ...]
    engine: str
    advice: str


_KNOWN_EDITIONS: tuple[_KnownEdition, ...] = (
    _KnownEdition(
        name="Doki Doki Literature Club Plus!",
        aliases=(
            "doki doki literature club plus",
            "ddlc plus",
            "ddlcplus",
        ),
        engine="Unity",
        advice=(
            "DDLC Plus is a Unity reimplementation, not the original Ren'Py build. "
            "RenFrame supports the original Doki Doki Literature Club PC release; "
            "use that edition instead of Plus."
        ),
    ),
    _KnownEdition(
        name="OneShot: World Machine Edition",
        aliases=(
            "oneshot world machine edition",
            "oneshot wme",
            "world machine edition",
            "oneshotmg",
        ),
        engine="MonoGame / XNA",
        advice=(
            "OneShot: World Machine Edition was rebuilt on MonoGame/XNA. "
            "The earlier PC OneShot release is an RPG Maker title, so neither edition "
            "is a Ren'Py target for RenFrame."
        ),
    ),
    _KnownEdition(
        name="To the Moon (Unity remake/port)",
        aliases=(
            "to the moon",
            "tothemoon",
        ),
        engine="Unity",
        advice=(
            "This appears to be the Unity remake/port of To the Moon. "
            "The original PC release is an RPG Maker XP title, not Ren'Py."
        ),
    ),
)


def _normalize_identity(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _known_edition(root: Path, engine: str) -> _KnownEdition | None:
    names = [root.name]
    try:
        names.extend(p.name for p in root.iterdir())
    except OSError:
        pass
    identity = " ".join(_normalize_identity(name) for name in names)
    for edition in _KNOWN_EDITIONS:
        if edition.engine != engine:
            continue
        if any(_normalize_identity(alias) in identity for alias in edition.aliases):
            return edition
    return None


def _with_known_edition(
    root: Path,
    engine: str,
    evidence: list[str],
) -> ForeignEngineDetection:
    known = _known_edition(root, engine)
    return ForeignEngineDetection(
        engine=engine,
        evidence=tuple(evidence),
        known_edition=known.name if known else None,
        advice=known.advice if known else None,
    )


def detect_foreign_engine(root: Path) -> ForeignEngineDetection | None:
    """Detect common non-Ren'Py runtimes from strong filesystem markers."""
    if not root.is_dir():
        return None

    try:
        children = list(root.iterdir())
    except OSError:
        return None

    by_name = {p.name.lower(): p for p in children}

    # Unity desktop builds normally ship UnityPlayer.dll and/or a <Game>_Data
    # directory containing globalgamemanagers, resources.assets, or Assembly-CSharp.
    unity_evidence: list[str] = []
    for marker in ("unityplayer.dll", "gameassembly.dll"):
        if marker in by_name and by_name[marker].is_file():
            unity_evidence.append(_relative(root, by_name[marker]))

    data_dirs = [
        p for p in children
        if p.is_dir() and p.name.lower().endswith("_data")
    ]
    for data_dir in data_dirs:
        for marker in (
            data_dir / "globalgamemanagers",
            data_dir / "resources.assets",
            data_dir / "Managed" / "Assembly-CSharp.dll",
        ):
            if marker.exists():
                unity_evidence.append(_relative(root, marker))
                break

    if unity_evidence and (data_dirs or "unityplayer.dll" in by_name):
        return _with_known_edition(root, "Unity", unity_evidence)

    # FNA / MonoGame / legacy XNA managed assemblies are very distinctive.
    managed_names = {
        p.name.lower(): p
        for p in children
        if p.is_file() and p.suffix.lower() == ".dll"
    }
    monogame_evidence: list[str] = []
    for name, path in managed_names.items():
        if (
            name.startswith("monogame.framework")
            or name == "fna.dll"
            or name.startswith("microsoft.xna.framework")
        ):
            monogame_evidence.append(_relative(root, path))
    if monogame_evidence:
        return _with_known_edition(root, "MonoGame / XNA", monogame_evidence)

    # RPG Maker 2000/2003.
    if "rpg_rt.exe" in by_name and (
        "rpg_rt.ldb" in by_name or "rpg_rt.lmt" in by_name
    ):
        evidence = [_relative(root, by_name["rpg_rt.exe"])]
        return _with_known_edition(root, "RPG Maker 2000/2003", evidence)

    # RPG Maker XP/VX/VX Ace.
    game_ini = by_name.get("game.ini")
    rgss = [p for p in children if p.is_file() and p.name.lower().startswith("game.rgss")]
    if game_ini and game_ini.is_file() and rgss:
        evidence = [_relative(root, game_ini), _relative(root, rgss[0])]
        return _with_known_edition(root, "RPG Maker XP/VX/VX Ace", evidence)

    # RPG Maker MV/MZ. Some distributions place js/ at root, others under www/.
    for base in (root, root / "www"):
        js = base / "js"
        if not js.is_dir():
            continue
        for marker in ("rpg_core.js", "rmmz_core.js"):
            candidate = js / marker
            if candidate.is_file():
                engine = "RPG Maker MZ" if marker.startswith("rmmz") else "RPG Maker MV"
                return _with_known_edition(root, engine, [_relative(root, candidate)])

    # Godot desktop exports commonly keep the game pack beside the executable.
    pcks = [p for p in children if p.is_file() and p.suffix.lower() == ".pck"]
    if pcks:
        return _with_known_edition(root, "Godot", [_relative(root, pcks[0])])

    # Unreal packaged games normally expose Engine/ plus Content/Paks/.
    engine_dir = root / "Engine"
    paks_dir = root / "Content" / "Paks"
    if engine_dir.is_dir() and paks_dir.is_dir() and any(paks_dir.glob("*.pak")):
        return _with_known_edition(
            root,
            "Unreal Engine",
            [_relative(root, engine_dir), _relative(root, paks_dir)],
        )

    # Generic NW.js/web-runtime package. Keep this last so RPG Maker MV/MZ wins.
    if "package.json" in by_name and (
        "nw.dll" in by_name
        or "nw.exe" in by_name
        or "nw_elf.dll" in by_name
    ):
        evidence = [_relative(root, by_name["package.json"])]
        return _with_known_edition(root, "NW.js / web runtime", evidence)

    return None


def format_foreign_engine_error(
    root: Path,
    detection: ForeignEngineDetection,
) -> str:
    """Return a user-facing wrong-engine error with edition-specific advice."""
    if detection.known_edition:
        lead = (
            f"{detection.known_edition} detected ({detection.engine}), "
            "not a Ren'Py build."
        )
    else:
        lead = f"Detected {detection.engine}, not Ren'Py."

    lines = [lead]
    if detection.advice:
        lines.append(detection.advice)
    else:
        lines.append(
            "RenFrame only converts Ren'Py builds. This may be a remake, port, "
            "or special edition that uses a different engine than the original game."
        )
    if detection.evidence:
        lines.append("Detected from: " + ", ".join(detection.evidence[:3]))
    return "\n".join(lines)

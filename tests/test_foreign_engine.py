"""Tests for foreign-engine and cross-engine edition guardrails."""

from __future__ import annotations

from pathlib import Path

import pytest

from renframe.foreign_engine import (
    detect_foreign_engine,
    format_foreign_engine_error,
)
from renframe.inspect_service import inspect_game
from renframe.models import Compatibility
from renpy_arm.convert import ConvertError, resolve_input


def _make_unity(root: Path, *, data_name: str | None = None) -> Path:
    root.mkdir(parents=True)
    (root / "UnityPlayer.dll").write_bytes(b"fake")
    data = root / (data_name or f"{root.name}_Data")
    data.mkdir()
    (data / "globalgamemanagers").write_bytes(b"fake")
    return root


def test_detects_ddlc_plus_as_unity_with_specific_advice(tmp_path: Path) -> None:
    game = _make_unity(
        tmp_path / "Doki Doki Literature Club Plus",
        data_name="Doki Doki Literature Club Plus_Data",
    )
    detection = detect_foreign_engine(game)

    assert detection is not None
    assert detection.engine == "Unity"
    assert detection.known_edition == "Doki Doki Literature Club Plus!"

    message = format_foreign_engine_error(game, detection)
    assert "not a Ren'Py build" in message
    assert "original Doki Doki Literature Club PC release" in message


def test_detects_oneshot_world_machine_as_monogame(tmp_path: Path) -> None:
    game = tmp_path / "OneShot World Machine Edition"
    game.mkdir()
    (game / "MonoGame.Framework.dll").write_bytes(b"fake")

    detection = detect_foreign_engine(game)

    assert detection is not None
    assert detection.engine == "MonoGame / XNA"
    assert detection.known_edition == "OneShot: World Machine Edition"
    assert "RPG Maker" in (detection.advice or "")


def test_detects_rpg_maker_mv(tmp_path: Path) -> None:
    game = tmp_path / "SomeRpg"
    js = game / "www" / "js"
    js.mkdir(parents=True)
    (js / "rpg_core.js").write_text("// fake", encoding="utf-8")

    detection = detect_foreign_engine(game)

    assert detection is not None
    assert detection.engine == "RPG Maker MV"


def test_inspect_surfaces_foreign_engine(tmp_path: Path) -> None:
    game = _make_unity(tmp_path / "UnityGame")

    result = inspect_game(game)

    assert result.compatibility == Compatibility.NOT_A_RENPY_GAME
    assert result.foreign_engine == "Unity"
    assert result.foreign_engine_evidence
    assert any("Detected Unity" in issue for issue in result.potential_issues)


def test_resolve_input_rejects_known_wrong_edition_early(tmp_path: Path) -> None:
    game = _make_unity(tmp_path / "DDLC Plus", data_name="DDLC Plus_Data")
    work = tmp_path / "work"
    work.mkdir()

    with pytest.raises(ConvertError) as exc:
        resolve_input(game, work)

    message = str(exc.value)
    assert "Doki Doki Literature Club Plus!" in message
    assert "Unity" in message
    assert "original Doki Doki Literature Club PC release" in message

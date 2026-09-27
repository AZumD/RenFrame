"""Tests for path safety helpers."""

from __future__ import annotations

from pathlib import Path

from renframe.utils import (
    is_dangerous_output_path,
    is_runtime_owned_path,
    normalize_path,
    paths_conflict,
)


def test_normalize_path_expands_user(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    path = normalize_path("~/game")
    assert path == (tmp_path / "game").resolve()


def test_refuse_root_output() -> None:
    assert is_dangerous_output_path(Path("/"))


def test_paths_conflict_same_and_nested(tmp_path: Path) -> None:
    source = tmp_path / "game"
    source.mkdir()
    assert paths_conflict(source, source)
    assert paths_conflict(source, source / "out")
    assert paths_conflict(source / "out", source)
    other = tmp_path / "elsewhere"
    other.mkdir()
    assert not paths_conflict(source, other)


def test_runtime_owned_path_rules() -> None:
    assert is_runtime_owned_path(Path("lib/py3-linux-x86_64/lib.so"))
    assert is_runtime_owned_path(Path("renpy/__init__.py"))
    assert is_runtime_owned_path(Path("Game.sh"))
    assert not is_runtime_owned_path(Path("game/python-packages/mod.so"))
    assert not is_runtime_owned_path(Path("game/script.rpy"))

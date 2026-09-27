"""CLI-level tests for inspect output and exit codes."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from renframe.cli import EXIT_COMPATIBILITY, EXIT_INVALID_GAME, EXIT_OK, main


def _write_elf(path: Path, machine: int) -> None:
    data = bytearray(64)
    data[0:4] = b"\x7fELF"
    data[4] = 2
    data[5] = 1
    data[6] = 1
    struct.pack_into("<H", data, 16, 3)
    struct.pack_into("<H", data, 18, machine)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(data))


def _make_game(root: Path, *, bad_native: bool = False) -> Path:
    (root / "game").mkdir(parents=True)
    (root / "renpy").mkdir()
    (root / "game" / "script.rpy").write_text("label start:\n    return\n", encoding="utf-8")
    (root / "renpy" / "__init__.py").write_text("# renpy\n", encoding="utf-8")
    (root / "renpy" / "versions.py").write_text('version = "8.3.4"\n', encoding="utf-8")
    (root / "lib" / "py3-linux-x86_64").mkdir(parents=True)
    (root / "Example Game.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    if bad_native:
        _write_elf(root / "game" / "python-packages" / "x.so", 62)
    return root


def test_inspect_human_report(tmp_path: Path, capsys) -> None:
    game = _make_game(tmp_path / "Example Game")
    code = main(["inspect", str(game)])
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert "RenFrame compatibility scan" in captured.out
    assert "Detected Ren'Py version: 8.3.4" in captured.out
    assert "LIKELY_COMPATIBLE" in captured.out


def test_inspect_json(tmp_path: Path, capsys) -> None:
    game = _make_game(tmp_path / "JsonGame")
    code = main(["inspect", str(game), "--json"])
    captured = capsys.readouterr()
    assert code == EXIT_OK
    payload = json.loads(captured.out)
    assert payload["is_renpy"] is True
    assert payload["renpy_version"] == "8.3.4"
    assert payload["compatibility"] == "LIKELY_COMPATIBLE"


def test_inspect_invalid_game_exit_code(tmp_path: Path, capsys) -> None:
    plain = tmp_path / "nope"
    plain.mkdir()
    code = main(["inspect", str(plain)])
    assert code == EXIT_INVALID_GAME


def test_inspect_incompatible_exit_code(tmp_path: Path, capsys) -> None:
    game = _make_game(tmp_path / "BadNative", bad_native=True)
    code = main(["inspect", str(game)])
    assert code == EXIT_COMPATIBILITY


def test_build_not_implemented(tmp_path: Path, capsys) -> None:
    game = _make_game(tmp_path / "Later")
    code = main(["build", str(game)])
    captured = capsys.readouterr()
    assert code == 1
    assert "not implemented" in captured.err.lower()

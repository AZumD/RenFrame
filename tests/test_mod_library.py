from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from renframe.mod_library import (
    LibraryError,
    inspect_package,
    save_game,
    save_mod,
    slugify,
    validate_library,
)


def test_slugify() -> None:
    assert slugify("DDLC: The Normal Visual Novel!") == "ddlc-the-normal-visual-novel"


def test_zip_with_game_dir_suggests_merge(tmp_path: Path) -> None:
    archive = tmp_path / "mod.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("game/patch.rpa", b"example")
        zf.writestr("README.txt", b"hello")
    result = inspect_package(archive)
    assert result["suggested_method"] == "merge_game_directory"
    assert result["runtime_sensitive"] is False
    assert result["unsafe_entries"] == []


def test_runtime_overlay_is_flagged(tmp_path: Path) -> None:
    archive = tmp_path / "runtime-mod.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("game/script.rpy", b"pass")
        zf.writestr("lib/linux-x86_64/plugin.so", b"binary")
    result = inspect_package(archive)
    assert result["suggested_method"] == "overlay_game_root"
    assert result["runtime_sensitive"] is True


def test_unsafe_archive_path_is_reported(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.rpa", b"bad")
    result = inspect_package(archive)
    assert result["unsafe_entries"] == ["../escape.rpa"]


def test_library_validation_rejects_unknown_game(tmp_path: Path) -> None:
    (tmp_path / "mod_library" / "games").mkdir(parents=True)
    (tmp_path / "mod_library" / "mods").mkdir(parents=True)
    save_mod(
        {
            "id": "test-mod",
            "name": "Test Mod",
            "scope": "game",
            "game_id": "missing-game",
            "install": [{"op": "overlay_archive", "source": ".", "destination": "game"}],
        },
        root=tmp_path,
    )
    errors = validate_library(root=tmp_path)
    assert any("unknown game_id missing-game" in error for error in errors)


def test_save_and_validate_minimal_records(tmp_path: Path) -> None:
    save_game({"id": "example-game", "name": "Example Game", "fingerprint": {}}, root=tmp_path)
    save_mod(
        {
            "id": "example-patch",
            "name": "Example Patch",
            "scope": "game",
            "game_id": "example-game",
            "artifact": {},
            "install": [{"op": "copy_file", "source": "patch.rpa", "destination": "game/patch.rpa"}],
        },
        root=tmp_path,
    )
    assert validate_library(root=tmp_path) == []


def test_save_mod_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(LibraryError):
        save_mod(
            {
                "id": "evil",
                "name": "Evil",
                "scope": "universal",
                "install": [{"op": "copy_file", "source": "../evil", "destination": "game/evil"}],
            },
            root=tmp_path,
        )


def test_rar_requires_extraction(tmp_path: Path) -> None:
    archive = tmp_path / "mod.rar"
    archive.write_bytes(b"not-a-real-rar")
    with pytest.raises(LibraryError, match="extract the archive"):
        inspect_package(archive)


def test_installer_only_zip_requires_manual_review(tmp_path: Path) -> None:
    archive = tmp_path / "installer.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("setup.exe", b"binary")
    result = inspect_package(archive)
    assert result["suggested_method"] == "custom"
    assert result["suggested_operations"] == []
    assert result["executable_entries"] == ["setup.exe"]

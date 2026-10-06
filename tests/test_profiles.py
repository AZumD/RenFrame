from pathlib import Path

import pytest

from renpy_arm.convert import (
    ConvertError,
    convert_game,
    detect_version,
    is_renpy_game,
    normalize_version,
)
from renpy_arm.profiles import (
    KATAWA_PROFILE,
    detect_legacy_version,
    detect_profile,
)


def _legacy_root(tmp_path: Path, name: str = "Katawa Shoujo") -> Path:
    root = tmp_path / name
    (root / "renpy").mkdir(parents=True)
    (root / "game").mkdir()
    (root / "renpy" / "__init__.py").write_text(
        'version = "Ren\'Py 6.10.2e"\nscript_version = 5003000\n',
        encoding="utf-8",
    )
    return root


def _katawa_root(tmp_path: Path, name: str = "Katawa Shoujo") -> Path:
    root = _legacy_root(tmp_path, name)
    (root / "python25.dll").write_bytes(b"legacy-python")
    (root / "renpy.code").write_bytes(b"legacy-renpy")
    for filename in ("imachine.rpyc", "ui_settings.rpyc", "script-a1-monday.rpyc"):
        (root / "game" / filename).write_bytes(b"fixture")
    return root


def test_normalize_version_accepts_legacy_suffix() -> None:
    assert normalize_version("Ren'Py 6.10.2e") == "6.10.2"


def test_detect_version_reads_legacy_init(tmp_path: Path) -> None:
    root = _legacy_root(tmp_path)
    assert detect_legacy_version(root) == "6.10.2e"
    assert detect_version(root) == "6.10.2"


def test_legacy_distribution_is_recognized_as_renpy(tmp_path: Path) -> None:
    root = _legacy_root(tmp_path)
    (root / "python25.dll").write_bytes(b"fixture")
    assert is_renpy_game(root)


def test_katawa_profile_matches_without_folder_name(tmp_path: Path) -> None:
    root = _katawa_root(tmp_path, "some-random-folder")
    match = detect_profile(root)
    assert match is not None
    assert match.profile.id == KATAWA_PROFILE.id
    assert match.variant == "vanilla"


def test_katawa_hd_profile_matches_name(tmp_path: Path) -> None:
    root = _katawa_root(tmp_path, "Katawa Shoujo HD")
    match = detect_profile(root)
    assert match is not None
    assert match.variant == "hd"


def test_katawa_hd_profile_can_use_png_dimensions(tmp_path: Path) -> None:
    root = _katawa_root(tmp_path, "renamed-game")
    # Enough of a PNG header for the profile's IHDR size probe.
    header = (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\x0d"
        + b"IHDR"
        + (1920).to_bytes(4, "big")
        + (1080).to_bytes(4, "big")
    )
    (root / "game" / "presplash.png").write_bytes(header)
    match = detect_profile(root)
    assert match is not None
    assert match.variant == "hd"


def test_unknown_legacy_game_gets_specific_error(tmp_path: Path) -> None:
    root = _legacy_root(tmp_path, "Other Legacy VN")
    (root / "python25.dll").write_bytes(b"fixture")

    with pytest.raises(ConvertError, match="Legacy Ren'Py 6.10.2e detected"):
        convert_game(root, work_dir=tmp_path / "work")

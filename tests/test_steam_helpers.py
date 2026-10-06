from pathlib import Path

from renpy_arm.convert import patch_launcher_sh, write_steam_helpers


def test_steam_wrapper_does_not_inject_basedir_argument(tmp_path: Path) -> None:
    launcher = tmp_path / "Sample Game.sh"
    launcher.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")

    write_steam_helpers(tmp_path, "Sample Game", "8.5.3", launcher)

    wrapper = (tmp_path / "launch-steam.sh").read_text(encoding="utf-8")
    assert 'exec "$GAME_DIR/Sample Game.sh" "$@"' in wrapper
    assert 'exec "$GAME_DIR/Sample Game.sh" "$GAME_DIR" "$@"' not in wrapper


def test_frame_diagnostic_helper_is_written(tmp_path: Path) -> None:
    launcher = tmp_path / "Sample Game.sh"
    launcher.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")

    write_steam_helpers(tmp_path, "Sample Game", "8.5.3", launcher)

    diag = (tmp_path / "diagnose-frame.sh").read_text(encoding="utf-8")
    assert 'if [[ "${1:-}" == "--launch" ]]; then' in diag
    assert 'bash -x "$GAME_DIR/launch-steam.sh"' in diag
    assert "librenpython dependencies" in diag


def test_launcher_crlf_is_normalized_even_if_arm_mapping_exists(tmp_path: Path) -> None:
    launcher = tmp_path / "Legacy.sh"
    launcher.write_bytes(
        b"#!/bin/sh\r\n"
        b"case \"$RENPY_PLATFORM\" in\r\n"
        b"  *-aarch64|*-arm64)\r\n"
        b"    RENPY_PLATFORM=\"linux-aarch64\"\r\n"
        b"    ;;\r\n"
        b"esac\r\n"
    )

    patch_launcher_sh(launcher)

    data = launcher.read_bytes()
    assert b"\r" not in data
    assert data.startswith(b"#!/bin/sh\n")

from pathlib import Path

from renpy_arm.convert import write_steam_helpers


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

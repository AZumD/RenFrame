#!/usr/bin/env bash
# Unit tests for renpy_arm convert (no full SDK download).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT"
FIXTURE="$ROOT/tests/fixtures/minimal_renpy"

pass=0
fail=0
check() {
  local desc="$1"; shift
  if "$@"; then echo "PASS: $desc"; pass=$((pass+1)); else echo "FAIL: $desc"; fail=$((fail+1)); fi
}

check "app main exists" test -f "$ROOT/app/main.py"
check "convert module exists" test -f "$ROOT/renpy_arm/convert.py"
check "requirements exist" test -f "$ROOT/requirements.txt"
check "windows build script" test -f "$ROOT/build/build_windows.ps1"
check "linux aarch64 build script" test -f "$ROOT/build/build_linux_aarch64.sh"
check "docs exist" test -f "$ROOT/docs/README/RENPY_ARM_CONVERTER.md"
check "windows build docs" test -f "$ROOT/docs/README/BUILD_WINDOWS.md"
check "linux aarch64 build docs" test -f "$ROOT/docs/README/BUILD_LINUX_AARCH64.md"
check "fixture exists" test -d "$FIXTURE/renpy" -a -d "$FIXTURE/lib"
check "windows exe built" test -f "$ROOT/dist/windows/RenFrame/RenFrame.exe"

if python3 - <<PY
import sys
from pathlib import Path
root = Path(r"$ROOT")
sys.path.insert(0, str(root))
from renpy_arm.convert import (
    detect_version, find_launcher_sh, is_renpy_game, normalize_version, FRAME_INSTRUCTIONS,
)
assert normalize_version("8.5.3.26051504") == "8.5.3"
fixture = root / "tests" / "fixtures" / "minimal_renpy"
assert is_renpy_game(fixture)
ver = detect_version(fixture)
assert ver == "8.3.7", ver
launch = find_launcher_sh(fixture)
assert launch.suffix == ".sh"
assert "add-to-steam.sh" in FRAME_INSTRUCTIONS
print("detect", ver, "launcher", launch.name)
PY
then
  echo "PASS: convert helpers + version detect"
  pass=$((pass+1))
else
  echo "FAIL: convert helpers + version detect"
  fail=$((fail+1))
fi

echo "Result: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]

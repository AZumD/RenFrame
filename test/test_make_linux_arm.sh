#!/usr/bin/env bash
# Smoke-test make-linux-arm.sh (no huge archive by default).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL="$ROOT/make-linux-arm.sh"
fail=0
pass=0

check() {
  local desc="$1"; shift
  if "$@"; then
    echo "PASS: $desc"
    pass=$((pass + 1))
  else
    echo "FAIL: $desc"
    fail=$((fail + 1))
  fi
}

check "installer exists" test -f "$INSTALL"

TMP_CACHE="${TMPDIR:-/tmp}/renpy-arm-test-cache-$$"
mkdir -p "$TMP_CACHE"
if [[ -f "$ROOT/_arm_experiment/renpy-8.5.3-sdkarm.tar.bz2" ]]; then
  cp -f "$ROOT/_arm_experiment/renpy-8.5.3-sdkarm.tar.bz2" "$TMP_CACHE/" 2>/dev/null || true
fi

bash "$INSTALL" --cache-dir "$TMP_CACHE" --no-archive

check "aarch64 librenpython present" test -f "$ROOT/lib/py3-linux-aarch64/librenpython.so"
check "game-named launcher binary" test -f "$ROOT/lib/py3-linux-aarch64/summertimesaga"
check "launch-steam.sh written" test -f "$ROOT/launch-steam.sh"
check "add-to-steam.sh written" test -f "$ROOT/add-to-steam.sh"
check "desktop written in game dir" test -f "$ROOT/summertimesaga.desktop"
check "steam readme written" test -f "$ROOT/README for adding games to steam.txt"
check "steam readme mentions add-to-steam.sh" grep -q 'add-to-steam.sh' "$ROOT/README for adding games to steam.txt"
check "launcher maps aarch64" grep -q 'linux-aarch64' "$ROOT/summertimesaga.sh"
check "add-to-steam mentions steamos-add-to-steam" grep -q 'steamos-add-to-steam' "$ROOT/add-to-steam.sh"
check "make script has no add_to_steam() fn" bash -c "! grep -q '^add_to_steam()' '$INSTALL'"
check "make script documents device-side add" grep -q 'add-to-steam.sh' "$INSTALL"

if command -v file >/dev/null 2>&1; then
  check "lib is ARM aarch64 ELF" bash -c "file '$ROOT/lib/py3-linux-aarch64/librenpython.so' | grep -q 'ARM aarch64'"
fi

bash "$INSTALL" --cache-dir "$TMP_CACHE" --no-archive
check "idempotent re-run" true

# Tiny archive smoke: zip only steam scripts + a marker via --no-archive already done;
# verify create_archive path exists in installer.
check "create_archive function present" grep -q 'create_archive' "$INSTALL"

echo "Result: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]

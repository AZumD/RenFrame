#!/usr/bin/env bash
# Build native Linux aarch64 binary (run ON the Frame / aarch64 Linux).
# Usage:
#   cd renpy-arm-converter
#   python3 -m venv .venv && source .venv/bin/activate
#   pip install -r requirements.txt
#   # SteamOS / Frame may need: sudo pacman -S tk  (or python-tk)
#   bash build/build_linux_aarch64.sh
set -euo pipefail
cd "$(dirname "$0")/.."

ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
  echo "WARNING: building on $ARCH — for Frame, run this script on aarch64."
fi

PY=python3
if [[ -x .venv/bin/python ]]; then
  PY=.venv/bin/python
fi

"$PY" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name RenFrame \
  --paths . \
  --add-data "app/assets:app/assets" \
  --hidden-import customtkinter \
  --hidden-import tkinterdnd2 \
  --collect-all customtkinter \
  --collect-all tkinterdnd2 \
  app/main.py

mkdir -p dist/linux-aarch64/RenFrame
if [[ -d dist/RenFrame ]]; then
  cp -a dist/RenFrame/. dist/linux-aarch64/RenFrame/
fi

cat > dist/linux-aarch64/RenFrame/README.txt <<'EOF'
RenFrame (Linux aarch64 / Steam Frame)
======================================

1. Run:  ./RenFrame
2. Drop a Ren'Py PC game folder or .zip
3. Click Convert — get a *-linux-aarch64.zip
4. Unpack that zip on this device, then:

     chmod +x add-to-steam.sh launch-steam.sh *.sh
     ./add-to-steam.sh

Needs a display (Desktop Mode / gamescope session). Keep this folder intact.
EOF

chmod +x dist/linux-aarch64/RenFrame/RenFrame 2>/dev/null || true
echo "Built: dist/linux-aarch64/RenFrame/RenFrame"

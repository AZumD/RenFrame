#!/usr/bin/env bash
set -euo pipefail
cd /mnt/c/Users/Antho/Projects/summertimesaga-21.0.0-wip.8194-pc/renpy-arm-converter
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
python -c 'import customtkinter; from renpy_arm.convert import convert_game; print("imports_ok")'

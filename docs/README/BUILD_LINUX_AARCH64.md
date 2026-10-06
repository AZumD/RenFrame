# BUILD_LINUX_AARCH64

## Purpose
PyInstaller script that produces a native **Linux aarch64** binary for Steam Frame.

## Run (on Frame / aarch64)
```bash
cd renpy-arm-converter
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# if tk missing: sudo pacman -S tk
bash build/build_linux_aarch64.sh
```

## Output
`dist/linux-aarch64/RenFrame/RenFrame`

Must be built on aarch64 — do not cross-compile from Windows/x86_64.

## Related
- [RENPY_ARM_CONVERTER.md](RENPY_ARM_CONVERTER.md)
- [BUILD_WINDOWS.md](BUILD_WINDOWS.md)

# RENPY_ARM_CONVERTER

## Purpose
Desktop app that turns a **Ren'Py PC build** into a **Linux aarch64 zip** for Steam Frame (same job as `make-linux-arm.sh`, with a UI).

## Workflow
1. Drag a Ren'Py game **folder** or **.zip** into the app (or Browse).  
2. Click **Convert**.  
3. App writes `<game>-linux-aarch64.zip` (default: Desktop).  
4. Copy the zip to the Frame → unpack → run `./add-to-steam.sh` (Steam running).  

The right-hand panel in the app always shows Frame / Steam steps. The zip also contains `README for adding games to steam.txt`, `add-to-steam.sh`, and `launch-steam.sh`.

## Run from source
```bash
cd renpy-arm-converter
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux Frame:
source .venv/bin/activate

pip install -r requirements.txt
python app/main.py
```

CLI (no GUI):
```bash
python -m renpy_arm /path/to/MyGame-pc -o MyGame-linux-aarch64.zip
```

## Native builds
### Windows (x64) — ready-made
Prebuilt folder (after `build_windows.ps1`):

`dist/windows/RenFrame/RenFrame.exe`

Keep the whole `RenFrame` folder (companion `_internal` files). Zip: `dist/RenFrame-windows-x64.zip`.

Rebuild:
```powershell
powershell -File build\build_windows.ps1
```

### Steam Frame / Linux aarch64
Must be built **on** aarch64 (the Frame or another ARM Linux box) — PyInstaller does not cross-compile:
```bash
cd renpy-arm-converter
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# SteamOS / Frame may need: sudo pacman -S tk
bash build/build_linux_aarch64.sh
# → dist/linux-aarch64/RenPyArmConverter/RenPyArmConverter
```

## Layout
| Path | Role |
|------|------|
| `renpy_arm/convert.py` | Conversion core (detect, download sdkarm, graft, steam scripts, zip) |
| `app/main.py` | CustomTkinter UI |
| `build/build_windows.ps1` | PyInstaller Windows |
| `build/build_linux_aarch64.sh` | PyInstaller Linux ARM |

## Notes
- Your original game folder is **copied** before patching; the PC build is left alone.  
- Needs network once per Ren'Py version to fetch `renpy-<ver>-sdkarm.tar.bz2`.  
- Same limits as the shell script: pure Ren'Py games without exotic native modules.

## Tests
```bash
./test/test_renpy_arm_converter.sh
```

## Related
- [MAKE_LINUX_ARM.md](MAKE_LINUX_ARM.md)  
- [ADD_TO_STEAM.md](ADD_TO_STEAM.md)  
- [OVERVIEW.md](OVERVIEW.md)

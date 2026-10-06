# OVERVIEW

## Project
**RenFrame** — package Ren'Py PC builds for native **Linux ARM64 / Steam Frame**.

### GUI + convert core
- `app/main.py` — drag-drop converter UI  
- `renpy_arm/convert.py` — detect version, download sdkarm, graft aarch64, Steam scripts, zip  
- Docs: [RENPY_ARM_CONVERTER.md](RENPY_ARM_CONVERTER.md)  
- Builds: [BUILD_WINDOWS.md](BUILD_WINDOWS.md), [BUILD_LINUX_AARCH64.md](BUILD_LINUX_AARCH64.md)

### Shell
- `make-linux-arm.sh` — [MAKE_LINUX_ARM.md](MAKE_LINUX_ARM.md)  
- `add-to-steam.sh` — [ADD_TO_STEAM.md](ADD_TO_STEAM.md)

### CLI inspect / runtime-swap build
Python package `renframe` (`renframe inspect`, `renframe build`) — see [CLI.md](CLI.md), [BUILDER.md](BUILDER.md).

### Version
`0.1.0` — first public release (GUI convert + Windows binary).

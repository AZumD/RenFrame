# RenFrame

Convert **Ren'Py PC builds** into native **Linux ARM64** packages for the **Steam Frame**.

```text
Drop game → Convert → *-linux-aarch64.zip → Frame unpack → ./add-to-steam.sh
```

## 0.1.0

- **GUI app** (Windows native + Linux aarch64 build script)
- **CLI convert** (`python -m renpy_arm`) with automatic `sdkarm` download
- Shell helper `make-linux-arm.sh` (same conversion pipeline)
- Steam helpers: `add-to-steam.sh`, `launch-steam.sh`
- Optional: `renframe inspect` / `renframe build` (compatibility report + runtime-swap build)

## Quick start (Windows GUI)

1. Download **RenFrame-windows-x64.zip** from [Releases](https://github.com/AZumD/RenFrame/releases).
2. Unpack and run `RenFrame.exe` (keep the folder together).
3. Drop a Ren'Py game folder or `.zip` → **Convert**.
4. Copy the output zip to your Frame, unpack, then:

```bash
chmod +x add-to-steam.sh launch-steam.sh *.sh
./add-to-steam.sh
```

## Run from source

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux:   source .venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

CLI:

```bash
python -m renpy_arm /path/to/MyGame-pc -o MyGame-linux-aarch64.zip
```

### Mod Library Manager

Maintainers can browse, add, edit, inspect, and validate the machine-readable game/mod catalog without hand-editing JSON:

```bash
pip install -e .
renframe-library
```

Or from the repository checkout:

```bash
python -m renframe.library_manager
```

The manager never commits or pushes automatically. Review its changes with the built-in **Git diff** view, then commit normally.

## Native builds

| Target | Script |
|--------|--------|
| Windows x64 | `powershell -File build/build_windows.ps1` |
| Steam Frame (aarch64) | run on device: `bash build/build_linux_aarch64.sh` |

## Docs

- [Project overview](docs/README/OVERVIEW.md)
- [Ren'Py mod library research](docs/MOD_LIBRARY.md)
- [Machine-readable mod library](mod_library/README.md)

## License

[GNU General Public License v3.0](LICENSE) (GPL-3.0).

Copyleft: if someone distributes RenFrame or a modified version, they must also provide the source under GPLv3 — they cannot take this code into closed proprietary software.

---

*Made with help of AI.*

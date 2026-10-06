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

## Native builds

| Target | Script |
|--------|--------|
| Windows x64 | `powershell -File build/build_windows.ps1` |
| Steam Frame (aarch64) | run on device: `bash build/build_linux_aarch64.sh` |

## Docs

See [docs/README/OVERVIEW.md](docs/README/OVERVIEW.md).

## License

MIT

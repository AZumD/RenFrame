# RenFrame

Convert **Ren'Py PC builds** into native **Linux ARM64** packages for the **Steam Frame**.

```text
Drop game → Convert → *-linux-aarch64.zip → Frame unpack → ./add-to-steam.sh
```


## 0.1.1 (in development)

- **Legacy compatibility profiles** for known old Ren'Py games that cannot use the normal runtime-transplant path.
- Experimental first profile: **Katawa Shoujo / Katawa Shoujo HD (Ren'Py 6.10.2e)**.
  - fingerprints the game instead of relying on the folder name;
  - normalizes it against a pinned known-good Ren'Py 8 port;
  - keeps/reapplies the user's local game assets;
  - reapplies the HD project's source overrides for the HD edition;
  - then hands the result back to RenFrame's normal Linux ARM64 converter.
- Unknown legacy Ren'Py builds now report their detected engine version instead of saying they are not Ren'Py games.
- SDK and compatibility downloads use a persistent per-user cache.
- Archive extraction now rejects path-traversal entries.

The Katawa profile is intentionally experimental until it has been exercised against
the original release and the HD build end-to-end on a Steam Frame.

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

[GNU General Public License v3.0](LICENSE) (GPL-3.0).

Copyleft: if someone distributes RenFrame or a modified version, they must also provide the source under GPLv3 — they cannot take this code into closed proprietary software.

---

*Made with help of AI.*

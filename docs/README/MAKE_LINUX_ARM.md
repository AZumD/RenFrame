# MAKE_LINUX_ARM

## Purpose
Build a **portable Linux aarch64 Ren'Py game package** from a PC build:

1. Graft official `sdkarm` runtime into the game tree  
2. Write Steam helper scripts (`launch-steam.sh`, `add-to-steam.sh`, `.desktop`)  
3. Pack a `.zip` / `.7z` / `.tar.gz` to copy to an ARM device (e.g. Steam Frame)

Steam registration is **not** done here — that happens on the device via [`ADD_TO_STEAM.md`](ADD_TO_STEAM.md).

## Workflow
### On a build PC (any arch)
```bash
chmod +x make-linux-arm.sh
./make-linux-arm.sh
```
Copy the produced archive (next to the game folder), e.g. `summertimesaga-linux-aarch64.zip`.

### On the Frame / ARM Linux box
```bash
# unpack the archive, then:
cd summertimesaga   # or whatever the folder is named
chmod +x add-to-steam.sh launch-steam.sh *.sh
./add-to-steam.sh
```
Steam must be running. Then check the library; set compatibility to Linux runtime / native (not Proton).

## Options
| Flag | Meaning |
|------|---------|
| `--version X.Y.Z` | Skip auto-detect (from `renpy/vc_version.py` or `.pyc`) |
| `--force` | Re-download / re-install aarch64 libs |
| `--no-steam-scripts` | Skip writing launch/add-to-steam/.desktop |
| `--no-archive` | Skip packing zip/7z |
| `--full-archive` | Include Windows/x86_64 libs (default archive is lean) |
| `--cache-dir DIR` | SDK download cache |
| `--clean-cache` | Delete SDK tarball after install |

## What it writes into the game folder
- `lib/py3-linux-aarch64/`
- patched game `.sh` (arm64 → `linux-aarch64`)
- `launch-steam.sh` — Steam-safe launcher  
- `add-to-steam.sh` — register non-Steam shortcut on the device  
- `<gamename>.desktop` — paths refreshed by `add-to-steam.sh` after unpack  
- `README for adding games to steam.txt` — short how-to packed into the archive  

## Requirements
`bash`, `curl`, `tar`; `python3` recommended; `zip` or `7z` nice-to-have for archives.

## Related
- [ADD_TO_STEAM.md](ADD_TO_STEAM.md)
- `test/test_make_linux_arm.sh`
- [OVERVIEW.md](OVERVIEW.md)
# ADD_TO_STEAM

## Purpose
On-device script that registers the unpacked Linux ARM Ren'Py game as a **non-Steam** library shortcut.

Shipped inside the archive produced by [`make-linux-arm.sh`](MAKE_LINUX_ARM.md). Run this **on the Frame** (or other ARM Linux + Steam machine), not on the build PC.

## Usage
```bash
cd /path/to/unpacked/game
chmod +x add-to-steam.sh launch-steam.sh
./add-to-steam.sh
```

## What it does
1. Resolves the game directory from its own location  
2. Rewrites `<game>.desktop` with absolute `Exec=` / `Path=` for this unpack path  
3. Calls `steamos-add-to-steam` when available, otherwise `steam://addnonsteamgame/…`  
4. Reminds you to use Steam Linux Runtime / native (not Proton)

Also ships `README for adding games to steam.txt` in the game archive (plain-language steps for the Frame).

## Requirements
- Steam running  
- `steamos-add-to-steam` (SteamOS) or `steam` on `PATH`

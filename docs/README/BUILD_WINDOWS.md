# BUILD_WINDOWS

## Purpose
PyInstaller script that produces a native **Windows x64** build of Ren'Py ARM Converter.

## Run
```powershell
cd renpy-arm-converter
# once: python -m venv .venv && .\.venv\Scripts\Activate.ps1 && pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File build\build_windows.ps1
```

## Output
- `dist/windows/RenFrame/RenFrame.exe` (+ `_internal` folder)
- `dist/RenFrame-windows-x64.zip`

## Related
- [RENPY_ARM_CONVERTER.md](RENPY_ARM_CONVERTER.md)
- [BUILD_LINUX_AARCH64.md](BUILD_LINUX_AARCH64.md)

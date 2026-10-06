# Build native Windows .exe (run on Windows x64)
# Usage (from repo root):
#   python -m venv .venv
#   .\.venv\Scripts\Activate.ps1
#   pip install -r requirements.txt
#   powershell -File build\build_windows.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$py = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  $py = "python"
}

& $py -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name "RenFrame" `
  --paths "." `
  --add-data "app\assets;app\assets" `
  --hidden-import customtkinter `
  --hidden-import tkinterdnd2 `
  --collect-all customtkinter `
  --collect-all tkinterdnd2 `
  "app\main.py"

$release = "dist\windows\RenFrame"
New-Item -ItemType Directory -Force -Path $release | Out-Null
if (Test-Path "dist\RenFrame") {
  Copy-Item -Recurse -Force "dist\RenFrame\*" $release
}

$readme = @"
RenFrame (Windows)
==================

1. Run RenFrame.exe
2. Drop a Ren'Py PC game folder or .zip
3. Click Convert — a *-linux-aarch64.zip appears (Desktop by default)
4. Copy that zip to your Steam Frame, unpack, then:

     chmod +x add-to-steam.sh launch-steam.sh *.sh
     ./add-to-steam.sh

Keep this whole folder together.
"@
Set-Content -Path (Join-Path $release "README.txt") -Value $readme -Encoding UTF8

$zip = "dist\RenFrame-windows-x64.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $release -DestinationPath $zip -CompressionLevel Optimal

Write-Host "Built: $release\RenFrame.exe"
Write-Host "Zip:   $zip"

# Build native Windows .exe (run on Windows x64)
# Usage (from repo root):
#   py -3.12 -m venv .venv-win
#   .\.venv-win\Scripts\Activate.ps1
#   python -m pip install -e ".[build,gui]"
#   powershell -ExecutionPolicy Bypass -File build\build_windows.ps1

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot

# Prefer the active environment, then the dedicated Windows build venv.
# A shared WSL checkout may contain a .venv whose Windows shim points back to
# /usr/bin, so .venv-win must win over that fallback.
$py = $null
if ($env:VIRTUAL_ENV) {
  $activePy = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
  if (Test-Path $activePy) { $py = $activePy }
}
if (-not $py) {
  $windowsPy = Join-Path $repoRoot ".venv-win\Scripts\python.exe"
  if (Test-Path $windowsPy) { $py = $windowsPy }
}
if (-not $py) {
  $legacyPy = Join-Path $repoRoot ".venv\Scripts\python.exe"
  if (Test-Path $legacyPy) { $py = $legacyPy }
}
if (-not $py) { $py = "python" }

$workPath = Join-Path $repoRoot ".pyinstaller-work"
$distPath = Join-Path $repoRoot "dist"
$assetsPath = Join-Path $repoRoot "app\assets"
$entryPoint = Join-Path $repoRoot "app\main.py"

if (-not (Test-Path $assetsPath)) {
  throw "Missing application assets: $assetsPath"
}

# A previously launched PyInstaller build can keep its Python/Tk DLLs locked
# even after the GUI window disappears. Stop only processes whose executable
# actually lives inside RenFrame's own dist directories before cleanup.
$buildRoots = @(
  (Join-Path $distPath "RenFrame"),
  (Join-Path $distPath "windows\RenFrame")
)

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ForEach-Object {
  $exe = $_.ExecutablePath
  if (-not $exe) { return }
  foreach ($root in $buildRoots) {
    if ($exe.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
      Write-Host "Stopping stale build process $($_.Name) (PID $($_.ProcessId))"
      Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
      break
    }
  }
}
Start-Sleep -Milliseconds 300

if (Test-Path $workPath) { Remove-Item -Recurse -Force $workPath }
if (Test-Path (Join-Path $distPath "RenFrame")) {
  Remove-Item -Recurse -Force (Join-Path $distPath "RenFrame")
}
if (Test-Path (Join-Path $distPath "windows\RenFrame")) {
  Remove-Item -Recurse -Force (Join-Path $distPath "windows\RenFrame")
}

Write-Host "Using Python:"
Write-Host "  $py"
Write-Host ""

& $py -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --workpath $workPath `
  --specpath $workPath `
  --distpath $distPath `
  --name "RenFrame" `
  --paths $repoRoot `
  --add-data "$assetsPath;app\assets" `
  --hidden-import customtkinter `
  --hidden-import tkinterdnd2 `
  --collect-all customtkinter `
  --collect-all tkinterdnd2 `
  $entryPoint

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$builtApp = Join-Path $distPath "RenFrame\RenFrame.exe"
if (-not (Test-Path $builtApp)) {
  throw "PyInstaller completed but expected executable was not created: $builtApp"
}

$release = Join-Path $distPath "windows\RenFrame"
New-Item -ItemType Directory -Force -Path $release | Out-Null
Copy-Item -Recurse -Force (Join-Path $distPath "RenFrame\*") $release

$readme = @"
RenFrame (Windows)
==================

1. Run RenFrame.exe
2. Drop a Ren'Py PC game folder or .zip
3. Click Convert — a *-linux-aarch64.zip appears (Desktop by default)
4. Copy that zip to your Steam Frame, unpack, then:

     chmod +x add-to-steam.sh launch-steam.sh diagnose-frame.sh *.sh
     ./add-to-steam.sh

If a converted game does not launch on the Frame:

     ./diagnose-frame.sh --launch

Keep this whole folder together.
"@
Set-Content -Path (Join-Path $release "README.txt") -Value $readme -Encoding UTF8

$zip = Join-Path $distPath "RenFrame-windows-x64.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $release -DestinationPath $zip -CompressionLevel Optimal

$releaseExe = Join-Path $release "RenFrame.exe"
if (-not (Test-Path $releaseExe)) {
  throw "Release packaging failed: $releaseExe was not created"
}

Write-Host ""
Write-Host "Built app (run this one):"
Write-Host "  $releaseExe"
Write-Host ""
Write-Host "Release zip:"
Write-Host "  $zip"
Write-Host ""
Write-Host "NOTE: .pyinstaller-work is temporary build scaffolding. Do not run executables from it."

param(
    [string]$Output = "build/windows-portable",
    [switch]$SkipSidecar
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Destination = Join-Path $Root $Output

if (Test-Path $Destination) { Remove-Item -Recurse -Force $Destination }
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Destination "config") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Destination "resource") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Destination "resource/bin") | Out-Null

Copy-Item (Join-Path $Root "config/config.yaml") (Join-Path $Destination "config/config.yaml")
Copy-Item (Join-Path $Root "resource/*") (Join-Path $Destination "resource") -Recurse -Force -ErrorAction SilentlyContinue

if (-not $SkipSidecar) {
    uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec
    $Sidecar = Join-Path $Root "dist/babelcodex-service.exe"
    if (-not (Test-Path $Sidecar)) { throw "missing PyInstaller sidecar: $Sidecar" }
    Copy-Item $Sidecar (Join-Path $Destination "resource/bin/babelcodex-service.exe") -Force
}

Write-Host "Portable staging directory: $Destination"
Write-Host "Next: build the Windows Tauri executable, copy it beside config/cache/logs/output/resource, then run scripts/audit_windows_portable.ps1."
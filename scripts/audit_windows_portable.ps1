param([Parameter(Mandatory = $true)][string]$Bundle)

$ErrorActionPreference = "Stop"
$Path = (Resolve-Path $Bundle).Path
$Forbidden = @(".git", ".venv", "node_modules", "__pycache__", "state", "logs", "incoming", "*.toml", "*.bak")
$Violations = @()

foreach ($Item in Get-ChildItem -LiteralPath $Path -Recurse -Force) {
    $Relative = $Item.FullName.Substring($Path.Length).TrimStart('\', '/')
    foreach ($Part in $Forbidden) {
        if ($Part.StartsWith('*.') -and $Item.Name -like $Part) { $Violations += "forbidden file: $Relative" }
        elseif (-not $Part.StartsWith('*.') -and $Relative -split '[\\/]' -contains $Part) { $Violations += "forbidden path: $Relative" }
    }
    if ($Item.PSIsContainer) { continue }
    if ($Item.Extension -in @('.yaml', '.yml', '.json', '.txt', '.js', '.css', '.html')) {
        $Text = Get-Content -LiteralPath $Item.FullName -Raw -ErrorAction SilentlyContinue
        if ($Text -match '(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|/home/|/Users/|/tmp/)') { $Violations += "absolute development path: $Relative" }
    }
}

if (-not (Test-Path (Join-Path $Path "config/config.yaml"))) { $Violations += "missing config/config.yaml" }
if (-not (Test-Path (Join-Path $Path "resource"))) { $Violations += "missing resource directory" }
if ($Violations.Count -gt 0) { $Violations | ForEach-Object { Write-Error $_ }; exit 1 }
Write-Host "Windows portable audit passed: $Path"
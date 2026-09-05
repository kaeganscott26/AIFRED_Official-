[CmdletBinding()]
param(
    [string] $EnginePath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

try {
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8787/health' -TimeoutSec 2
    if ($health.engine_running) {
        Write-Host "AifredEngine is already running (provider: $($health.provider), model: $($health.model_name))."
        exit 0
    }
} catch {
    # The loopback companion is not running yet.
}

if (-not $EnginePath) {
    $installed = Join-Path $env:LOCALAPPDATA 'Aifred\bin\AifredEngine.exe'
    if (Test-Path -LiteralPath $installed -PathType Leaf) {
        $EnginePath = $installed
    } else {
        $repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
        $EnginePath = Join-Path $repositoryRoot 'out/windows-x64/current/AifredEngine/AifredEngine.exe'
    }
}

$resolvedEngine = (Resolve-Path -LiteralPath $EnginePath).Path
Start-Process -FilePath $resolvedEngine -WorkingDirectory (Split-Path -Parent $resolvedEngine) `
    -WindowStyle Hidden

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 250
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8787/health' -TimeoutSec 2
        if ($health.engine_running) {
            Write-Host "AifredEngine started: $resolvedEngine"
            Write-Host "Provider ready: $($health.provider_ready)"
            Write-Host "Provider:       $($health.provider)"
            Write-Host "Model:          $($health.model_name)"
            exit 0
        }
    } catch {
        # Keep polling during the bounded startup window.
    }
}

throw 'AifredEngine did not become healthy on 127.0.0.1:8787.'

[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$source = Join-Path $root 'integrations/forge'
$parent = Split-Path -Parent $Destination
New-Item -ItemType Directory -Force -Path $parent | Out-Null
if (Test-Path -LiteralPath $Destination) {
    $existing = (Get-Item -LiteralPath $Destination -Force)
    if ($existing.LinkType -eq 'SymbolicLink' -and $existing.Target -eq $source) { return }
    throw "Refusing to replace an existing unrelated destination: $Destination"
}
New-Item -ItemType SymbolicLink -Path $Destination -Target $source | Out-Null
Write-Host "Linked $Destination -> $source"

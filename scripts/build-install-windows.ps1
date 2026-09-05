[CmdletBinding()]
param([switch] $Install, [switch] $ReplaceSharedSlot, [ValidateSet('windows-release','ninja-release')] [string] $Preset = 'windows-release')
# The former preset name is accepted only by this compatibility wrapper.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'windows/build.ps1') -Action release
if ($Install) { & (Join-Path $PSScriptRoot 'windows/install.ps1') -ReplaceSharedSlot:$ReplaceSharedSlot }

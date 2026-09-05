[CmdletBinding()]
param([switch] $ReplaceSharedSlot)
$ErrorActionPreference = 'Stop'
if (!$ReplaceSharedSlot) { throw 'Both channels own Aifred.vst3 today. Explicit -ReplaceSharedSlot is required; see docs/COEXISTENCE.md.' }
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
& python -B (Join-Path $root 'scripts/common/release.py') verify --platform windows-x64
if ($LASTEXITCODE -ne 0) { throw 'Current artifact verification failed.' }
$current = Join-Path $root 'out/windows-x64/current'
Add-Type -AssemblyName Microsoft.VisualBasic
foreach ($component in @(
    @{ Source = (Join-Path $current 'Aifred.vst3'); Parent = (Join-Path $env:COMMONPROGRAMFILES 'VST3'); Name = 'Aifred.vst3' },
    @{ Source = (Join-Path $current 'AifredEngine'); Parent = (Join-Path $env:LOCALAPPDATA 'Aifred'); Name = 'bin' }
)) {
    $parent = [IO.Path]::GetFullPath($component.Parent)
    $target = [IO.Path]::GetFullPath((Join-Path $parent $component.Name))
    if (!( $target.StartsWith($parent.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase))) { throw 'Invalid install target.' }
    if (Test-Path -LiteralPath $target) {
        $entries = @(Get-Item -LiteralPath $target) + @(Get-ChildItem -LiteralPath $target -Recurse -Force)
        if ($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw 'Refusing install through a reparse point.' }
        [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($target, 'OnlyErrorDialogs', 'SendToRecycleBin', 'ThrowException')
    }
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Copy-Item -LiteralPath $component.Source -Destination $target -Recurse
    foreach ($sourceFile in Get-ChildItem -LiteralPath $component.Source -File -Recurse) {
        $relative = [IO.Path]::GetRelativePath($component.Source, $sourceFile.FullName)
        if ((Get-FileHash -LiteralPath $sourceFile.FullName).Hash -ne (Get-FileHash -LiteralPath (Join-Path $target $relative)).Hash) { throw 'Installed hash mismatch.' }
    }
}
Write-Host 'Official installed into the shared slot. DAW validation still required.'

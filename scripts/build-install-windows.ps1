[CmdletBinding()]
param(
    [switch] $Install,
    [string] $Preset = 'ninja-release'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-ChildPath {
    param(
        [Parameter(Mandatory)] [string] $Candidate,
        [Parameter(Mandatory)] [string] $Parent
    )

    $candidatePath = [System.IO.Path]::GetFullPath($Candidate)
    $parentPath = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\') + '\'
    if (-not $candidatePath.StartsWith($parentPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing filesystem operation outside expected parent: $candidatePath"
    }
}

function Initialize-MsvcEnvironment {
    if (Get-Command cl.exe -ErrorAction SilentlyContinue) { return }

    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
        throw 'MSVC was not found. Install Visual Studio Build Tools with the C++ workload.'
    }

    $installation = (& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath).Trim()
    if (-not $installation) { throw 'A Visual Studio installation with x64 C++ tools was not found.' }
    $developerCommand = Join-Path $installation 'Common7\Tools\VsDevCmd.bat'
    if (-not (Test-Path -LiteralPath $developerCommand -PathType Leaf)) {
        throw "VsDevCmd.bat was not found under: $installation"
    }

    $environmentLines = & cmd.exe /d /s /c "`"$developerCommand`" -arch=x64 -host_arch=x64 >nul && set"
    if ($LASTEXITCODE -ne 0) { throw 'Visual Studio developer environment initialization failed.' }
    foreach ($line in $environmentLines) {
        $parts = $line -split '=', 2
        if ($parts.Count -eq 2 -and $parts[0]) {
            [Environment]::SetEnvironmentVariable($parts[0], $parts[1], 'Process')
        }
    }
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$cmakeFile = Join-Path $repositoryRoot 'CMakeLists.txt'
$cmakeText = Get-Content -Raw -LiteralPath $cmakeFile
$versionMatch = [regex]::Match($cmakeText, 'set\(AIFRED_VERSION_STRING\s+"([^"]+)"')
if (-not $versionMatch.Success) {
    throw 'AIFRED_VERSION_STRING was not found in CMakeLists.txt.'
}

$version = $versionMatch.Groups[1].Value
$commit = (& git -C $repositoryRoot rev-parse --short=7 HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Unable to read the Git commit.' }

Initialize-MsvcEnvironment

& cmake --preset $Preset -S $repositoryRoot
if ($LASTEXITCODE -ne 0) { throw 'CMake configure failed.' }
& cmake --build --preset $Preset --target Aifred_VST3 aifred_dsp_smoke aifred_comparison_tests
if ($LASTEXITCODE -ne 0) { throw 'Release build failed.' }
& ctest --preset $Preset
if ($LASTEXITCODE -ne 0) { throw 'Smoke tests failed.' }

$buildRoot = Join-Path $repositoryRoot "build\$Preset"
$sourceBundle = Join-Path $buildRoot 'Aifred_artefacts\Release\VST3\Aifred.vst3'
if (-not (Test-Path -LiteralPath $sourceBundle -PathType Container)) {
    throw "Expected VST3 bundle not found: $sourceBundle"
}

$distributionRoot = Join-Path $repositoryRoot "dist\AIFRED-$version-win64"
$distributionBundle = Join-Path $distributionRoot 'Aifred.vst3'
Assert-ChildPath -Candidate $distributionBundle -Parent $repositoryRoot
New-Item -ItemType Directory -Force -Path $distributionRoot | Out-Null
if (Test-Path -LiteralPath $distributionBundle) {
    Remove-Item -Recurse -Force -LiteralPath $distributionBundle
}
Copy-Item -Recurse -Force -LiteralPath $sourceBundle -Destination $distributionBundle

$sourceBinary = Get-ChildItem -LiteralPath $sourceBundle -Recurse -File |
    Where-Object Name -EQ 'Aifred.vst3' |
    Select-Object -First 1
$distributionBinary = Get-ChildItem -LiteralPath $distributionBundle -Recurse -File |
    Where-Object Name -EQ 'Aifred.vst3' |
    Select-Object -First 1
if ($null -eq $sourceBinary -or $null -eq $distributionBinary) {
    throw 'The VST3 binary was not found inside its bundle.'
}

$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourceBinary.FullName).Hash
$distributionHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $distributionBinary.FullName).Hash
if ($sourceHash -ne $distributionHash) { throw 'Canonical copy hash mismatch.' }

$installedBundle = Join-Path $env:COMMONPROGRAMFILES 'VST3\Aifred.vst3'
$installedHash = $null
if ($Install) {
    $installParent = Split-Path -Parent $installedBundle
    Assert-ChildPath -Candidate $installedBundle -Parent $installParent
    New-Item -ItemType Directory -Force -Path $installParent | Out-Null
    if (Test-Path -LiteralPath $installedBundle) {
        Remove-Item -Recurse -Force -LiteralPath $installedBundle
    }
    Copy-Item -Recurse -Force -LiteralPath $distributionBundle -Destination $installedBundle
    $installedBinary = Get-ChildItem -LiteralPath $installedBundle -Recurse -File |
        Where-Object Name -EQ 'Aifred.vst3' |
        Select-Object -First 1
    $installedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $installedBinary.FullName).Hash
    if ($installedHash -ne $distributionHash) { throw 'Installed bundle hash mismatch.' }
}

$buildInfo = [ordered]@{
    version = $version
    commit = $commit
    configuration = 'RELEASE'
    platform = 'WIN64'
    sourceArtifact = $sourceBundle
    canonicalArtifact = $distributionBundle
    installedArtifact = if ($Install) { $installedBundle } else { $null }
    sha256 = $distributionHash
}
$buildInfo | ConvertTo-Json | Set-Content -Encoding utf8 -LiteralPath (Join-Path $distributionRoot 'build-info.json')

Write-Host "AIFRED version:       $version"
Write-Host "Git commit:          $commit"
Write-Host 'Build identity:      WIN64 / RELEASE'
Write-Host "Source artifact:     $sourceBundle"
Write-Host "Canonical artifact:  $distributionBundle"
Write-Host "Installed artifact:  $(if ($Install) { $installedBundle } else { 'not installed (use -Install)' })"
Write-Host "SHA-256:             $distributionHash"

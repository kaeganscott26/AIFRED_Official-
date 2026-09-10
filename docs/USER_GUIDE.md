# AIFRED Official user guide

## Install the development dependencies

The supported build and install path is Windows x64. Install:

- Visual Studio 2022 with **Desktop development with C++**, MSVC x64 tools, and a Windows 10 or 11 SDK
- CMake and Ninja
- PowerShell 7
- Python 3
- .NET 10 SDK and runtime
- Git

Node.js 22 or newer is also required for website and Worker validation. Android Admin development additionally needs Android Studio, Android SDK 35, and JDK 17. Those control-plane dependencies are not required to load the VST3.

Open PowerShell 7 and verify the command-line dependencies:

```powershell
git --version
cmake --version
ninja --version
pwsh --version
python --version
dotnet --list-sdks
node --version
npm --version
```

The build script locates Visual Studio and imports its x64 developer environment. You do not need to launch a Developer PowerShell first.

## Build and test

From the repository root:

```powershell
pwsh -NoProfile -File scripts/windows/build.ps1 -Action configure
pwsh -NoProfile -File scripts/windows/build.ps1 -Action build
pwsh -NoProfile -File scripts/windows/build.ps1 -Action test
pwsh -NoProfile -File scripts/windows/build.ps1 -Action release
```

`release` builds and tests before it promotes a verified artifact under `out/windows-x64/current`. It does not install the plugin.

## Install or update

Close every DAW that may hold the bundle open. Start an elevated PowerShell 7 prompt in the repository root and run:

```powershell
pwsh -NoProfile -File scripts/windows/lifecycle.ps1 -Action update
```

The same command handles first install and later updates. It builds, tests, prepares and verifies the release, promotes `current`, installs the VST3 and Intelligence Host, registers host startup, starts the host, and verifies copied file hashes. Rescan or reload AIFRED in the DAW afterward.

Official owns:

```text
VST3     %CommonProgramFiles%\VST3\AIFRED Official\Aifred.vst3
Host     %LOCALAPPDATA%\Aifred\official\IntelligenceHost
Settings %APPDATA%\Aifred\official\IntelligenceHost\settings.json
Port     8788
```

## Uninstall

Close the DAW, open elevated PowerShell 7, and run:

```powershell
pwsh -NoProfile -File scripts/windows/lifecycle.ps1 -Action uninstall
```

Uninstall removes only Official binaries and startup registration. It retains settings, references, provider data, and the Beta channel. Inspect any retained `.candidate` or `.previous` recovery path before changing it.

## Use the plugin

Choose a profile that matches the task: MIX BALANCED, SPECTRUM SURGICAL, MASTERING PRECISION, or STEREO / PHASE DIAGNOSTIC. Profile changes start a clean observation epoch. The plugin measures live audio locally; opening it does not produce periodic Cloudflare calls. Reference, Chat, and Analysis make remote requests only after an explicit user action.

An installed-file hash match proves deployment, not DAW discovery or correct runtime behavior. Complete a manual rescan, load the plugin, pass audio through it, and confirm meters respond to that audio.

See [Build](BUILD.md), [Installation](INSTALLATION.md), [Testing](TESTING.md), and the [backend map](../backend_map.md).

# Build

## Windows prerequisites

Install Visual Studio 2022 C++ x64 with the Windows SDK, CMake, Ninja, PowerShell 7, Python 3, and the .NET 10 SDK. [windows.ps1](../scripts/common/windows.ps1) imports the x64 MSVC environment through `VsDevCmd.bat`; do not use an uninitialized shell compiler by accident.

## Commands

```powershell
pwsh -NoProfile -File scripts/windows/build.ps1 -Action configure
pwsh -NoProfile -File scripts/windows/build.ps1 -Action build
pwsh -NoProfile -File scripts/windows/build.ps1 -Action test
pwsh -NoProfile -File scripts/windows/build.ps1 -Action stage
pwsh -NoProfile -File scripts/windows/build.ps1 -Action release
```

The script uses `out/windows-x64/build` for incremental compiler output. The exact compiler VST3 is `out/windows-x64/build/Aifred_artefacts/Release/VST3/Aifred.vst3`; its binary is `Contents/x86_64-win/Aifred.vst3`. `COPY_PLUGIN_AFTER_BUILD` remains false.

Targets include the VST3, shared engine, pipeline, fixture meter, core tests, frontend contracts, and plugin state contracts. .NET outputs follow [Directory.Build.props](../Directory.Build.props).

macOS arm64 and Linux x64 presets exist as unvalidated build scaffolds. They do not provide a validated distribution, install, update, or runtime workflow.

## Related

- [Distribution](DISTRIBUTION.md)
- [Installation](INSTALLATION.md)
- [Testing](TESTING.md)
- [Repository Construction](REPOSITORY_CONSTRUCTION.md)

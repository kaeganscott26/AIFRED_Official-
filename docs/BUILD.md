# Build

## Windows prerequisites

Install Visual Studio 2022 with Desktop development with C++, MSVC x64 tools, and a Windows SDK. Also install CMake, Ninja, PowerShell 7, Python 3, the .NET 10 SDK/runtime, and Git. Node.js 22 or newer is needed only for website and backend checks. [windows.ps1](../scripts/common/windows.ps1) imports the x64 MSVC environment through `VsDevCmd.bat`.

Verify the command-line tools with the commands in the [user guide](USER_GUIDE.md). Android work also needs Android Studio, Android SDK 35, and JDK 17.

## Commands

```powershell
pwsh -NoProfile -File scripts/windows/build.ps1 -Action configure
pwsh -NoProfile -File scripts/windows/build.ps1 -Action build
pwsh -NoProfile -File scripts/windows/build.ps1 -Action test
pwsh -NoProfile -File scripts/windows/build.ps1 -Action stage
pwsh -NoProfile -File scripts/windows/build.ps1 -Action release
```

The script uses `out/windows-x64/build` for incremental compiler output. The exact compiler VST3 is `out/windows-x64/build/Aifred_artefacts/Release/VST3/Aifred.vst3`; its binary is `Contents/x86_64-win/Aifred.vst3`. `COPY_PLUGIN_AFTER_BUILD` remains false.

`release` promotes a verified artifact but does not install it. Use `scripts/windows/lifecycle.ps1 -Action update` for a first install or update, and `-Action uninstall` to remove the Official channel.

Targets include the VST3, shared engine, pipeline, fixture meter, core tests, frontend contracts, and plugin state contracts. .NET outputs follow [Directory.Build.props](../Directory.Build.props).

macOS arm64 and Linux x64 presets exist as unvalidated build scaffolds. They do not provide a validated distribution, install, update, or runtime workflow.

## Related

- [Distribution](DISTRIBUTION.md)
- [Installation](INSTALLATION.md)
- [Testing](TESTING.md)
- [Repository Construction](REPOSITORY_CONSTRUCTION.md)

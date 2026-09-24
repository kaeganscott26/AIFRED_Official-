# Build

## Prerequisites

Windows requires Visual Studio 2022 with Desktop development with C++, MSVC x64 tools, and a Windows SDK. Also install CMake, Ninja, PowerShell 7, Python 3, the .NET 10 SDK/runtime, and Git. [windows.ps1](../scripts/common/windows.ps1) imports the x64 MSVC environment through `VsDevCmd.bat`.

macOS requires Apple Silicon, Xcode command-line tools, CMake, Ninja, Python 3, the .NET 10 SDK/runtime, Git, and Node.js. Android Admin additionally needs JDK 17 and Android SDK 35. Node.js 22 or newer is needed for website/backend/archive checks, not for loading the plugin.

Verify the command-line tools with the commands in the [user guide](USER_GUIDE.md). Android work also needs Android Studio, Android SDK 35, and JDK 17.

## Windows commands

```powershell
pwsh -NoProfile -File scripts/windows/build.ps1 -Action configure
pwsh -NoProfile -File scripts/windows/build.ps1 -Action build
pwsh -NoProfile -File scripts/windows/build.ps1 -Action test
pwsh -NoProfile -File scripts/windows/build.ps1 -Action stage
pwsh -NoProfile -File scripts/windows/build.ps1 -Action release
```

The script uses `out/windows-x64/build` for incremental compiler output. The exact compiler VST3 is `out/windows-x64/build/Aifred_artefacts/Release/VST3/Aifred.vst3`; its binary is `Contents/x86_64-win/Aifred.vst3`. `package` creates `out/windows-x64/package/AIFRED-Official-windows-x64.zip`; `release` promotes verified `current` and packages that exact tree. `COPY_PLUGIN_AFTER_BUILD` remains false.

`release` promotes a verified artifact but does not install it. Use `scripts/windows/lifecycle.ps1 -Action update` for a first install or update, and `-Action uninstall` to remove the Official channel.

Targets include the VST3, shared engine, pipeline, fixture meter, core tests, frontend contracts, and plugin state contracts. .NET outputs follow [Directory.Build.props](../Directory.Build.props).

## macOS commands

```sh
./scripts/macos/build.sh test
./scripts/macos/build.sh release
./scripts/macos/install.sh
./apps/admin-desktop/macos/install.sh
```

The release command builds the same VST3 and native contracts as Windows, runs repository/Python/.NET/CTest validation, stages a self-contained arm64 host, writes and verifies the release manifest, promotes `current`, and creates the archive under `out/macos-arm64/package/`. The install command owns only `~/Library/Audio/Plug-Ins/VST3/AIFRED Official/` and `~/Library/Application Support/Aifred/official/`. The Admin installer owns only `~/Applications/AIFRED Admin.app`.

The macOS artifacts are locally validated but unsigned. Linux x64 remains an unvalidated build scaffold.

## Android Admin

```sh
cd apps/admin-android
./gradlew test assembleDebug
```

On Windows use `gradlew.bat`. The APK is `apps/admin-android/app/build/outputs/apk/debug/app-debug.apk`. Keep `local.properties` untracked; start from `local.properties.example` only when local values are required.

## Related

- [Distribution](DISTRIBUTION.md)
- [Installation](INSTALLATION.md)
- [Testing](TESTING.md)
- [Repository Construction](REPOSITORY_CONSTRUCTION.md)

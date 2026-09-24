# Installation

## Windows

Install the Windows build dependencies before using the lifecycle command: Visual Studio 2022 Desktop development with C++ and a Windows SDK, CMake, Ninja, PowerShell 7, Python 3, the .NET 10 SDK/runtime, and Git. See the [user guide](USER_GUIDE.md) for verification commands. Node.js and Android tooling are control-plane development dependencies, not plugin runtime requirements.

### First install or update

Close every DAW that may hold the VST3 open. In an elevated PowerShell 7 prompt run:

```powershell
pwsh -NoProfile -File scripts/windows/lifecycle.ps1 -Action update
```

The command runs build, tests, release staging, manifest/hash verification, promotion, VST3 installation, Intelligence Host installation, startup registration, host restart, and copied-file hash verification. Reload or rescan in the DAW afterward.

To build without installing, use `scripts/windows/build.ps1`; [Build](BUILD.md) documents each action.

### Official ownership

| Component | Location |
|---|---|
| VST3 | `CommonProgramFiles/VST3/AIFRED Official/Aifred.vst3` |
| host | `%LOCALAPPDATA%/Aifred/official/IntelligenceHost` |
| logs | `%LOCALAPPDATA%/Aifred/official/logs` |
| settings | `%APPDATA%/Aifred/official/IntelligenceHost/settings.json` |
| startup entry | `AIFRED Official Intelligence Host` |
| port | `8788` |

[install-ownership.ps1](../scripts/common/install-ownership.ps1) validates target ancestry and reparse points, copies into `.candidate`, checks each copied file hash, moves any prior install to `.previous`, promotes the candidate, then sends the prior owned tree to the Recycle Bin. Retained recovery paths stop the operation for inspection.

Uninstall removes only Official binaries and startup registration. It preserves user settings, references, provider data, and Beta. Run:

```powershell
pwsh -NoProfile -File scripts/windows/lifecycle.ps1 -Action uninstall
```

Installed hash equality proves file deployment, not DAW scan/load behavior. [Testing](TESTING.md) lists the required manual host checks.

## macOS arm64

Build, verify, promote, and install the unsigned local release:

```sh
./scripts/macos/build.sh release
./scripts/macos/install.sh
./apps/admin-desktop/macos/install.sh
```

Owned locations are `~/Library/Audio/Plug-Ins/VST3/AIFRED Official/Aifred.vst3`, `~/Library/Application Support/Aifred/official/IntelligenceHost`, `~/Library/LaunchAgents/com.north3rnlight3r.aifred-official-intelligence-host.plist`, and `~/Applications/AIFRED Admin.app`. Remove them with `scripts/macos/uninstall.sh` and `apps/admin-desktop/macos/uninstall.sh`. User settings and archive data are preserved.

The local build is not signed or notarized. Installation proves copied-file identity and host startup registration, not DAW scan/load behavior.

## Related

- [Distribution](DISTRIBUTION.md)
- [Coexistence](COEXISTENCE.md)
- [Build](BUILD.md)
- [Debugging](DEBUGGING.md)

# Installation

## Update current development install

Close every DAW that may hold the VST3 open. In an elevated PowerShell 7 prompt run:

```powershell
pwsh -NoProfile -File scripts/windows/lifecycle.ps1 -Action update
```

The command runs build, tests, release staging, manifest/hash verification, promotion, VST3 installation, Intelligence Host installation, startup registration, host restart, and copied-file hash verification. Reload or rescan in the DAW afterward.

## Official ownership

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

## Related

- [Distribution](DISTRIBUTION.md)
- [Coexistence](COEXISTENCE.md)
- [Build](BUILD.md)
- [Debugging](DEBUGGING.md)

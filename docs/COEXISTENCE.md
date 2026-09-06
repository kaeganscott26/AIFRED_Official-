# Beta and Official coexistence

| Ownership | Beta | Official |
|---|---|---|
| VST3 install | `VST3/AIFRED Beta/Aifred.vst3` | `VST3/AIFRED Official/Aifred.vst3` |
| host port | 8787 | 8788 |
| runtime channel | `beta` | `official` |
| runtime root | `%LOCALAPPDATA%/Aifred/beta` | `%LOCALAPPDATA%/Aifred/official` |
| settings | `%APPDATA%/Aifred/beta/IntelligenceHost` | `%APPDATA%/Aifred/official/IntelligenceHost` |
| startup entry | `AIFRED Beta Intelligence Host` | `AIFRED Official Intelligence Host` |
| manufacturer / plugin code | `N3Lr` / `Aifr` | `Aifr` / `Af40` |
| bundle ID | `com.aifred.plugin` | `com.aifred.audio.aifred` |

Both products preserve their established IDs and inner `Aifred.vst3` filename. Their parent install directories and class IDs separate them. Requests carry channel, product version, plugin instance, session, profile, revision, and schema. Clients reject a host from the wrong channel.

Old global `VST3/Aifred.vst3` and legacy startup/runtime files have ambiguous ownership. The installers do not delete them. Before coexistence testing, close the DAW, identify the product that owns each old path, preserve needed state, remove the old bundle from scanning, and disable only its startup entry. Do not run a broad legacy uninstaller across both channels.

Simultaneous DAW loading still requires manual validation.

## Related

- [Installation](INSTALLATION.md)
- [Architecture](ARCHITECTURE.md)
- [Testing](TESTING.md)
- [Debugging](DEBUGGING.md)

# Installation and user data

CURRENT Windows artifacts come from out/windows-x64/current after release validation. Build/test/stage/release never install. Close the DAW before replacing a loaded bundle. Verify the manifest before use.

Run scripts/windows/install.ps1 -ReplaceSharedSlot only after deliberately choosing Official for the shared installation. It copies the verified VST3 and companion. The existing scripts/build-install-windows.ps1 remains a compatibility wrapper and requires the same explicit replacement flag with -Install.

Both products currently install Aifred.vst3 into %CommonProgramFiles%/VST3. Official installs its engine under %LOCALAPPDATA%/Aifred/bin and its settings/logs under %APPDATA%/Aifred/Engine. This pass preserves current IDs and runtime settings formats. Consult [channel collisions](COEXISTENCE.md); shared-slot replacement is not side-by-side support.

Uninstall/update/rollback wrappers document their boundary and refuse automatic mutation until channel ownership is established. Official currently has no channel-safe uninstaller; do not recursively remove the shared Aifred user-data root. User references, settings, models, reports and other-channel files must survive by default. Build cleanup never touches installed files or user data.

Official has no complete macOS/Linux companion or installer. Platform command wrappers are SCAFFOLDED / NOT VALIDATED.

The gateway is 127.0.0.1:8787; Ollama is a separate service normally at 127.0.0.1:11434. A healthy port alone does not identify the correct channel. Do not auto-start arbitrary provider processes during a build. Installation and model downloads require a deliberate runtime operation.

Future lifecycle: a channel manifest records installed files and hashes; update validates product/channel and waits for host shutdown; uninstall removes only owned components; rollback restores a verified prior same-channel package. These are planned boundaries, not a new updater implementation.

# AIFRED 4 Official

CURRENT: 4.0.0-alpha.2 / JUCE 8.0.8. Flagship rebuild: native VST3 analysis, GUI, Compare, reference client and .NET model companion.

The repositories remain separate. AIFRED helps producers interpret measured audio; it does not automatically mix a session. Windows x64 is the construction validation target. The current companion and WebView integration require Windows validation; macOS is scaffolded. Linux (Arch/Debian/Ubuntu) is SCAFFOLDED / NOT VALIDATED. No complete Linux release is claimed.

Build/test/release from this repository:

```powershell
pwsh -NoProfile -File scripts/windows/build.ps1 -Action release
```

Prerequisites and configure/build/test actions: [BUILD](docs/BUILD.md). Output: out/windows-x64/current. Installation is separate: [INSTALLATION](docs/INSTALLATION.md). Read [DISTRIBUTION](docs/DISTRIBUTION.md) before packaging or replacing artifacts and [COEXISTENCE](docs/COEXISTENCE.md) before installing either channel. Both currently use the shared Aifred.vst3 slot and gateway port 8787.

[ARCHITECTURE](docs/ARCHITECTURE.md) maps current folders/runtime ownership. [DEVELOPMENT](docs/DEVELOPMENT.md) explains configuration and contribution boundaries. [TESTING](docs/TESTING.md) lists actual tests and release gates. [Documentation index](docs/README.md) links specialized component contracts.

PLANNED / UNIMPLEMENTED: shared aifred_engine -> BufferHunter -> aifred_filter, selectable DSP profiles and matching controls. Existing DSP/model/GUI behavior remains unchanged. Read the authoritative [Codex construction guide](docs/REPOSITORY_CONSTRUCTION.md). Python remains offline/experimental, outside the native runtime. Future LLM/context tools begin only after analyzer validation.

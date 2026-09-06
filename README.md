# AIFRED Official 4.0.0-alpha.2

AIFRED Official is a transparent Windows x64 VST3 analyzer. The current source implements the measurement, observation, and deterministic filtering machine:

```text
DAW audio -> aifred_engine -> EngineSnapshot -> BufferHunter
          -> ObservationSnapshot -> aifred_filter -> FilteredMixContext
```

The existing `AifredIntelligenceHost` transports filtered context on the Official channel. This phase does not implement a new intelligence layer or the Babylon GUI.

The plugin exposes four validated DSP profiles: MIX BALANCED, SPECTRUM SURGICAL, MASTERING PRECISION, and STEREO / PHASE DIAGNOSTIC. Profiles select one shared algorithm library. The default spectrum viewport is `-96..0 dBFS`; `-120`, `-72`, and `-48 dBFS` floors are presentation-only choices. Full-resolution FFT power remains unclipped.

## Normal Windows workflow

Prerequisites: Visual Studio 2022 C++ x64 and Windows SDK, CMake, Ninja, PowerShell 7, Python 3, and the .NET 10 SDK/runtime.

Close the DAW, open an elevated PowerShell 7 prompt, and run:

```powershell
pwsh -NoProfile -File scripts/windows/lifecycle.ps1 -Action update
```

That command builds, tests, stages, manifests, verifies, promotes `current`, installs the Official VST3 and host, starts the host, and verifies copied files. Reload or rescan the plugin in the DAW afterward.

The owned install locations are:

- VST3: `CommonProgramFiles/VST3/AIFRED Official/Aifred.vst3`
- host: `%LOCALAPPDATA%/Aifred/official/IntelligenceHost`
- settings: `%APPDATA%/Aifred/official/IntelligenceHost/settings.json`
- host port: `8788`

Generated build and release output belongs under `out/windows-x64`. Do not commit it.

## Documentation

Start with the [documentation hub](docs/README.md). The main references are [Architecture](docs/ARCHITECTURE.md), [DSP Configuration](docs/DSP_CONFIGURATION.md), [Shared DSP](shared-dsp/README.md), [Testing](docs/TESTING.md), [Installation](docs/INSTALLATION.md), and [Implementation Status](docs/IMPLEMENTATION_STATUS.md).

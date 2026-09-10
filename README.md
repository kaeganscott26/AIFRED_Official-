# AIFRED Official 4.0.0-alpha.2

AIFRED Official is a transparent Windows x64 VST3 analyzer. The current source implements the measurement, observation, and deterministic filtering machine:

```text
DAW audio -> aifred_engine -> EngineSnapshot -> BufferHunter
          -> ObservationSnapshot -> aifred_filter -> FilteredMixContext
```

The existing `AifredIntelligenceHost` transports filtered context on the Official channel. This phase does not implement a new intelligence layer or the Babylon GUI.

The plugin exposes four validated DSP profiles: MIX BALANCED, SPECTRUM SURGICAL, MASTERING PRECISION, and STEREO / PHASE DIAGNOSTIC. Profiles select one shared algorithm library. The default spectrum viewport is `-96..0 dBFS`; `-120`, `-72`, and `-48 dBFS` floors are presentation-only choices. Full-resolution FFT power remains unclipped.

## Repository and backend migration

Official contains the unified website/backend, Android Admin, desktop Admin, and `/ops`. The target production topology is:

```text
north3rnlight3r.com/* -> Cloudflare Pages Advanced Mode -> backend routes or static assets
```

The single Pages deployment remains a migration candidate until preview and production validation prove it. No second Worker may intercept `/api/*`. The public Beta repository remains intact as the current production-source fallback. See the [backend map](backend_map.md), [website map](website_map.md), [Cloudflare production guide](docs/CLOUDFLARE_PRODUCTION.md), and [migration checklist](docs/CLOUDFLARE_MIGRATION_CHECKLIST.md).

## Install dependencies and manage the plugin

Install Visual Studio 2022 with Desktop development with C++ and a Windows SDK, CMake, Ninja, PowerShell 7, Python 3, the .NET 10 SDK/runtime, and Git. Node.js 22 or newer is needed for website and Worker checks, not for loading the plugin. The [user guide](docs/USER_GUIDE.md) includes verification commands and the Android development dependencies.

Build and test without installation:

```powershell
pwsh -NoProfile -File scripts/windows/build.ps1 -Action test
```

For a first install or update, close the DAW, open an elevated PowerShell 7 prompt, and run:

```powershell
pwsh -NoProfile -File scripts/windows/lifecycle.ps1 -Action update
```

That command builds, tests, stages, manifests, verifies, promotes `current`, installs the Official VST3 and host, starts the host, and verifies copied files. Reload or rescan the plugin in the DAW afterward.

Uninstall only the Official channel:

```powershell
pwsh -NoProfile -File scripts/windows/lifecycle.ps1 -Action uninstall
```

The owned install locations are:

- VST3: `CommonProgramFiles/VST3/AIFRED Official/Aifred.vst3`
- host: `%LOCALAPPDATA%/Aifred/official/IntelligenceHost`
- settings: `%APPDATA%/Aifred/official/IntelligenceHost/settings.json`
- host port: `8788`

Generated build and release output belongs under `out/windows-x64`. Do not commit it.

## Documentation

Start with the [documentation hub](docs/README.md). The main references are the [User Guide](docs/USER_GUIDE.md), [Architecture](docs/ARCHITECTURE.md), [Repository Map](docs/REPOSITORY_MAP.md), [Backend Map](backend_map.md), [Website Map](website_map.md), [DSP Configuration](docs/DSP_CONFIGURATION.md), [Shared DSP](shared-dsp/README.md), [Testing](docs/TESTING.md), [Installation](docs/INSTALLATION.md), [Implementation Status](docs/IMPLEMENTATION_STATUS.md), and [Changelog](CHANGELOG.md).

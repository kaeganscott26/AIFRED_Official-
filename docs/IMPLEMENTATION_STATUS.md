# Implementation status

This file separates working product code from scaffolding and future architecture. A source file or README is not proof that a capability is active.

## Implemented and validated

| Capability | State | Evidence boundary |
| --- | --- | --- |
| Shared DSP, `EngineSnapshot`, BufferHunter, `ObservationSnapshot`, `aifred_filter`, `FilteredMixContext` | Implemented | Native contract tests pass on macOS arm64; prior Windows validation is recorded in Git history |
| Four DSP profiles, spectrum presentation, metric detail, state compatibility | Implemented | Core, frontend, fixture, and state tests pass |
| Official VST3 | Implemented | macOS arm64 compiles, packages, verifies, and installs; Windows uses the same CMake targets and mirrored release layout |
| `AifredIntelligenceHost` transport | Implemented | Accepts only filtered context, validates the contract, routes replaceable providers, and passes .NET contract tests |
| Unified Pages website/backend and `/ops` | Implemented | Local website/backend integrity and module checks pass; live deployment is separate evidence |
| Android Admin | Implemented | JDK 17/SDK 35 unit tests and debug APK build pass; device installation is separate evidence |
| Windows Desktop Admin | Implemented | PowerShell/WinForms source and installer are canonical; Windows runtime validation requires Windows |
| macOS Desktop Admin | Implemented | Swift/AppKit/WebKit application compiles and installs to `~/Applications/AIFRED Admin.app` |
| Local archive and FORGE export bridge | Implemented | Archive lifecycle tests pass; bounded search/restore and verified-delete ordering are enforced |
| Shared-source pinning | Implemented | `shared-core.lock.json` pins normalized hashes and the verifier passes |

## Present but not a product capability

| Area | Classification | Meaning |
| --- | --- | --- |
| `tools/AifredIntelligenceHost/intelligence/` | Phase 1 design scaffold | Prompt and design material support the existing transport; there is no general `IntelligenceCore`, tool router, session memory, or autonomy |
| Linux preset | Build scaffold | A preset exists, but Linux compilation, packaging, installation, and host validation have not been performed |
| macOS distribution signing/notarization | Deployment work | Local unsigned build/install is validated; Developer ID signing and notarization are not implemented |

## Planned and intentionally not implemented

The fixed intelligence order remains:

1. grounded conversational intelligence;
2. current-session context plus nine retained sessions;
3. read-only DAW/session awareness;
4. maintenance-only autonomy for AIFRED-owned state.

Phases 2–4, Babylon, DAW mutation, mixer control, audio changes, routing changes, automation, and plugin-parameter control are not implemented. Later intelligence phases cannot be built ahead of their acceptance gates, and mutation capabilities are permanently prohibited.

## Evidence still required

- DAW scan/load, audio pass-through, state recall, UI, and simultaneous Beta/Official validation on each supported host.
- Physical Android device installation and authenticated production workflows.
- Windows compilation on a Windows x64 machine, including installer and startup-host validation.
- macOS signing/notarization, complete EBU/proprietary-meter comparison, and realtime CPU profiling.

See [Build](BUILD.md), [Testing](TESTING.md), [Archive Guide](ARCHIVE_GUIDE.md), and [Future](FUTURE.md).

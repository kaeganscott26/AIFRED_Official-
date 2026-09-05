# Repository construction contract

The shared analyzer is implemented. [Architecture](ARCHITECTURE.md) and [DSP contract](../shared-dsp/README.md) describe current ownership. Source lives in shared-dsp/include and shared-dsp/src, frontend adapters in plugin/src, provider host in tools/AifredIntelligenceHost. Python owns release checks only.

Clones build independently. Shared core/host are versioned and checksum-locked in both repositories. No sibling dependency or remote was added. Canonical platform roots are out/windows-x64, out/macos-arm64 and out/linux-x64. Build, stage, current and install have distinct ownership. Windows promotion is implemented; other-platform distribution remains unvalidated scaffolding.

Four initial profiles are implemented. Workspace discussion of tracking/reference-long/compliance/K-System and personality/memory/MCP tooling remains future architecture. Preserve plugin IDs; report manual migration/coexistence limits accurately.

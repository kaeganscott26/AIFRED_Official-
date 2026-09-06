# Repository construction

## Authoritative locations

| Responsibility | Location |
|---|---|
| DSP and contracts | [`shared-dsp/include/aifred`](../shared-dsp/include/aifred), [`shared-dsp/src`](../shared-dsp/src) |
| Shared tests | [`shared-dsp/tests`](../shared-dsp/tests) |
| Official plugin adapter/frontend | [`plugin/src`](../plugin/src) |
| Intelligence transport | [`tools/AifredIntelligenceHost`](../tools/AifredIntelligenceHost) |
| Release/install automation | [`scripts`](../scripts) |
| Canonical documentation | [`docs`](README.md) and [shared DSP README](../shared-dsp/README.md) |

No alternate analyzer, serializer, Python runtime, `.NET AifredEngine`, empty adapter shell, admin/backend/website scaffold, or mock updater contract belongs in the Official source tree. Git retains removed history.

## Independent reproduction

Official and Beta vendor the same shared core and host source. [shared-core.lock.json](../shared-core.lock.json) pins its normalized inventory. Neither CMake nor project references may point at a sibling checkout or machine-specific project path.

Canonical platform roots are `out/windows-x64`, `out/macos-arm64`, and `out/linux-x64`. Compiler output, release candidates, current artifacts, and installed files have separate owners. [Distribution](DISTRIBUTION.md) defines promotion; [Installation](INSTALLATION.md) defines deployment.

## Phase boundary

The completed construction target is `DAW -> EngineSnapshot -> ObservationSnapshot -> FilteredMixContext`. The next project may replace or extend intelligence behind that boundary. Babylon remains the final project phase.

## Related

- [Architecture](ARCHITECTURE.md)
- [Development](DEVELOPMENT.md)
- [Build](BUILD.md)
- [Future](FUTURE.md)

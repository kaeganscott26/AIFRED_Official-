# Repository construction

## Authoritative locations

| Responsibility | Location |
|---|---|
| DSP and contracts | [`shared-dsp/include/aifred`](../shared-dsp/include/aifred), [`shared-dsp/src`](../shared-dsp/src) |
| Shared tests | [`shared-dsp/tests`](../shared-dsp/tests) |
| Official plugin adapter/frontend | [`plugin/src`](../plugin/src) |
| Intelligence transport | [`tools/AifredIntelligenceHost`](../tools/AifredIntelligenceHost) |
| Unified Pages website, backend, and `/ops` | [`apps/website`](../apps/website) |
| Android and desktop administration | [`apps/admin-android`](../apps/admin-android), [`apps/admin-desktop`](../apps/admin-desktop) |
| Historical backend migration material | [`infra/cloudflare/aifred-api`](../infra/cloudflare/aifred-api) (not a deploy target) |
| Release/install automation | [`scripts`](../scripts) |
| Canonical documentation | [`docs`](README.md) and [shared DSP README](../shared-dsp/README.md) |

No alternate analyzer, serializer, Python runtime, `.NET AifredEngine`, empty adapter shell, or mock updater contract belongs in the Official source tree. The website, administration clients, and backend are product source in Official and deploy together through one Pages Advanced Mode runtime. A second `/api/*` Worker is prohibited.

## Independent reproduction

AIFRED Official vendors its shared core and host source directly. [shared-core.lock.json](../shared-core.lock.json) pins that normalized inventory so this repository remains independently reproducible. Neither CMake nor project references may point at a sibling checkout or machine-specific project path.

Canonical platform roots are `out/windows-x64`, `out/macos-arm64`, and `out/linux-x64`. Compiler output, release candidates, current artifacts, and installed files have separate owners. [Distribution](DISTRIBUTION.md) defines promotion; [Installation](INSTALLATION.md) defines deployment.

## Phase boundary

The completed construction target is `DAW -> EngineSnapshot -> ObservationSnapshot -> FilteredMixContext`. The next project may replace or extend intelligence behind that boundary. Babylon remains the final project phase.

Repository and production-infrastructure convergence comes before that next project. Until production ownership moves, Beta retains its live website/backend/admin sources as a rollback boundary.

## Related

- [Architecture](ARCHITECTURE.md)
- [Repository Map](REPOSITORY_MAP.md)
- [Cloudflare Migration Checklist](CLOUDFLARE_MIGRATION_CHECKLIST.md)
- [Development](DEVELOPMENT.md)
- [Build](BUILD.md)
- [Future](FUTURE.md)

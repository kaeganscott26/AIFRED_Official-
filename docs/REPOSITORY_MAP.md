# Official repository map

## Product and runtime

| Path | Responsibility |
| --- | --- |
| [`plugin`](../plugin) | AIFRED 4 VST3 adapter and frontend |
| [`shared-dsp`](../shared-dsp) | Authoritative measurement, observation, filtering, and native client code |
| [`tools/AifredIntelligenceHost`](../tools/AifredIntelligenceHost) | Replaceable provider transport after `FilteredMixContext` |
| [`tests`](../tests) | Native and repository contracts |
| [`scripts`](../scripts) | Build, install, release, and verification automation |

`shared-core.lock.json` pins the source shared with Beta. Both repositories build from their own vendored copy.

## Website and administration

| Path | Responsibility |
| --- | --- |
| [`apps/website`](../apps/website) | Unified Pages Advanced Mode website, backend, and `/ops` |
| [`apps/admin-android`](../apps/admin-android) | Owner-only Android administration and approved website-source editing |
| [`apps/admin-desktop`](../apps/admin-desktop) | Windows/macOS administration clients |
| [`config`](../config) | Non-secret administration and distribution contracts |

Pages owns both static and API behavior through `_worker.js`, with static fallthrough through `env.ASSETS`. Android source writes use its authenticated same-origin backend, an exact text-file allowlist, and a server-side GitHub credential to commit to Official.

## Cloudflare backend

| Path | Responsibility |
| --- | --- |
| [`infra/cloudflare/aifred-api`](../infra/cloudflare/aifred-api) | Abandoned split-Worker migration history; reusable schema/tests only, not deploy authority |
| [`infra/cloudflare/docs`](../infra/cloudflare/docs) | Supporting storage and deployment notes |
| [`docs/cloudflare`](cloudflare) | Dated recovery inventory and traffic policy |

Target routing:

```text
north3rnlight3r.com/* -> Pages Advanced Mode -> dynamic handlers or env.ASSETS
```

Source presence does not prove staging or production deployment. Use the [migration checklist](CLOUDFLARE_MIGRATION_CHECKLIST.md) and report each environment separately.

## Phase boundary

This repository contains no active new intelligence layer or Babylon implementation. The stable path ends at `FilteredMixContext -> AifredIntelligenceHost`. Infrastructure convergence must finish before the next intelligence phase starts.

## Related

- [Repository construction](REPOSITORY_CONSTRUCTION.md)
- [Architecture](ARCHITECTURE.md)
- [Cloudflare production](CLOUDFLARE_PRODUCTION.md)
- [Admin guide](ADMIN_GUIDE.md)
- [Testing](TESTING.md)

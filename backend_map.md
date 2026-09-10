# Official backend map

This map describes the unified source architecture. Production authority remains a separately verified deployment state.

## Request path

```text
north3rnlight3r.com/*
  -> Cloudflare Pages project aifred-site
  -> apps/website/_worker.js
  -> /health, /v1/*, /api/*, /api/v1/*, /ws/chat handlers
  -> env.ASSETS.fetch(request) for static fallthrough
```

There is no second `/api/*` Worker route. The abandoned `infra/cloudflare/aifred-api` tree is retained only as migration history and reusable schema/test material; it is not a deploy target.

## Source ownership

| Surface | Official source | Runtime owner |
| --- | --- | --- |
| website, `/ops`, and API | `apps/website/` | one Pages Advanced Mode runtime |
| backend handlers | `apps/website/lib/backend/` | imported by `_worker.js` |
| compatibility function entrypoints | `apps/website/functions/` | source compatibility; `_worker.js` owns Advanced Mode dispatch |
| Android Admin | `apps/admin-android/` | authenticated same-origin control plane |
| desktop Admin | `apps/admin-desktop/` | authenticated same-origin control plane |
| VST3 | `plugin-aifred/` | DAW process; no periodic backend traffic |
| provider transport | `tools/AifredIntelligenceHost/` | replaceable provider path using `/v1` |
| DSP truth | `shared-dsp/`, `aifred_engine/`, `BufferHunter/`, `aifred_filter/` | plugin process; unchanged by backend work |

The canonical origin is `https://north3rnlight3r.com`; application APIs use `/api/v1`, while OpenAI-compatible provider routes remain under `/v1`. Clients normalize stored `origin`, `origin/api`, `origin/api/v1`, and `origin/v1` values during migration.

## Storage

- D1 `AIFRED_OPS`: sessions, idempotency, references, inquiries, bounded recent activity, lifetime/daily aggregates, and minute request rollups.
- R2 `AIFRED_DOWNLOADS`: exact manifest-addressed release objects.
- R2 `AIFRED_REFERENCE_BUCKET`: licensed reference assets.
- KV: historical/read-mostly compatibility only; `AIFRED_SALES_LOG` is not a request-event firehose.
- Analytics Engine `AIFRED_ANALYTICS`: high-volume request telemetry.

See [Cloudflare production](docs/CLOUDFLARE_PRODUCTION.md), [migration checklist](docs/CLOUDFLARE_MIGRATION_CHECKLIST.md), and [API reference](docs/API_REFERENCE.md).

# AIFRED API

> OBSOLETE DEPLOYMENT PLAN. This directory is donor/reference material only.
> Production is the single `aifred-site` Pages Advanced Mode deployment sourced
> from `apps/website`. Do not deploy this Worker or give staging a domain route.
> The current authority and evidence are in [backend_map.md](../../../backend_map.md).
> All deployment instructions below are historical and superseded.

This directory is the sole authoritative server implementation for AIFRED API behavior.
Production is deployed as the `aifred-api` Worker and is routed only at
`north3rnlight3r.com/api/*`. The Official Pages project owns all other website routes.

## Traffic contract

- Health is a constant-time response. It does not query D1, R2, Analytics Engine, or Ollama.
- Models and releases are cached for 15 minutes; references are cached for five minutes.
  These responses include ETags and accept conditional requests.
- Chat and analysis require an authenticated, identified client. AIFRED plugin chat must
  include a valid `aifred.filtered-mix.v1` payload and an `Idempotency-Key`.
- Analytics accepts only authenticated batches of 1–50 events. Queue consumers combine
  request metrics into minute rollups before D1 writes.
- Admin data is never cached. Dashboard data loads on demand; provider checks are a separate,
  authenticated route and never run as part of health/dashboard refresh.
- Android Admin website edits use `/api/v1/admin/source/*`. The Worker exposes an exact text-file
  allowlist, validates drafts, requires the loaded Git blob SHA, and commits through a server-side
  `GITHUB_TOKEN`. It cannot delete/create files, traverse directories, or accept binary uploads.
- R2 access resolves known keys. No request lists a bucket.

## Storage responsibilities

| Service | Responsibility |
| --- | --- |
| KV `AIFRED_REFERENCE_POOL` | Retained historical reference records; not queried on the production request path after legacy list-quota exhaustion |
| KV `AIFRED_SALES_LOG` | Read-only historical compatibility during migration; no new event firehose writes |
| R2 `aifred-downloads` | Release artifacts and public media objects |
| R2 `aifred-reference-pool` | Retained reference assets; never exposed through bucket listing |
| D1 `aifred-ops` | Releases, structured reference catalog, inquiries, admin sessions, idempotency, activity, and batched minute rollups |
| Analytics Engine `aifred_events` | Per-request operational dimensions and latency/counter metrics |
| Queue `aifred-events` | Async activity ingestion and request-rollup batching |

## Validation and deployment

Local source validation:

```powershell
npm ci
npm run check
```

The check runs syntax tests, Node contract tests, and a Wrangler dry run. It does not prove remote
bindings, secret presence, staging health, production routing, or Pages publication.

Public website analysis uses `/api/v1/analysis/submit` (or `/api/v1/analyzer/submit`). It applies
the retained browser reference gate and stores only accepted, sanitized metadata in D1
`references_catalog`. Plugin analysis uses the distinct authenticated `/api/v1/analysis` route.

Run production and staging deployments, D1 migrations, and secret configuration from this
directory with Wrangler. Secret values belong only in ignored local files and Cloudflare secrets;
never put them in this README, `wrangler.jsonc`, tests, or source.

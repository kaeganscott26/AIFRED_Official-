# AIFRED production API Worker

This directory is the source of truth for `aifred-api`. Production is routed only at
`https://north3rnlight3r.com/api/*`; normal site routes continue to the website deployment.
The Worker normalizes the `/api` prefix and implements the public `/health` and `/v1/*`
contract. `workers.dev` and preview URLs are disabled in production configuration.

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

## Deployment

```powershell
npm ci
npm run check
npm run db:migrate:remote
npm run secrets:rotate
npx wrangler secret bulk .secrets.local.json
npm run deploy
```

The rotation script writes secret values only to ignored local files and prints variable names
only. Never add `.env`, `.dev.vars`, or `.secrets.local.json` to Git.

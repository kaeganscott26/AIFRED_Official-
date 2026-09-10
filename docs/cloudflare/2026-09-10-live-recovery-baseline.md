# Cloudflare live recovery baseline — 2026-09-10

This document records the read-only recovery baseline captured before changing AIFRED production. Secret values are intentionally omitted.

## Repository state

Both repositories were clean and synchronized with `origin/main` after `git fetch --prune origin`.

| Repository | HEAD and `origin/main` | Ahead/behind |
| --- | --- | --- |
| Beta `kaeganscott26/AIFRED` | `a4bdaefe389830989e5e39aa4743ec952854164b` | `0/0` |
| Official `kaeganscott26/AIFRED_Official-` | `99b3691ec3150ed3a08a4ce6a3243666d2d9513c` | `0/0` |

## Production application and rollback target

- Account: `Kaeganscott26@gmail.com's Account` (`b5bd4e29593c5e9ebb17ce26f2ae8f8d`).
- Runtime: Cloudflare Pages project `aifred-site` using Pages Advanced Mode (`apps/website/_worker.js` plus `env.ASSETS.fetch(request)`). There is no standalone Worker named `aifred-site`.
- Canonical production/rollback deployment: `b2b33ea0-e74e-46a0-a6b5-53fb5c5d4b4e`.
- Deployment URL: `https://b2b33ea0.aifred-site.pages.dev`.
- Created: `2026-09-10T13:26:22.598863Z`.
- Source revision recorded by Pages: `05c4444c2bfeba0ed7407f878a65060efbe055ca` (`fix(reference): connect VST to existing production reference pool`).
- Trigger: ad-hoc production deployment on branch `main`.
- Earlier accessible deployments of the same source revision include `c9fe7e78-eb20-42ce-8e66-f5871ec2ec76` and `02cf2cd3-5af4-4f6c-9ae6-185103abc2ef`.
- Production replacement is forbidden until the Official preview passes. Do not delete this rollback path.

## Pages source and domains

- Git source: `kaeganscott26/AIFRED`, branch `main`.
- Build command: empty.
- Root directory: repository root.
- Output directory: `apps/website`.
- Production and preview deployments are enabled.
- Domains: `aifred-site.pages.dev`, `north3rnlight3r.com`, and `www.north3rnlight3r.com`.
- Both custom domains report active verification and validation.
- `www.north3rnlight3r.com` currently serves `200` directly; it does not redirect to the apex in the rollback deployment.
- Zone Worker routes: none. In particular, no Worker route intercepts `north3rnlight3r.com/api/*`.

## Deployed Pages bindings

Production:

- KV `AIFRED_REFERENCE_POOL` -> `8a120701767e474f928d1af7037cd68a`.
- KV `AIFRED_SALES_LOG` -> `2c66da7795b54135a4d67e514b97491f`.
- R2 `AIFRED_DOWNLOADS` -> `aifred-downloads`.
- R2 `AIFRED_REFERENCE_BUCKET` -> `aifred-reference-pool`.
- No D1, Analytics Engine, or Queue binding is deployed to Pages at this baseline.

Preview:

- Only the `GITHUB_TOKEN` secret is present.
- No KV, R2, D1, Analytics Engine, or Queue binding is deployed at this baseline.

Required/observed production secret names:

- `AIFRED_ADMIN_USERNAME`
- `AIFRED_ADMIN_PASSWORD_SHA256`
- `AIFRED_ADMIN_SESSION_SECRET`
- `AIFRED_CHAT_PROVIDER`
- `AIFRED_PLUGIN_RELEASE_TAG`
- `AIFRED_RELEASE_VERSION`
- `Cloudflaireapi`
- `GITHUB_TOKEN`
- `OLLAMA_BASE_URL`
- `OLLMA_MODEL`

The last two observed names preserve the deployed spelling exactly. Values were not read or recorded.

## Other Cloudflare resources

- KV namespaces: `AIFRED_REFERENCE_POOL`, `AIFRED_SALES_LOG`.
- R2 buckets: `aifred-downloads`, `aifred-reference-pool`.
- D1 databases: `aifred-ops` (`60d95cd8-d1da-486c-b6fd-4bfedcd7bc47`) and `assets` (`30af13ab-6117-41c3-9ffd-aa3bedfe92e3`).
- `aifred-ops` migrations are current. It contains the release, inquiry, bounded activity, analytics rollup, request rollup, admin session, idempotency, and reference catalog tables. Baseline row counts were releases 2, activity 5, request rollups 96, analytics rollups 2, inquiries 0, admin sessions 0, and references 0.
- Analytics Engine `SHOW TABLES` returned `aifred_events_staging` only.
- Queues: `aifred-events` and `aifred-events-staging`, both with zero producers and zero consumers.
- An un-routed Worker service record named `aifred-api` still exists, with current version `b628fee0-bef6-4081-a6f9-3aa2935dd896`; it has no secrets and no zone route. `aifred-api-staging` does not exist. This discrepancy is preserved rather than mutated during recovery.

## R2 release and reference inventory

The canonical Beta objects exist in `aifred-downloads` and their bytes were independently downloaded and hashed:

| Key | Size | SHA-256 | Content type |
| --- | ---: | --- | --- |
| `releases/beta/v0.3.6-beta-stable/AIFRED-VST3-Setup.exe` | 53,964,697 | `ce9664d2cb3632cf72c3af930377cf3f0b6d15282c5ed1f33c8ec31aa829e71f` | `application/vnd.microsoft.portable-executable` |
| `releases/beta/v0.3.6-beta-stable/AIFRED-VST3-windows.zip` | 2,323,863 | `3bde33e7f30386d29baec937ed0613f2ee09cf5e322f1c76d758c6d78c6f2ea9` | `application/zip` |

Legacy duplicates also exist at `releases/v0.3.6-beta-stable/AIFRED-VST3-Setup.exe` and `releases/v0.3.6-beta-stable/AIFRED-VST3-windows.zip` with the same sizes and ETags. No release object was moved or deleted. No macOS release object exists.

The `aifred-reference-pool` bucket contains 22 JSON metadata objects under `reference-pool/metadata/`. The `aifred-downloads` bucket also contains the website catalog/audio, brand, data, docs, showcase, and one reference audio object. Historical KV was not enumerated or modified.

## Live rollback behavior

Read-only checks against `https://north3rnlight3r.com` showed:

- `/`, `/ops`, `/ops.css`, and `/ops.js`: `200`; Ops CSS is parsed as CSS and is not fenced in the deployed rollback artifact.
- `/health`: `200`.
- `/v1/models`: `200`.
- `/api/v1/catalog/list`: `200`.
- `/api/v1/reference/pool`: `404` (`unknown route`).
- Beta installer and ZIP `HEAD` requests: `500`.

This is a rollback baseline, not proof that every backend route is healthy.

## Repository/deployment mismatch to repair

Official `apps/website/wrangler.toml` contains committed merge markers and declares none of the deployed bindings. Official `_worker.js` intentionally rejects API routes. The abandoned `infra/cloudflare/aifred-api` config declares the D1, Analytics Engine, Queue, rate-limit, and split-route design, but those bindings are not part of the current Pages deployment. Recovery must move only the useful backend/storage design into the single Pages Advanced Mode runtime and must not recreate the split `/api/*` route.

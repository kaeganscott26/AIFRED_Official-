# Current AIFRED backend migration handoff

Last updated: `2026-09-10T19:26:53-05:00`

This file records the observed current state only. It is updated after each validated milestone. Secret values are never recorded here.

## Repository state

- Official implementation milestone: `6405fef209202a9a6ed6874a60125cc2d3baafed`; pushed to `origin/main`.
- Beta: `main` at `a4bdaefe389830989e5e39aa4743ec952854164b`; `origin/main` matches; worktree was clean after fetch.
- Current source contains two competing Official API implementations: Pages Advanced Mode backend modules under `apps/website/lib/backend/` and the dedicated Worker under `infra/cloudflare/aifred-api/`. Convergence is not complete.
- Beta still contains its website/backend/admin infrastructure. Retirement is not complete.

## Current production and validation evidence

- Production Pages project: `aifred-site`.
- Current recorded production deployment: `b2b33ea0-e74e-46a0-a6b5-53fb5c5d4b4e`.
- Current recorded production source authority: public Beta repository revision `05c4444c2bfeba0ed7407f878a65060efbe055ca`.
- Current recorded production topology: Pages Advanced Mode serves website and API behavior; no zone Worker route was present at the last live baseline.
- Official unified Pages preview: `20436ef4-2172-431f-ad05-fd9acb07755e` from Official revision `e1b98fd6efb4cc286d9ea81cb6e014ce9e1ec196`.
- Staging Worker is deployed at version `17816c14-693c-44d9-8f2a-fe0693490eab`. Production `aifred-api` remains at `b628fee0-bef6-4081-a6f9-3aa2935dd896` with no secrets and is not yet the public route owner.
- Production acceptance for this convergence: not run.

## Cloudflare resources currently recorded

- Pages: `aifred-site`.
- Workers: `aifred-api`, `aifred-api-staging` (existence/version must be rechecked live).
- D1: `aifred-ops`.
- R2: `aifred-downloads`, `aifred-reference-pool`.
- KV: `AIFRED_REFERENCE_POOL`, `AIFRED_SALES_LOG` (legacy data sources; not authoritative target storage).
- Queues: `aifred-events`, `aifred-events-staging`.
- Reference source: 22 JSON metadata objects under `aifred-reference-pool/reference-pool/metadata/`.
- Authoritative reference destination: D1 `aifred-ops.references_catalog`, now 22 active rows.

## Completed work

- Both repositories fetched and verified clean/synchronized before migration changes.
- Existing production/preview rollback documentation and recent repository history inspected.
- Durable handoff created before convergence changes.
- Dedicated `infra/cloudflare/aifred-api/` source is again declared canonical; its obsolete archive/deployment warnings were removed.
- Public website analyzer and authenticated plugin analysis are separate routes. Accepted website analysis writes sanitized metadata to D1 `references_catalog`; the behavior has an automated route-level persistence test.
- The FilteredMixContext server contract now accepts both `beta` and `official` product channels.
- Worker validation passed 17 Node tests, syntax checks, repository construction checks, and Wrangler production dry-run. This is source validation, not staging or production proof.
- Admin username was removed from versioned Wrangler variables; admin identity must be supplied as a Cloudflare secret.
- Recreated `aifred-api-staging`, configured seven recovered secret names, and applied D1 migration `0004_pages_unified_runtime.sql`.
- Non-provider staging smoke passed public API, release/download, admin, source-control status, analytics idempotency, and logout checks.
- Migrated all 22 historical R2 reference metadata objects into D1. Identity, names, ISO timestamps, metrics, and classification round-tripped 22/22; R2 source objects were not modified.
- Staging website analyzer ingestion and D1-backed pool retrieval passed with one synthetic row that was precisely removed after verification.

## Remaining work

- Complete dedicated Worker capability parity for current Ops/Android/Desktop clients and prove it in staging.
- Validate the migrated D1 pool through both plugin clients and later through production website ingestion.
- Recover/reconcile ignored local environment inputs and configure production secrets by name without exposing values.
- Route Beta and Flagship clients to `https://north3rnlight3r.com/api/v1` and add shared-contract tests.
- Decouple and physically remove Beta backend/site/admin infrastructure only after client/build tooling no longer depends on it.
- Build, test, package, and publish a new Beta release; mirror and verify artifacts.
- Deploy the Official Worker and Official website to production; validate the public domain and clients.
- Remove duplicate Official Pages API implementation and stale infrastructure/docs after production proof.
- Begin Intelligence work only after all convergence gates pass.

## Current blockers

- The current OAuth session can deploy Workers/Pages/routes but does not expose explicit Access mutation or DNS record-write scopes.
- The production Worker still has no secrets. Staging has the recovered API, analytics, admin identity/hash/session, GitHub, and Ollama API secret names.
- `OLLAMA_ACCESS_CLIENT_ID` and `OLLAMA_ACCESS_CLIENT_SECRET` remain unavailable, so protected provider/chat validation is blocked.
- Provider/chat previously failed because `ollama.north3rnlight3r.com` did not resolve and protected Tunnel/Access credentials were unavailable.
- Android device validation is independent and currently unverified; it does not block backend/site work.

## Exact next task

Implement and test the remaining current Ops/Android/Desktop Admin contract against the canonical Worker, then route both plugin clients to the same `/api/v1` contract before touching Beta infrastructure.

## Rollback points

- Official source rollback: `dde171989fb894537489a3a0b74ffaa8bd7090db`.
- Beta source rollback: `a4bdaefe389830989e5e39aa4743ec952854164b`.
- Production Pages rollback deployment: `b2b33ea0-e74e-46a0-a6b5-53fb5c5d4b4e`.
- Prior Official preview: `20436ef4-2172-431f-ad05-fd9acb07755e`.

# Current AIFRED backend migration handoff

Last updated: `2026-09-10T19:06:39-05:00`

This file records the observed current state only. It is updated after each validated milestone. Secret values are never recorded here.

## Repository state

- Official: `main` at `dde171989fb894537489a3a0b74ffaa8bd7090db`; `origin/main` matches; worktree was clean after fetch.
- Beta: `main` at `a4bdaefe389830989e5e39aa4743ec952854164b`; `origin/main` matches; worktree was clean after fetch.
- Current source contains two competing Official API implementations: Pages Advanced Mode backend modules under `apps/website/lib/backend/` and the dedicated Worker under `infra/cloudflare/aifred-api/`. Convergence is not complete.
- Beta still contains its website/backend/admin infrastructure. Retirement is not complete.

## Current production and validation evidence

- Production Pages project: `aifred-site`.
- Current recorded production deployment: `b2b33ea0-e74e-46a0-a6b5-53fb5c5d4b4e`.
- Current recorded production source authority: public Beta repository revision `05c4444c2bfeba0ed7407f878a65060efbe055ca`.
- Current recorded production topology: Pages Advanced Mode serves website and API behavior; no zone Worker route was present at the last live baseline.
- Official unified Pages preview: `20436ef4-2172-431f-ad05-fd9acb07755e` from Official revision `e1b98fd6efb4cc286d9ea81cb6e014ce9e1ec196`.
- Dedicated Worker staging evidence is historical and incomplete for provider/chat; it must be revalidated before reuse.
- Production acceptance for this convergence: not run.

## Cloudflare resources currently recorded

- Pages: `aifred-site`.
- Workers: `aifred-api`, `aifred-api-staging` (existence/version must be rechecked live).
- D1: `aifred-ops`.
- R2: `aifred-downloads`, `aifred-reference-pool`.
- KV: `AIFRED_REFERENCE_POOL`, `AIFRED_SALES_LOG` (legacy data sources; not authoritative target storage).
- Queues: `aifred-events`, `aifred-events-staging`.
- Reference source discovered at the last live baseline: 22 JSON metadata objects under `aifred-reference-pool/reference-pool/metadata/`; D1 `references_catalog` was empty at that baseline.

## Completed work

- Both repositories fetched and verified clean/synchronized before migration changes.
- Existing production/preview rollback documentation and recent repository history inspected.
- Durable handoff created before convergence changes.

## Remaining work

- Select `infra/cloudflare/aifred-api/` as the only Official API implementation and prove capability parity.
- Migrate historical reference metadata into one authoritative reference pool and test accepted website ingestion.
- Recover/reconcile ignored local environment inputs and configure production secrets by name without exposing values.
- Route Beta and Flagship clients to `https://north3rnlight3r.com/api/v1` and add shared-contract tests.
- Decouple and physically remove Beta backend/site/admin infrastructure only after client/build tooling no longer depends on it.
- Build, test, package, and publish a new Beta release; mirror and verify artifacts.
- Deploy the Official Worker and Official website to production; validate the public domain and clients.
- Remove duplicate Official Pages API implementation and stale infrastructure/docs after production proof.
- Begin Intelligence work only after all convergence gates pass.

## Current blockers

- Live Cloudflare authority, resource state, secret-name inventory, protected provider connectivity, and production routing have not yet been revalidated in this run.
- Provider/chat previously failed because `ollama.north3rnlight3r.com` did not resolve and protected Tunnel/Access credentials were unavailable.
- Android device validation is independent and currently unverified; it does not block backend/site work.

## Exact next task

Inventory the two Official API trees and Beta backend dependencies, then run the dedicated Worker test suite and a narrow live Cloudflare read-only check before choosing the first parity/convergence edit.

## Rollback points

- Official source rollback: `dde171989fb894537489a3a0b74ffaa8bd7090db`.
- Beta source rollback: `a4bdaefe389830989e5e39aa4743ec952854164b`.
- Production Pages rollback deployment: `b2b33ea0-e74e-46a0-a6b5-53fb5c5d4b4e`.
- Prior Official preview: `20436ef4-2172-431f-ad05-fd9acb07755e`.

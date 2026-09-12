# AIFRED backend map — current state

Updated 2026-09-12. This file is the current website/backend and Cloudflare
evidence record. Dated migration notes are historical and are not deployment
instructions.

## Runtime authority

The production runtime is one Cloudflare Pages Advanced Mode project:

```text
north3rnlight3r.com/* -> Pages project aifred-site -> apps/website/_worker.js
                                      -> backend routes or env.ASSETS.fetch
```

`apps/website/_worker.js` is the only production request router. It dispatches
`/health`, `/v1/*`, `/api/*`, `/api/v1/*`, and `/ws/chat` to the same backend;
all other requests fall through to the Pages asset binding. No dedicated
Worker may intercept production `/api/*`.

The repository and Pages Git source are `kaeganscott26/AIFRED_Official-`,
branch `main`, with website source under `apps/website`. `aifred-api-staging`
is an isolated smoke/donor Worker, not the production route owner. Its live
storage bindings match the Pages resources and it additionally retains
staging-only queue and rate-limit bindings; those are not copied into
production or used by the website request path.

## Current live evidence

| Item | Verified state |
| --- | --- |
| Pages project | `aifred-site` |
| Pages Git source | Official repository, `main` |
| Pages build output | `apps/website` (corrected from the failing `AIFRED_Official-\\apps\\website` path) |
| Latest Git deployment | `db7d9cf9` from commit `bba3238`, active and verified |
| Pages assets/API | Healthy on `db7d9cf9.aifred-site.pages.dev` and project hostname |
| Apex custom domain | Registered but pending until the zone has the Pages CNAME |
| `www` custom domain | Active but currently protected by an existing Cloudflare Access redirect |
| Zone Worker routes | None |
| `aifred-api-staging` | Exists, isolated, no production route |

The apex DNS write could not be completed by the current Wrangler OAuth scope
(`zone:read` only). No Access application, secret, or existing DNS record was
removed or overwritten. Until the CNAME is added, the Pages hostname is the
verified deployment origin and the Android production origin remains the
intended canonical URL rather than a completed apex-DNS claim.

## Shared API contract

Web, Beta, Official, Android Admin, desktop Admin, and `/ops` use the same
origin and versioned application contract:

```text
https://north3rnlight3r.com/api/v1
```

Browser config derives the current origin. Native clients normalize legacy
origins to `/api/v1`. OpenAI-compatible provider routes remain available at
`/v1/*` for compatibility. Both `beta` and `official` measured-context
identities are accepted without changing DSP validation.

Public routes include health, models, catalog, releases, references, chat,
analysis, analytics, inquiries, downloads, and approved R2 assets. The Android
admin contract additionally includes:

- `GET /api/v1/registry/actions` for the server allowlist;
- `POST /api/v1/command/run` for authenticated allowlisted commands;
- `GET /api/v1/chat/settings` and authenticated settings save;
- authenticated provider configuration/test routes;
- authenticated catalog/reference upload, catalog removal, sales, logs,
  inquiries, dashboard, export, and approved-source routes.

The command route never executes arbitrary shell or filesystem input. Website
source administration remains limited to the existing approved text-file
allowlist, optimistic Git SHA checks, and server-held GitHub credentials.
Binary website assets and arbitrary create/delete/path operations remain
unsupported.

## Bindings

Production Pages uses the existing resources below. `ASSETS` is supplied by
Pages and is not a Worker binding that should be recreated elsewhere.

| Binding | Resource | Responsibility |
| --- | --- | --- |
| `AIFRED_OPS` | D1 `aifred-ops` | references, sessions, idempotency, limits, activity and rollups |
| `AIFRED_DOWNLOADS` | R2 `aifred-downloads` | pinned Beta artifacts and catalog media |
| `AIFRED_REFERENCE_BUCKET` | R2 `aifred-reference-pool` | licensed reference audio |
| `AIFRED_REFERENCE_POOL` | KV `8a120701767e474f928d1af7037cd68a` | historical runtime compatibility |
| `AIFRED_SALES_LOG` | KV `2c66da7795b54135a4d67e514b97491f` | historical sales compatibility, read-only |
| `AIFRED_ANALYTICS` | Analytics Engine `aifred_events` | optional request telemetry |

Staging uses the same D1/KV/R2 resources with dataset
`aifred_events_staging`, queue `aifred-events-staging`, and staging rate-limit
namespaces. This preserves current staging configuration while keeping it
isolated from the production Pages route.

## Deployment and validation

Run the repository check, then use the existing packaging/deployment helper:

```powershell
npm --prefix apps run website:check
npm --prefix apps run website:preview
npm --prefix apps run website:deploy
```

The helper bundles `_worker.js` and packages only public website files/assets.
It does not publish repository source, secrets, SQL, or generated build output.
Deployment `db7d9cf9` was verified for `/`, static assets, `/health`,
`/api/health`, `/api/v1/registry/actions`, `/api/v1/chat/settings`,
`/api/v1/reference/pool`, `/v1/models`, `/ops`, and both full public artifact
downloads. The downloaded installer and ZIP matched the Beta current files by
size and SHA-256. Authenticated admin routes remain covered by the local
contract suite and require owner credentials for live testing. Wait at least
five minutes with no synthetic traffic before making idle-traffic claims.
Wait at least five minutes with no synthetic traffic before making idle-traffic
claims. Report repository HEAD, deployment ID, manifest SHA/hashes, and manual
host/client coverage separately.

## Release boundary

Only the pinned public Beta artifacts are advertised. Official binaries are
not exposed by the website. DSP precision, the FilteredMixContext contract,
and AifredIntelligenceHost ownership remain unchanged by this website/admin
repair.

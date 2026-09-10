# Cloudflare production guide

## Target topology

```text
north3rnlight3r.com/*      -> Cloudflare Pages project aifred-site
north3rnlight3r.com/api/*  -> Cloudflare Worker aifred-api
```

Pages owns HTML, CSS, JavaScript, assets, and the static `/ops` shell. The dedicated Worker owns public, provider, storage, analytics, and authenticated administration APIs. Do not add replacement API handlers under `apps/website/functions`.

## Current migration status

Official contains the implemented replacement Worker and website source. The dated pre-migration inventory found the production Pages project bound to public Beta and `/api/health` outside the replacement route. Staging passed a previous smoke run, including D1-backed references, but those observations do not prove current staging state or production cutover.

Treat these statuses separately:

| Layer | Status |
| --- | --- |
| Official Worker source | Implemented replacement backend |
| Local Worker tests/dry run | Must pass in the current checkout |
| Staging deployment | Previously observed; revalidate before promotion |
| Production `/api/*` route | Pending production cutover; not verified |
| Pages source authority | Beta remains the production fallback until moved and verified |

## Source and configuration

| Responsibility | Authoritative path |
| --- | --- |
| Pages website | `apps/website` |
| Pages configuration | `apps/website/wrangler.toml` |
| API Worker | `infra/cloudflare/aifred-api` |
| Worker configuration | `infra/cloudflare/aifred-api/wrangler.jsonc` |
| D1 migrations | `infra/cloudflare/aifred-api/migrations` |
| Traffic/rate-limit policy | `docs/cloudflare/TRAFFIC_POLICY.md` |
| Recovery inventory | `docs/cloudflare/2026-09-08-pre-migration-inventory.md` |

The root and `infra/cloudflare` Wrangler files are historical/convenience mirrors. Do not deploy them as substitutes for the two authoritative configs.

## Worker bindings

| Binding | Responsibility |
| --- | --- |
| D1 `AIFRED_OPS` | Releases, reference catalog, inquiries, sessions, idempotency, activity, and request rollups |
| R2 `AIFRED_DOWNLOADS` | Release and public media objects |
| R2 `AIFRED_REFERENCE_BUCKET` | Licensed reference assets |
| KV `AIFRED_REFERENCE_POOL` | Historical reference compatibility; not listed on the request path |
| KV `AIFRED_SALES_LOG` | Historical compatibility; not the new event firehose |
| Queue `AIFRED_EVENTS_QUEUE` | Batched activity and request-rollup ingestion |
| Analytics Engine `AIFRED_ANALYTICS` | Per-request operational metrics |
| Rate Limit bindings | Route-specific request enforcement |

## Secrets and external authority

Required secret names depend on enabled features. Admin auth requires `AIFRED_ADMIN_PASSWORD_SHA256` and `AIFRED_ADMIN_SESSION_SECRET`. Authenticated product requests use `AIFRED_API_TOKEN`; public browser analytics may use `AIFRED_ANALYTICS_API_TOKEN`. Provider routes use the configured OpenAI or protected Ollama credentials.

Android website-source administration requires `GITHUB_TOKEN` as a Worker secret with write access limited to `kaeganscott26/AIFRED_Official-`. The Worker accepts only its exact editable-file allowlist. The APK receives neither this token nor Cloudflare credentials.

Never print or commit secret values. `wrangler secret put` changes deployed state; perform secret changes only in an authorized staging or production step.

## Local validation

```powershell
Set-Location infra/cloudflare/aifred-api
npm ci
npm run check

Set-Location ../../../apps
npm ci
npm run website:check
```

`npm run check` includes a Wrangler production dry run. It checks packaging and configuration syntax but does not validate remote resources, secrets, routes, or runtime behavior.

## Staging and production

Use the repository scripts after confirming their targets:

```powershell
npm run deploy:staging
npm run smoke:staging
```

Do not run `npm run deploy`, `npm run smoke:production`, database migration commands with `--remote`, secret uploads, WAF changes, or route changes during source preparation. Follow the [migration checklist](CLOUDFLARE_MIGRATION_CHECKLIST.md), capture rollback state, and obtain production authorization first.

## Mobile website-source flow

Android Admin uses authenticated `/api/v1/admin/source/*` routes to list approved files, load content and its Git blob SHA, validate a draft, commit with optimistic concurrency, and inspect source-control status. The Worker returns a commit SHA and marks deployment verification false. A commit can trigger Pages only after Cloudflare Pages points at Official; the operator must confirm the deployment and deployed content.

Binary website assets do not use this Git text editor. Keep runtime media in an approved R2 flow once that upload contract and bucket ownership are configured.

## Promotion checks

Before production work, record the current repo SHA, deployed Worker/Pages identifiers, resource and binding inventory, secret names, previous and new routes, rollback commands, and smoke procedure. Confirm the external recovery bundle exists instead of relying on the dated note. Preserve Beta until the Official API and website pass production checks together.

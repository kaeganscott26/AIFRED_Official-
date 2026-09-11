# Cloudflare production guide

## Architecture

```text
north3rnlight3r.com/* -> Cloudflare Pages project aifred-site
                     -> apps/website/_worker.js
                     -> dynamic routes or env.ASSETS.fetch(request)
```

The site and backend are one Pages Advanced Mode deployment. `_worker.js` owns `/health`, `/v1/*`, `/api/*`, `/api/v1/*`, and `/ws/chat`; static requests fall through to `env.ASSETS`. A second Worker must not intercept `/api/*`.

## Evidence boundary

Current live state and acceptance evidence: [backend_map.md](../backend_map.md).
The older deployment IDs below are historical rollback evidence, not current status.

The current live rollback baseline is deployment `b2b33ea0-e74e-46a0-a6b5-53fb5c5d4b4e`, documented in [the recovery baseline](cloudflare/2026-09-10-live-recovery-baseline.md). At capture time, Pages Git integration still named the public Beta repository. Official becomes production source authority only after an Official preview passes, the unified deployment is promoted, the Git source is changed, and production is observed successfully. Source implementation or a preview alone does not establish production state.

## Authoritative paths

| Responsibility | Path |
| --- | --- |
| unified site/backend | `apps/website` |
| Pages configuration | `apps/website/wrangler.toml` |
| backend handlers | `apps/website/lib/backend` |
| release manifest | `apps/website/lib/release-manifest.js` |
| preview D1 schema | `apps/website/migrations/0001_unified_runtime.sql` |
| historical migration material | `infra/cloudflare/aifred-api` (not deployable authority) |

## Bindings

| Binding | Responsibility |
| --- | --- |
| `AIFRED_OPS` | D1 operational state, sessions, idempotency, references, bounded activity, aggregates, request rollups |
| `AIFRED_DOWNLOADS` | R2 immutable release objects |
| `AIFRED_REFERENCE_BUCKET` | R2 licensed reference assets |
| `AIFRED_REFERENCE_POOL` | historical/read-mostly KV compatibility |
| `AIFRED_SALES_LOG` | historical/read-only KV compatibility; never the request-event firehose |
| `AIFRED_ANALYTICS` | Analytics Engine request telemetry |

No Queue is required by the unified Pages path. D1 rate-limit rows provide the fallback where Pages cannot bind Workers Rate Limiting.

## Secrets

Admin authentication requires `AIFRED_ADMIN_USERNAME`, `AIFRED_ADMIN_PASSWORD_SHA256`, and `AIFRED_ADMIN_SESSION_SECRET`. Mobile source administration additionally requires `GITHUB_TOKEN`, held by the runtime and never the APK. Provider credentials depend on the selected provider. Record names only; never print or commit values.

## Validation and promotion

```powershell
npm ci --prefix apps
npm --prefix apps run website:check
```

Use `npm --prefix apps run website:preview` for a filtered, bundled Pages preview.
The helper enforces the public asset list because Pages ignores `.assetsignore`.
The preview uses the existing canonical D1 references and does not clone them.
Validate static files, APIs, real references, downloads, admin and provider behavior
before `npm --prefix apps run website:deploy`. Capture the production deployment ID
again and retain rollback. No plugin build or release is part of website recovery.

## Admin source control

`/api/v1/admin/source/*` lists an exact allowlist, reads current text plus Git blob SHA, validates drafts, and updates an existing Official file with optimistic concurrency. It cannot create arbitrary paths, delete, or upload binaries. A returned commit SHA marks deployment verification false until the resulting Pages deployment is independently observed.

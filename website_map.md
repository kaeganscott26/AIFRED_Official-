# Official website and Cloudflare map

## Unified topology

```text
north3rnlight3r.com/*
  -> Cloudflare Pages project aifred-site
  -> apps/website/_worker.js
     -> dynamic backend routes
     -> env.ASSETS.fetch(request) for all remaining static paths
```

`www.north3rnlight3r.com` redirects to the apex in Official source. No Worker route may intercept `/api/*` ahead of this Pages deployment.

| Item | Value |
| --- | --- |
| intended source authority | `kaeganscott26/AIFRED_Official-` |
| website root | `apps/website/` |
| Pages config | `apps/website/wrangler.toml` |
| project | `aifred-site` |
| canonical origin | `https://north3rnlight3r.com` |
| application API prefix | `/api/v1` |
| provider compatibility prefix | `/v1` |

The live recovery baseline is recorded in [2026-09-10 live recovery baseline](docs/cloudflare/2026-09-10-live-recovery-baseline.md). It remains the rollback target until an Official preview and subsequent production promotion pass independently. A source commit does not prove deployment.

## Routes

The unified runtime owns `/health`, `/v1/*`, `/api/*`, `/api/v1/*`, and `/ws/chat`. `/ops` is a static same-origin client whose authenticated calls use `/api/v1/admin/*`. All other requests fall through to `env.ASSETS.fetch(request)`.

## Releases

`apps/website/lib/release-manifest.js` is the authoritative public release mapping. It pins the Beta channel, tag, exact R2 keys, filenames, media types, byte counts, SHA-256 values, and publication state. No macOS artifact is advertised. Public Beta may redirect to its pinned public GitHub asset if an exact R2 object is unavailable; private Flagship assets never use that fallback.

## Administration

Android and desktop clients use the same origin. Source editing is restricted to an exact text-file allowlist, requires the currently loaded Git blob SHA, and commits only to Official through a server-held `GITHUB_TOKEN`. It cannot create arbitrary paths, delete files, or replace binaries. Returned commit evidence is not treated as deployment evidence.

## Rollback

Record the active Pages deployment before promotion and retain deployment `b2b33ea0-e74e-46a0-a6b5-53fb5c5d4b4e` as the current known-good rollback baseline unless a newer verified baseline is explicitly recorded. Do not delete Beta source or Cloudflare recovery resources during stabilization.

See [Backend Map](backend_map.md), [Cloudflare Production](docs/CLOUDFLARE_PRODUCTION.md), and [Migration Checklist](docs/CLOUDFLARE_MIGRATION_CHECKLIST.md).

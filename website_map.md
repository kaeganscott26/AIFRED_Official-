# Official website and Cloudflare map

This document maps the checked-in Official website to the Cloudflare resources that serve it.

## Public topology

```text
north3rnlight3r.com/*
  -> Cloudflare Pages project: aifred-site
  -> source directory: apps/website

north3rnlight3r.com/api/*
  -> Cloudflare Worker route
  -> Worker: aifred-api
  -> source directory: infra/cloudflare/aifred-api
```

`www.north3rnlight3r.com` redirects to the apex. Pages owns HTML, CSS, JavaScript, images, catalog data, and the static `/ops` client. The dedicated Worker owns API responses. The Pages `_worker.js` deliberately rejects `/api`, `/v1`, and `/ws` paths so a missing Worker route fails closed instead of reviving Pages Functions as a second backend.

## Website source and deploy configuration

| Item | Value |
| --- | --- |
| source authority | `kaeganscott26/AIFRED_Official-` |
| website directory | `apps/website/` |
| Pages config | `apps/website/wrangler.toml` |
| Pages project | `aifred-site` |
| production branch label | `main` |
| apex domain | `north3rnlight3r.com` |
| API base | `https://north3rnlight3r.com/api` |

Validate and deploy from the Official checkout:

```powershell
npm ci --prefix apps
npm --prefix apps run website:check
npm --prefix apps run website:deploy
```

Cloudflare Pages was historically connected to the public `AIFRED` repository. During migration, automatic production deployments from that Git integration must be disabled before Official becomes the durable source authority. Direct Wrangler deployments then use only `apps/website` from this repository.

The Official source was deployed to preview alias `official-cutover-preview.aifred-site.pages.dev` on 2026-09-10. Cloudflare accepted the assets and compiled the Pages Worker. The existing Access preview policy correctly requires authentication. Production remains on the Beta-connected deployment until the failed provider gate is repaired.

## Product links

The site presents the latest public Beta as free and AIFRED 4.0 Flagship at `$149.99`. The Beta installer and ZIP resolve through the Worker to immutable, versioned R2 objects whose SHA-256 values match the latest public GitHub release. Release Notes links directly to `https://github.com/kaeganscott26/AIFRED`, where a new user can find dependency, build, install, update, and uninstall instructions.

Flagship purchase or artifact links stay unavailable until a separately validated sale and release exists. No placeholder checkout or unverified artifact is exposed.

## Backend bindings

The Worker uses:

- D1 `aifred-ops` for releases, references, sessions, inquiries, idempotency, and rollups;
- R2 `aifred-downloads` for versioned plugin and catalog objects;
- R2 `aifred-reference-pool` for licensed runtime media where appropriate;
- KV bindings retained for compatibility and non-request-path records;
- Queues for bounded activity ingestion;
- Analytics Engine for request telemetry;
- Worker rate-limit bindings for public and authenticated routes.

Secret values are held by Cloudflare. The repository names required secrets but never contains their values.

## Events and reference pool

Beta and Official use the canonical reference endpoint `https://north3rnlight3r.com/api/v1/references`. Reads are request-driven and cached; uploads require authentication, rate limiting, and idempotency. Successful R2 response resolution emits `plugin.download.served`; an accepted reference write emits `reference.upload.accepted`. Both enter the bounded queue and D1 activity/rollup path used by admin clients. A served event proves that the Worker resolved and started the response, not that a browser consumed every byte. Future UI event handlers must use these contracts rather than direct storage access.

## Rollback

Before a production change, record the active Pages deployment ID, active Worker version, route, bindings, secret names, repository SHAs, R2 artifact hashes, and smoke commands. Roll back by promoting the previous known Pages deployment and Worker version or restoring the previous route. Do not delete Beta source or Cloudflare resources as part of rollback preparation.

See [Backend Map](backend_map.md), [Cloudflare Production](docs/CLOUDFLARE_PRODUCTION.md), and [Migration Checklist](docs/CLOUDFLARE_MIGRATION_CHECKLIST.md).

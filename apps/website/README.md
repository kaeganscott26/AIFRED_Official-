# AIFRED unified Pages website/backend

This directory is the complete Cloudflare Pages Advanced Mode source for
project `aifred-site`. `_worker.js` dispatches `/health`, `/v1/*`, `/api/*`,
`/api/v1/*`, and `/ws/chat` to the backend; every other request falls through
to `env.ASSETS.fetch(request)`.

There is one production site/API runtime. The canonical application origin is
`https://north3rnlight3r.com`, application routes use `/api/v1`, and provider-
compatible routes retain `/v1`. Beta, Official, Android Admin, desktop Admin,
and `/ops` use this same API contract. `aifred-api-staging` remains isolated
for smoke testing and is not a second production `/api/*` Worker.

```powershell
npm ci --prefix apps
npm --prefix apps run website:check
npm --prefix apps run website:dev
```

Use `npm --prefix apps run website:preview` for a filtered preview and
`npm --prefix apps run website:deploy` for the existing Pages deployment
pipeline. The repository’s Pages build output is `apps/website`; the helper
bundles `_worker.js` and packages only public HTML/CSS/JS/assets, headers, and
the worker bundle. It never publishes secrets, SQL, backend source, or
generated build output.

Never commit `.dev.vars` or `.env`. Use the example files for variable names.
See [API Reference](../../docs/API_REFERENCE.md), [Administration Guide](../../docs/ADMIN_GUIDE.md),
and [backend map](../../backend_map.md) for route, security, binding, and live
validation details.

Preview uses the existing canonical `aifred-ops` D1 database so references are
not duplicated. Preview traffic creates normal telemetry/session records;
tests must not insert fabricated reference records.

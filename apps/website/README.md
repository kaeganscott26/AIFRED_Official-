# AIFRED unified Pages website/backend

This directory is the complete Cloudflare Pages Advanced Mode source for project `aifred-site`. `_worker.js` dispatches `/health`, `/v1/*`, `/api/*`, `/api/v1/*`, and `/ws/chat`; every remaining request falls through to `env.ASSETS.fetch(request)`.

There is no separate production API Worker. The canonical origin is `https://north3rnlight3r.com`, application APIs use `/api/v1`, and OpenAI-compatible provider routes use `/v1`.

```sh
npm ci --prefix apps
npm --prefix apps run website:check
npm --prefix apps run website:dev
```

Deploy preview branches before production. Never commit `.dev.vars`; use `.dev.vars.example` for names only. See [API Reference](../../docs/API_REFERENCE.md), [`/ops` Guide](../../docs/OPS_GUIDE.md), and [Cloudflare Production Guide](../../docs/CLOUDFLARE_PRODUCTION.md).

Use `npm --prefix apps run website:preview` from the repository root. After all
acceptance checks pass, `npm --prefix apps run website:deploy` promotes `main` to
the existing Pages project. Both commands use `tools/deploy-website.mjs`.

Wrangler Pages ignores `.assetsignore`. The deployment helper therefore packages
only this directory's public HTML/CSS/JS/assets, `_headers`, and bundled `_worker.js`.
It retains a temporary mirror for review; no repository/plugin files, environment
files, backend source, or migration SQL enter the static upload. The source and
logical output root remain `AIFRED_Official-/apps/website`; no separate runtime or
Cloudflare project is created. Do not deploy the unfiltered directory directly.

Preview uses the existing canonical `aifred-ops` D1 database so references are not
duplicated. Preview requests create normal telemetry/admin session records there;
tests must not insert fabricated reference records. Historical preview D1 is retained.

# AIFRED unified Pages website/backend

This directory is the complete Cloudflare Pages Advanced Mode source for project `aifred-site`. `_worker.js` dispatches `/health`, `/v1/*`, `/api/*`, `/api/v1/*`, and `/ws/chat`; every remaining request falls through to `env.ASSETS.fetch(request)`.

There is no separate production API Worker. The canonical origin is `https://north3rnlight3r.com`, application APIs use `/api/v1`, and OpenAI-compatible provider routes use `/v1`.

```sh
npm ci --prefix apps
npm --prefix apps run website:check
npm --prefix apps run website:dev
```

Deploy preview branches before production. Never commit `.dev.vars`; use `.dev.vars.example` for names only. See [API Reference](../../docs/API_REFERENCE.md), [`/ops` Guide](../../docs/OPS_GUIDE.md), and [Cloudflare Production Guide](../../docs/CLOUDFLARE_PRODUCTION.md).

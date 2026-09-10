# AIFRED Pages website

This directory is the Cloudflare Pages source for project `aifred-site`. It serves HTML, CSS, JavaScript, public assets, and the static `/ops` shell. It does not implement the production API.

The dedicated [`aifred-api` Worker](../../infra/cloudflare/aifred-api/README.md) owns `north3rnlight3r.com/api/*`. Advanced-mode `_worker.js` redirects `www` and rejects API-shaped paths when the dedicated route does not intercept them; all other requests delegate to Pages assets.

```sh
npm ci --prefix apps
npm --prefix apps run website:check
npm --prefix apps run website:dev
npm --prefix apps run website:deploy
```

Never commit `.dev.vars`; use `.dev.vars.example` for names only. See [API Reference](../../docs/API_REFERENCE.md), [`/ops` Guide](../../docs/OPS_GUIDE.md), and [Cloudflare Production Guide](../../docs/CLOUDFLARE_PRODUCTION.md).

Official is the intended source authority. The production Pages project was still tied to Beta in the pre-migration inventory, so a source commit here does not prove publication.

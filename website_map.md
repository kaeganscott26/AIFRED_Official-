# Website map

The canonical website and backend source is `apps/website`, deployed as one
Cloudflare Pages Advanced Mode project named `aifred-site`.

`apps/website/_worker.js` owns backend compatibility routes and sends every
other request to `env.ASSETS.fetch`. The production application API is
`/api/v1`; `/v1` remains the provider-compatible/native-client route. The
staging Worker is isolated smoke infrastructure and is not a second production
API router.

Use [backend_map.md](backend_map.md) for current Cloudflare bindings,
deployment evidence, route ownership, and validation boundaries.

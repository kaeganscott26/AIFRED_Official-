# Cloudflare Backend Map

The canonical current backend map is:

- [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md)

This file is retained as an operations entry point so old links under `infra/cloudflare/docs/` do not break, but it must not become a second independent source of backend truth.

Current authority summary:

- Repository: `kaeganscott26/AIFRED`
- Website/backend source: `apps/website/`
- Worker router: `apps/website/_worker.js`
- Static website and `/ops`: `apps/website/`
- Dedicated API entry point: `infra/cloudflare/aifred-api/src/index.js`
- API handlers: `infra/cloudflare/aifred-api/src/handlers.js`
- Controlled mobile source edits: `infra/cloudflare/aifred-api/src/source-control.js`
- Pages project name used by deploy tooling: `aifred-site`
- Worker name: `aifred-api`

Production cutover remains pending. Beta retains the current Pages Functions backend until the dedicated Worker passes the migration checklist.
- Production branch: `main`

Cloudflare config roles:

- `apps/website/wrangler.toml` — primary app config and bindings.
- `infra/cloudflare/wrangler.toml` — operations/support mirror.
- `wrangler.jsonc` — root convenience config pointed at `apps/website`.

Do not restore the deleted top-level `website/` source tree or point backend file operations at the retired standalone website repository.

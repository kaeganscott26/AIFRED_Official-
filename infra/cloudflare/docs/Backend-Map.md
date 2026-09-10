# Cloudflare Backend Map

The canonical current backend map is:

- [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md)

This file is retained as an operations entry point so old links under `infra/cloudflare/docs/` do not break, but it must not become a second independent source of backend truth.

Current authority summary:

- Intended production repository: `kaeganscott26/AIFRED_Official-`
- Website/backend source: `apps/website/`
- Worker router: `apps/website/_worker.js`
- Static website, `/ops`, and backend: `apps/website/`
- Unified entry point: `apps/website/_worker.js`
- API handlers: `apps/website/lib/backend/`
- Controlled mobile source edits: `apps/website/lib/backend/source-control.js`
- Pages project name used by deploy tooling: `aifred-site`
- Separate API Worker: none

Production promotion remains pending. Beta retains current Git source authority until the unified Official preview passes the migration checklist.
- Production branch: `main`

Cloudflare config roles:

- `apps/website/wrangler.toml` — primary app config and bindings.
- `infra/cloudflare/wrangler.toml` — operations/support mirror.
- `wrangler.jsonc` — root convenience config pointed at `apps/website`.

Do not restore the deleted top-level `website/` source tree or point backend file operations at the retired standalone website repository.

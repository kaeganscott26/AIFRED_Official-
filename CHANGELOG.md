# Changelog

## Unreleased

- Added the dedicated `aifred-api` replacement Worker contract, local tests, dry-run configuration, rate limiting, queue activity, and storage bindings.
- Restored Android website management through an authenticated, exact-path source-control API with validation and optimistic Git SHA updates.
- Aligned documentation around Pages owning the website and the Worker owning `/api/*` after a separately authorized production cutover.
- Reconciled the shared provider contract and `shared-core` inventory at version 1.2.1.
- Added the backend ownership map, migration checklist, and complete Windows dependency/build/install/update/uninstall guidance.
- Added the website/Cloudflare map and free-Beta versus `$149.99` Flagship presentation.
- Added channel-aware release metadata so the latest public GitHub Beta assets can be served from immutable R2 keys.

No production Cloudflare route, deployment, binding, resource, or secret was changed by these source updates.

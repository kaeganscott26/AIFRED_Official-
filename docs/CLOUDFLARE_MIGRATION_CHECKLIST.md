# Unified Pages production migration checklist

Record repository SHA, deployment ID, command, result, timestamp, and operator. A local or preview pass does not establish production state.

## Recovery and source

- [x] Record both repository starting SHAs/status/logs and fetch without destructive operations.
- [x] Inventory live Pages, routes, deployments, domains, bindings, storage, queues, datasets, and secret names.
- [x] Preserve production deployment `b2b33ea0-e74e-46a0-a6b5-53fb5c5d4b4e` as rollback.
- [x] Confirm no `/api/*` Worker route exists.
- [x] Reconcile the monolithic backend into `apps/website` without changing DSP.
- [x] Remove source conflict markers and Markdown fence corruption; enforce both in checks.
- [ ] Commit and push a fully validated Official source tree.

## Preview

- [ ] Deploy an Official non-production branch to Pages project `aifred-site` using `apps/website`.
- [ ] Confirm preview bindings use preview D1 and do not mutate production D1.
- [ ] Confirm required admin secret names exist in preview; stop authenticated validation if any are absent.
- [ ] Validate website/styles/assets, `/ops`, `/health`, catalog, references, models, analysis, provider/chat when available, admin login/session/dashboard/logout/exports, and source-control concurrency.
- [ ] Validate installer and ZIP HEAD, range, filename, content type, length, and full SHA-256.
- [ ] Build/test Android against preview and validate desktop configuration against preview.
- [ ] Hold website and `/ops` idle for at least five minutes and confirm no uncontrolled traffic. Record any unavailable VST/device manual coverage separately.

## Production promotion

- [ ] Re-record the active production deployment ID immediately before mutation.
- [ ] Apply only required production D1 migrations and seed validated reference metadata.
- [ ] Promote the unified Pages deployment; do not add a second Worker route.
- [ ] Verify apex, `www`, assets, APIs, Ops/admin, clients, downloads, and telemetry/storage.
- [ ] Observe errors and traffic for several minutes; roll back on critical regression.
- [ ] Change Pages source to `kaeganscott26/AIFRED_Official-`, branch `main`, root `apps/website`, only after preview acceptance.
- [ ] Prove an allowlisted Android source edit creates an Official commit and observed Pages deployment.
- [ ] Retain the rollback deployment and leave Beta intact until stability is established.

## Intelligence gate

- [ ] Begin only after backend/site production is green.
- [ ] If `intelligence/` is absent, stop and request restoration; never recreate it from memory.
- [ ] If restored, repair the intelligence skill frontmatter, read the mandated architecture material, and implement Phase 1 only.

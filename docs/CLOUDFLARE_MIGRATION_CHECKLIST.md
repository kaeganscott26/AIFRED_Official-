# Cloudflare production migration checklist

Record the repository SHA, deployment identifier, command, result, timestamp, and operator for each completed item. A local pass does not advance a staging or production status.

## Source preparation

- [ ] Keep the existing Beta production website, Pages Functions, admin surfaces, and rollback source intact.
- [ ] Make Official source, tests, configuration, and documentation internally consistent.
- [ ] Run the Official repository, website, Worker, host, Android, and shared-core checks supported by the build machine.
- [ ] Repair Beta repository/documentation checks and run its shared-core and plugin checks without removing production code.

## Staging

- [ ] Deploy `aifred-api-staging` with the intended staging bindings and secret names.
- [ ] Apply D1 migrations to the selected staging database.
- [ ] Run staging smoke tests for health, models, references, releases/downloads, chat, analysis, analytics, admin auth, Android Admin, desktop Admin, `/ops`, provider/Ollama, D1, R2, Queue, and rate limits.
- [ ] Confirm source-control status without exposing the GitHub credential; test read, validate, conflicting SHA rejection, controlled save, and commit evidence on an approved staging path or branch.
- [ ] Keep the website, VST, Android Admin, and `/ops` idle for at least five minutes. Confirm no repeating website/VST/provider traffic, no Android background traffic, at most one visible Android dashboard refresh per minute, and no hidden-tab `/ops` polling.

## Rollback capture

- [ ] Record both repository SHAs and confirm clean or explain every preserved local change.
- [ ] Export the current deployed-state and resource inventory without secret values.
- [ ] Record Worker/Pages bindings, secret names, routes, domains, deployment identifiers, and the previous live route.
- [ ] Verify the pre-migration recovery bundle still exists and is readable. The dated repository inventory alone does not prove the external bundle remains available.
- [ ] Write the exact rollback and smoke-test commands before changing a production route.

## Production API cutover

- [ ] Obtain separate authorization for production changes.
- [ ] Route only `north3rnlight3r.com/api/*` to `aifred-api`; leave normal Pages routes unchanged.
- [ ] Validate production health, models, references, releases/downloads, chat, analysis, analytics, admin auth, all admin clients, provider/Ollama, D1, R2, Queue, and rate limits.
- [ ] Repeat the five-minute idle-traffic acceptance test in production.
- [ ] Keep the prior API deployment and route available for rollback until acceptance completes.

## Website source authority

- [ ] Reconfigure the Pages Git source from Beta to `kaeganscott26/AIFRED_Official-` only after the production API passes.
- [ ] Deploy and validate the Official website and `/ops` with the dedicated `/api/*` Worker.
- [ ] Confirm Android approved-source commits produce an observable Pages deployment and that the deployed file matches the committed SHA/content.

## Beta retirement

- [ ] Remove Beta website, admin, `/ops`, backend, and production-infrastructure ownership only after both production cutovers pass and rollback evidence exists.
- [ ] Simplify Beta workflows, repository map, and documentation around the standalone plugin boundary.
- [ ] Run Beta standalone plugin CI and release checks.
- [ ] Start the next intelligence architecture phase only after the migration remains stable.

## Status vocabulary

Use one of these labels for each subsystem:

- `IMPLEMENTED IN SOURCE`
- `VALIDATED LOCALLY`
- `VALIDATED IN STAGING`
- `DEPLOYED TO PRODUCTION`
- `NOT YET VERIFIED`

## 2026-09-10 staging evidence

- `VALIDATED LOCALLY`: Worker syntax, 14 Node tests, and the production-config Wrangler dry run passed.
- `VALIDATED IN STAGING`: Worker version `9f0ff56e-b233-40d5-b52e-d4d2bbe75688` passed health, models, D1 references, reference cache HIT, Beta release metadata, R2 installer/ZIP HEAD, admin authentication/status/analytics/providers/dashboard/exports, source-control status, analytics acceptance/idempotency, and logout.
- `VALIDATED IN STAGING`: D1 migration `0003_beta_release_assets.sql` applied; GitHub release assets were mirrored to immutable R2 Beta keys and downloaded back with matching SHA-256 values.
- `NOT YET VERIFIED`: chat JSON, chat SSE, and provider test returned 502 because `ollama.north3rnlight3r.com` does not resolve. A protected replacement Tunnel, DNS record, Access application/policy, and service-token bindings are required before production API cutover.
- `NOT YET VERIFIED`: Android build is blocked on this machine because no JDK is installed or selected.
- `NOT YET VERIFIED`: production Worker route and Official Pages source cutover were not changed while the provider gate remained failed.
- `VALIDATED IN STAGING`: Official Pages preview deployment `42893ba2` uploaded and compiled; the existing Access preview policy returned the expected login redirect to unauthenticated checks.
- Full identifiers and rollback evidence are in [2026-09-10 cutover readiness](cloudflare/2026-09-10-cutover-readiness.md).

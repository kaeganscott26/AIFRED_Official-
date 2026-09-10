# 2026-09-10 production cutover readiness

> Superseded historical record: this file describes the abandoned split-Worker plan. Do not use it as current deployment instruction. Current authority is [Cloudflare production](../CLOUDFLARE_PRODUCTION.md) and the [live recovery baseline](2026-09-10-live-recovery-baseline.md).

This record separates completed staging work from the blocked production cutover. It contains identifiers and secret names only, never secret values.

## Source and rollback baseline

- Official starting branch/SHA: `main` at `7e29a70358e50d099a673065d505d0acf0a3a20c`.
- Beta starting branch/SHA: `main` at `d0e6755e611b9e39e1225c22ee4c554530a8d942`.
- Pre-migration Pages deployment: `02cf2cd3-5af4-4f6c-9ae6-185103abc2ef`, Git source `kaeganscott26/AIFRED` at short SHA `05c4444`.
- Pages project: `aifred-site`; domains: `aifred-site.pages.dev`, `north3rnlight3r.com`, and `www.north3rnlight3r.com`.
- Pre-cutover Pages Git configuration: production branch `main`, automatic production deployments enabled, preview deployment setting `none`, Pages Functions enabled.
- External recovery directory was present at `C:\Users\North\Documents\Projects\AIFRED-recovery\cloudflare-reset-20260908`; both repository bundles passed `git bundle verify` during this pass.

## Artifact proof

GitHub latest release: `kaeganscott26/AIFRED` tag `v0.3.6-beta-stable`, published `2026-09-07T01:30:42Z`.

| Artifact | Bytes | SHA-256 | R2 key |
| --- | ---: | --- | --- |
| `AIFRED-VST3-Setup.exe` | 53,964,697 | `ce9664d2cb3632cf72c3af930377cf3f0b6d15282c5ed1f33c8ec31aa829e71f` | `releases/beta/v0.3.6-beta-stable/AIFRED-VST3-Setup.exe` |
| `AIFRED-VST3-windows.zip` | 2,323,863 | `3bde33e7f30386d29baec937ed0613f2ee09cf5e322f1c76d758c6d78c6f2ea9` | `releases/beta/v0.3.6-beta-stable/AIFRED-VST3-windows.zip` |

Both R2 objects were downloaded after upload and matched the GitHub release digests and byte counts.

## Staging state

- D1 migration `0003_beta_release_assets.sql`: applied remotely with Cloudflare backup behavior.
- Staging Worker: `aifred-api-staging`, version `9f0ff56e-b233-40d5-b52e-d4d2bbe75688`.
- Staging secrets present: `AIFRED_ADMIN_PASSWORD_SHA256`, `AIFRED_ADMIN_SESSION_SECRET`, `AIFRED_ANALYTICS_API_TOKEN`, `AIFRED_API_TOKEN`, `OLLAMA_API_TOKEN`.
- Staging smoke: public API, reference cache, release metadata, R2 downloads, admin authentication/data/exports, source status, analytics idempotency, and logout passed.
- Official Pages preview: deployment `42893ba2`, alias `official-cutover-preview.aifred-site.pages.dev`. Upload and Pages Worker compilation passed; unauthenticated content inspection is blocked by the existing Cloudflare Access preview policy.

## Failed gates and missing configuration

- `ollama.north3rnlight3r.com` does not resolve. Local Ollama is healthy on `127.0.0.1:11434`, but no protected public Tunnel path is available.
- Staging JSON chat, streaming chat, and provider test return 502.
- The available Cloudflare OAuth session can deploy Workers, Pages, D1, R2, and Queues, but its DNS record query was rejected. It does not establish the required Access application/policy and service-token authority.
- Production Worker currently reports no secret names. Production must receive the reviewed server-side secrets before route cutover.
- `GITHUB_TOKEN` is absent from the local/staging secret inventory. Android source read/save remains safely unconfigured until a repository-scoped Contents credential is supplied server-side.
- `OLLAMA_ACCESS_CLIENT_ID` and `OLLAMA_ACCESS_CLIENT_SECRET` are absent. Do not expose the local Ollama port or use an unprotected quick tunnel as a substitute.
- Android build remains blocked because no JDK is installed or selected on this machine.

## Production status

- Dedicated Worker source: `IMPLEMENTED IN SOURCE` and `VALIDATED LOCALLY`.
- Dedicated Worker staging: `VALIDATED IN STAGING` except provider/chat.
- Beta release objects: `VALIDATED IN STAGING` through R2 and Worker HEAD requests.
- Official Pages website: `VALIDATED IN STAGING` for upload/compile; content inspection requires Access authentication.
- Production `/api/*` route: `NOT YET VERIFIED`; no cutover was performed.
- Production Pages source authority: `NOT YET VERIFIED`; the live project remains connected to Beta until the API gate passes.

## Next exact production action

Create a new named Cloudflare Tunnel to `127.0.0.1:11434`, protect it with an Access application and service-token policy, set the resulting DNS record, place only the service-token ID/secret plus the existing Ollama API token in staging Worker secrets, and rerun `node scripts/smoke.mjs https://aifred-api-staging.aifred-site.workers.dev --provider`.

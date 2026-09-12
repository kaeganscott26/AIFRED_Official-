# Cloudflare production guide

## Architecture

```text
north3rnlight3r.com/* -> Pages project aifred-site -> apps/website/_worker.js
                                      -> backend routes or env.ASSETS.fetch
```

The site and application API are one Pages Advanced Mode deployment.
`_worker.js` owns `/health`, `/v1/*`, `/api/*`, `/api/v1/*`, and `/ws/chat`;
static requests fall through to `env.ASSETS`. No second Worker may intercept
production `/api/*`.

`aifred-api-staging` is an isolated Worker for smoke testing. Its current D1,
KV, R2, Analytics, queue, and rate-limit configuration is preserved; matching
the Pages storage bindings does not make it the production route owner.

## Current control-plane state

Pages Git source is `kaeganscott26/AIFRED_Official-`, branch `main`. The Pages
build output directory is `apps/website`; the previous Git deployment failed
because it used the repository-name-prefixed path
`AIFRED_Official-\\apps\\website`. The last successful ad-hoc deployment is
retained as rollback evidence until the corrected Git deployment succeeds.

The apex custom domain is already registered but remains pending because its
zone CNAME is missing. Existing `www` and Access configuration were not
removed. The current Wrangler credential has `zone:read`, not DNS write, so
adding that CNAME requires an authorized Cloudflare DNS administrator.

## Authoritative paths and bindings

| Responsibility | Path/resource |
| --- | --- |
| unified website/backend | `apps/website` |
| request router | `apps/website/_worker.js` |
| Pages configuration | `apps/website/wrangler.toml` |
| backend handlers/tools | `apps/website/lib/backend` |
| release manifest | `apps/website/lib/release-manifest.js` |
| historical staging donor | `infra/cloudflare/aifred-api` |

Production Pages binds D1 `aifred-ops`, R2 `aifred-downloads` and
`aifred-reference-pool`, KV `AIFRED_REFERENCE_POOL` and `AIFRED_SALES_LOG`, and
Analytics Engine dataset `aifred_events`. The staging Worker uses the same
storage resources, staging Analytics dataset, and its existing staging queue
and rate-limit namespaces. Production Pages has no Queue dependency.

## Release artifacts

The website advertises only the public Beta channel, and the download route
reads the exact keys below from `AIFRED_DOWNLOADS`:

| Artifact | Source | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `AIFRED-VST3-Setup.exe` | Beta `out/windows-x64/current` | 53,930,848 | `d0731bfa6afdf5af02e9429bd03a847d7d06df1e549760c04fe5548bb3ae3421` |
| `AIFRED-VST3-windows.zip` | Beta `out/windows-x64/current` | 2,363,132 | `9cbcebbefe1928bbd7f5fd533abbc3136d7fcbcd6059ec72fbb3d108305a8d36` |

The ZIP contains the VST3, `AifredIntelligenceHost`, channel/configuration
files, and README from the verified Beta current artifact. Shared DSP is
compiled into the VST3 and is not a separate runtime folder. The Official
`out/windows-x64/current` alpha artifact has no public download route. If an
R2 object is missing or its size differs, the API returns unavailable and does
not redirect to an external or stale binary.

## Secrets and validation

Admin authentication requires `AIFRED_ADMIN_USERNAME`,
`AIFRED_ADMIN_PASSWORD_SHA256`, and `AIFRED_ADMIN_SESSION_SECRET`.
`GITHUB_TOKEN` supports only the approved Official text-file source controls.
Provider credentials remain Worker-managed. Record names only; never print or
commit values.

```powershell
npm ci --prefix apps
npm --prefix apps run website:check
npm --prefix apps run website:preview
npm --prefix apps run website:deploy
```

After deployment, verify repository HEAD, Pages deployment ID, static assets,
`/health`, `/api/health`, `/api/v1/reference/pool`, `/v1/models`, authenticated
admin routes, download HEAD metadata and full artifact hashes. Wait five idle
minutes before making idle-traffic claims. Treat source, automation, preview,
production, installed APK, and manual plugin/DAW evidence as separate records.

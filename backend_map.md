# AIFRED backend map — current recovery state

Updated 2026-09-11. This is the single current backend map. Older migration documents are historical.

## Live production versus recovered source

| Item | Verified state |
| --- | --- |
| Public domains | `north3rnlight3r.com`, `www.north3rnlight3r.com` |
| Cloudflare project | Existing Pages project `aifred-site`; both custom domains active |
| Current production deployment | `3adb682f-48c4-4380-ade8-ed320fc7faf5` (preserved rollback) |
| Current production recorded commit | Beta `468f06ed859d0887ffd86f0f997370944aabbe24` |
| Current Pages Git source | Absent in live API response; Git automation/source reassignment is not verified |
| Recovered source authority | `kaeganscott26/AIFRED_Official-`, `apps/website` |
| Recovered preview | `https://recovery-completion.aifred-site.pages.dev` |
| Production promotion | Not performed: configured Ollama connection fails acceptance |
| Zone Worker routes | None; neither API Worker owns a production domain route |

Live production `/styles.css` and `/app.js` return 404. Pages build root/output are empty and the recorded deployment uses the Beta revision whose website/backend files were removed. Official's CSS matches the known-good recovery CSS byte-for-byte. The recovered preview renders the intended styled website and Ops console. Current HTML prose is preserved except malformed download markup, unsupported platform links, and unreleased product advertising.

## One request router

`apps/website/_worker.js` is the only runtime entry point. It imports `lib/backend/index.js` and explicitly invokes the WebSocket compatibility handler; Pages file routing is not relied on.

| Request | Dispatch |
| --- | --- |
| `www.north3rnlight3r.com/*` | 308 to the same path/query on the apex |
| `/health` | Backend health |
| `/api`, `/api/*`, `/api/v1`, `/api/v1/*` | Backend; strip `/api` and use versioned contracts; unknown routes return JSON 404 |
| `/v1`, `/v1/*` | Same backend compatibility contracts |
| `/ws/chat` | Explicit WebSocket adapter to the same chat handler |
| `/ops`, `/ops.html` | Real Ops static frontend through `env.ASSETS.fetch(request)` |
| Every other path | `env.ASSETS.fetch(request)`; missing files use a real 404 page |

Browser config derives `window.location.origin`; browser/admin API prefix is `/api/v1`. Both existing native host source copies normalize AIFRED origins to `/api/v1`. The recovered backend accepts both `beta` and `official` measured-context identities. No plugin/host source was changed or rebuilt in recovery.

## Chat and references

Chat: client -> `/api/v1/chat/completions` (also `/v1/chat/completions`) -> `_worker.js` -> `lib/backend/handlers.js` -> `providers.js` -> `OLLAMA_BASE_URL/v1/chat/completions`. Existing client/admin authentication, context validation, idempotency and D1 rate limits remain enforced. `OLLMA_MODEL` remains a compatible alias for the deployed legacy spelling. No new provider was introduced.

The existing `aifred-ollama` tunnel (`d4c779b6-a550-4058-b4de-3368451045c3`) reports healthy, but its remote configuration is null and the zone has no Ollama hostname record. Preview provider test and chat return 502. Phase 13's DNS restriction prevents silently adding that hostname. Production promotion remains pending this connection repair and successful provider validation.

References: `/api/v1/reference/pool`, `/v1/reference/pool`, and `/api/v1/references` read the existing `aifred-ops.references_catalog`. Both pool routes returned the 22 real active records in preview. Existing KV/R2 reference contents were not changed; no reference database was created. Browser metadata submission uses the existing recovered reference gate; native analysis remains separately authenticated.

## Existing storage and bindings

| Binding | Resource / use |
| --- | --- |
| `ASSETS` | Pages static assets |
| `AIFRED_OPS` | D1 `aifred-ops`, `60d95cd8-d1da-486c-b6fd-4bfedcd7bc47`: references, inquiries, sessions, idempotency, limits, activity and rollups |
| `AIFRED_DOWNLOADS` | R2 `aifred-downloads`: pinned Beta binaries and compatibility catalog media |
| `AIFRED_REFERENCE_BUCKET` | Existing R2 `aifred-reference-pool`, retained reference assets; pool reads use D1 |
| `AIFRED_REFERENCE_POOL` | Existing KV `8a120701767e474f928d1af7037cd68a`, historical compatibility, no request-time list |
| `AIFRED_SALES_LOG` | Existing KV `2c66da7795b54135a4d67e514b97491f`, historical compatibility, no event writes |
| `AIFRED_ANALYTICS` | Preview `aifred_events_preview`; production config `aifred_events`; optional telemetry |

Production at the baseline has the two KV and two R2 bindings but no D1/Analytics binding. Recovered preview binds canonical D1 and the existing preview Analytics dataset. The deploy configuration will supply existing resources at promotion. No Queue dependency exists in the Pages runtime. `wrangler pages download config` was run into ignored scratch space and compared before deployment; production secret values were never overwritten.

## Public Beta downloads and catalog

Only AIFRED Beta is public: `kaeganscott26/AIFRED`, tag `v0.3.6-beta-stable`. `lib/release-manifest.js` pins these objects:

| Artifact | R2 key | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Windows installer | `releases/beta/v0.3.6-beta-stable/AIFRED-VST3-Setup.exe` | 53,964,697 | `ce9664d2cb3632cf72c3af930377cf3f0b6d15282c5ed1f33c8ec31aa829e71f` |
| Windows ZIP | `releases/beta/v0.3.6-beta-stable/AIFRED-VST3-windows.zip` | 2,323,863 | `3bde33e7f30386d29baec937ed0613f2ee09cf5e322f1c76d758c6d78c6f2ea9` |

Routes: `/api/v1/downloads/plugin?channel=beta&asset=setup` and `asset=zip`. HEAD and GET 200, byte-range 206, filename, content type, length and full-file SHA-256 passed in preview and match the public GitHub release. Unpublished release metadata is not returned by the public listing; its private placeholder remains. No Official binary was uploaded. Download buttons appear only after matching HEAD verification.

The unchanged catalog contains 53 real tracks. All 53 referenced MP3s were recovered from `.codex/skills/AIFRED-3.6-Beta RECOVERY_REFERRENCE_ONLY/apps/website/assets/audio/catalog/` into `apps/website/assets/audio/catalog/`. Catalog data and three existing images already matched or resolved; no entries were fabricated. The full 58-file referenced asset graph passes exact-case, existence, nonempty and Pages size-limit checks. Representative static MP3 GETs and existing `/api/v1/assets/audio/catalog/*` R2 range requests passed.

## Ops and credentials

Preview `/ops`, `/ops.html`, `/ops.css`, `/ops.js` pass HTTP/content-type checks and a browser-rendered screenshot confirms styling. Login/logout, status, dashboard/state, providers, references, analytics, exports, source list/status/read/validation pass. Source-save rejects non-allowlisted paths; optimistic concurrency has automated coverage. No arbitrary path writes or synthetic reference inserts were performed.

Production encrypted names preserved: `AIFRED_ADMIN_PASSWORD_SHA256`, `AIFRED_ADMIN_SESSION_SECRET`, `AIFRED_ADMIN_USERNAME`, `AIFRED_CHAT_PROVIDER`, `AIFRED_PLUGIN_RELEASE_TAG`, `AIFRED_RELEASE_VERSION`, `Cloudflaireapi`, `GITHUB_TOKEN`, `OLLAMA_BASE_URL`, `OLLMA_MODEL`.

Preview reused existing local credential values for `AIFRED_API_TOKEN`, `AIFRED_ANALYTICS_API_TOKEN`, the three admin names, `AIFRED_CHAT_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_API_TOKEN`, and `GITHUB_TOKEN`. A preview binding reconciliation initially passed the API's redacted GitHub value back; the preview binding was recovered with the existing locally configured fine-grained PAT, and authenticated Official source reads now pass. Production bindings were untouched. No credential was generated or rotated.

`AIFRED-AUTH`: the available local GitHub credential is a fine-grained PAT and can read Official. Its human-assigned label cannot be verified with the available GitHub API session; an App lookup for `aifred-auth` returned 404. No replacement GitHub credential was created. Production `GITHUB_TOKEN` remains unchanged and awaits production runtime validation.

`aifred-api-staging` remains an isolated donor Worker with no production route. Old `aifred-api` has no zone route and was not deployed or revived. Its local donor configuration no longer declares a production route, and its documentation is explicitly obsolete.

## Deployment and validation boundary

Use `npm --prefix apps run website:check`, then `npm --prefix apps run website:preview`. Pages ignores `.assetsignore`; `tools/deploy-website.mjs` packages only the public files/assets and bundled router from `apps/website` into a retained temporary mirror. Private backend/config/SQL paths return 404 in that preview. The router and static source remain entirely in Official; no Beta runtime dependency exists.

Local tests: 13 passing backend/frontend contracts plus syntax/import, asset graph, command-registry and repository checks. Protected plugin/DSP/host/CMake/installer paths have zero diff against recovery start `656ead82648405cfdab206a9cf7db17099900fef`. Beta remains clean at `468f06ed859d0887ffd86f0f997370944aabbe24` with no tracked website/API tree. No VST was built, installed, packaged or released; DAW coverage is not claimed.

Real remaining defects: Ollama DNS/ingress and provider 502; production promotion/bindings/source automation still pending; production authenticated Ops/GitHub validation pending; `AIFRED-AUTH` label not independently confirmed. The currently broken production deployment has deliberately not been replaced while required provider acceptance is failing.

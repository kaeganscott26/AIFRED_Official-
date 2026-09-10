# AIFRED API reference

Production candidate base: `https://north3rnlight3r.com/api`.

The dedicated `aifred-api` Worker implements this contract. The source exists in Official, but production routing remains unverified until the authorized cutover and smoke test complete. Staging `workers.dev` URLs may expose the same paths without the `/api` prefix for validation only.

## Public and product routes

| Method | Production path | Auth | Behavior |
| --- | --- | --- | --- |
| GET/HEAD | `/api/health` | No | Constant-time service and contract health |
| GET/HEAD | `/api/v1/models` | No | Configured public model descriptors |
| GET/HEAD | `/api/v1/catalog/list` | No | Static Official catalog metadata |
| GET/HEAD | `/api/v1/releases` | No | Flagship release metadata from D1 |
| GET/HEAD | `/api/v1/releases/current` | No | Current flagship release metadata |
| GET/HEAD | `/api/v1/references` | No | Sanitized D1-backed reference catalog |
| GET/HEAD | `/api/v1/reference/pool` | No | Alias of the sanitized reference catalog |
| POST | `/api/v1/chat/completions` | Product/admin token | OpenAI-compatible request with `FilteredMixContext` and `Idempotency-Key` |
| POST | `/api/v1/analysis` | Product/admin token | Bounded `FilteredMixContext` submission |
| POST | `/api/v1/analysis/submit` | Product/admin token | Alias of analysis submission |
| POST | `/api/v1/analyzer/submit` | Product/admin token | Alias of analysis submission |
| POST | `/api/v1/analytics/events` | Product token or allowed same-site browser | Sanitized batch of 1–50 events |
| POST | `/api/v1/activity/record` | Product token or allowed same-site browser | Alias of analytics ingestion |
| POST | `/api/v1/inquiries` | No | Bounded contact inquiry |
| POST | `/api/v1/inquiries/submit` | No | Alias of inquiry submission |
| GET/HEAD | `/api/v1/downloads/plugin?asset=setup\|zip\|macos` | No | Allowlisted release object from R2 |
| GET/HEAD | `/api/v1/assets/<approved-key>` | No | Known R2 object with Range support |

Public models and releases cache for 15 minutes. References cache for five minutes. Admin, chat, analysis, inquiry, and analytics responses use `Cache-Control: no-store`.

## Measurement contract

Chat and analysis accept AIFRED-owned `aifred.filtered-mix.v1` context only. The Worker checks the Official channel, profile revision, 16 metric identities/units, and exact 30-band frequency contract. The provider may interpret this context but cannot redefine DSP truth.

## Admin session and operations

`POST /api/v1/admin/login` accepts the configured username and password over HTTPS. Success returns a bounded signed session. `POST /api/v1/admin/logout` revokes it. All other admin routes require the returned bearer session.

Read routes:

- `GET /api/v1/admin/status` and `/ops/status`
- `GET /api/v1/admin/analytics`
- `GET /api/v1/admin/activity` and `/logs/list`
- `GET /api/v1/admin/inquiries` and `/inquiries/list`
- `GET /api/v1/admin/releases`
- `GET /api/v1/admin/reference/list`
- `GET /api/v1/admin/catalog/list`
- `GET /api/v1/admin/dashboard/state`
- `GET /api/v1/admin/providers` and `/providers/ollama`
- `GET /api/v1/admin/export/site` and `/export/tracks`

Provider checks run only after an explicit `POST /api/v1/admin/provider/test` or `/providers/ollama/test` request. Dashboard and health requests never probe Ollama.

## Android website-source administration

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/admin/source/files` | Return the exact editable Official website-file allowlist |
| GET | `/api/v1/admin/source/status` | Report repository, branch, credential presence, and unverified deployment state without secrets |
| POST | `/api/v1/admin/source/read` | Read one approved file and return its Git blob SHA |
| POST | `/api/v1/admin/source/validate` | Validate an approved text draft without writing |
| POST | `/api/v1/admin/source/save` | Commit a validated update with the loaded SHA and an `Idempotency-Key` |

The Worker accepts eight named text files under `apps/website`. It rejects path traversal, directory access, arbitrary files, deletion, file creation, and binary uploads. Save requires `GITHUB_TOKEN` in the Worker environment and a fine-grained credential limited to Official repository contents. The phone never receives that credential.

The save response contains commit evidence and `deployment.verified: false`. Confirm the Pages deployment after every commit. Official has not yet replaced Beta as the verified Pages source.

## Storage authority

D1 `references_catalog` owns structured public reference records. The request path does not list the legacy KV namespace. D1 also owns releases, inquiries, sessions, idempotency, activity, and rollups. R2 owns release/media bytes; Queue and Analytics Engine handle operational telemetry.

## Local AifredIntelligenceHost

Beta uses `http://127.0.0.1:8787`; Official uses `http://127.0.0.1:8788`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Host/channel/schema and provider availability |
| POST | `/chat` | User message plus strict `FilteredMixContext` |
| GET/POST | `/v1/settings` | Redacted provider settings read/update |

The local host remains separate from the Cloudflare control plane and makes no provider request while idle.

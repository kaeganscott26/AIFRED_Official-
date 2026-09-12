# AIFRED API reference

The canonical application API is the same-origin Pages backend:
`https://north3rnlight3r.com/api/v1`. The apex is the intended production
origin; until its pending DNS verification is complete, validate against the
healthy `aifred-site.pages.dev` deployment. `/v1/*` is retained for native and
OpenAI-compatible compatibility routes.

## Public and product routes

| Method | Path | Auth | Behavior |
| --- | --- | --- | --- |
| GET/HEAD | `/api/health` | No | Service and contract health |
| GET/HEAD | `/api/v1/models` | No | Configured public model descriptors |
| GET/HEAD | `/api/v1/catalog/list` | No | Official catalog metadata |
| GET/HEAD | `/api/v1/releases` and `/current` | No | Published Beta release metadata |
| GET/HEAD | `/api/v1/references` and `/reference/pool` | No | Sanitized D1 reference catalog |
| POST | `/api/v1/chat/completions` and `/chat/ask` | Product/admin token | Provider-backed chat grounded in bounded `FilteredMixContext` |
| POST | `/api/v1/analysis` and `/analysis/submit` | Product/admin token | Bounded analysis submission |
| POST | `/api/v1/analyzer/submit` | Product/admin token | Analysis alias |
| POST | `/api/v1/analytics/events` and `/activity/record` | Product token or same-site browser | Sanitized activity batch |
| POST | `/api/v1/inquiries` and `/inquiries/submit` | No | Bounded contact inquiry |
| GET/HEAD | `/api/v1/downloads/plugin?asset=setup\|zip` | No | Pinned public Beta R2 artifact |
| GET/HEAD | `/api/v1/assets/<approved-key>` | No | Known R2 object with Range support |
| GET/HEAD | `/api/v1/registry/actions` | No | Backend command metadata for admin clients |
| GET/HEAD | `/api/v1/chat/settings` | No | Redacted chat runtime settings |

Public models/releases cache for 15 minutes and references for five minutes.
Admin, chat, analysis, inquiry, and analytics responses are `no-store`.

## Measurement contract

Chat and analysis accept AIFRED-owned `aifred.filtered-mix.v1` context only.
The backend validates channel, profile revision, metric identities/units, and
the exact 30-band frequency contract. A provider may interpret that context;
it cannot redefine DSP truth, snapshots, session state, or evidence authority.

## Admin session and operations

`POST /api/v1/admin/login` accepts the owner credential over HTTPS and returns
a bounded signed bearer session. `POST /api/v1/admin/logout` revokes it. Other
admin routes require that session.

Read routes:

- `/api/v1/admin/status` and `/ops/status`
- `/api/v1/admin/analytics`, `/activity`, `/logs/list`, `/inquiries/list`,
  `/releases`, `/reference/list`, `/catalog/list`, `/sales/list`
- `/api/v1/admin/dashboard/state`
- `/api/v1/admin/providers` and `/providers/ollama`
- `/api/v1/admin/export/site` and `/export/tracks`

Mutating/explicit routes:

- `POST /api/v1/command/run` accepts only the server allowlist and never runs
  arbitrary shell or filesystem input.
- `POST /api/v1/admin/api/config` saves provider routing in the existing
  runtime KV; `POST /api/v1/admin/api/test` probes only the requested provider.
- `GET /api/v1/admin/chat/settings` reads authenticated settings, including the
  operator-entered webhook secret; the public settings route is redacted.
  `POST /api/v1/admin/chat/settings/save` saves bounded chat settings.
- `POST /api/v1/admin/catalog/upload` and `/reference/upload` use controlled
  R2 storage; `POST /catalog/remove` updates the approved catalog source.
- Provider checks occur only after an explicit request. Health/dashboard
  requests never probe Ollama.

## Android website-source administration

`GET /api/v1/admin/source/files` returns the exact eight-file Official text
allowlist. `POST /source/read` returns current text plus its Git blob SHA;
`POST /source/validate` validates without writing; and `POST /source/save`
requires that SHA plus an `Idempotency-Key` before committing to Official.

The backend rejects path traversal, directory access, arbitrary files,
deletion, creation, and binary website-asset uploads. `GITHUB_TOKEN` remains
server-held. A commit SHA is source evidence only; verify the resulting Pages
deployment separately.

## Storage and local host

D1 `references_catalog` owns structured public references; D1 also owns
sessions, idempotency, limits, activity, and rollups. R2 owns release/media
bytes. KV remains historical compatibility and sales storage. Analytics Engine
receives optional telemetry; production Pages has no Queue dependency.

Beta uses `http://127.0.0.1:8787`; Official uses `http://127.0.0.1:8788` for
the local AifredIntelligenceHost. The local host remains independent of
Cloudflare and makes no provider request while idle.

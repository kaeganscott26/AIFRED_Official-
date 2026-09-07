# AIFRED API Reference

Production origin: `https://www.north3rnlight3r.com`. Function responses use JSON. Administrative/chat responses use `Cache-Control: no-store`; the sanitized shared reference pool may use short public/edge caching. `/api/*` is a compatibility shim to the canonical `/api/v1/*` implementation.

## Canonical public contract

| Method | Path | Auth | Behavior |
| --- | --- | --- | --- |
| GET | `/health` | No | API health and contract version |
| GET | `/v1/models` | No | OpenAI-compatible model list; may be empty when no provider is configured |
| POST | `/v1/chat/completions` | Provider-dependent | OpenAI-compatible chat; supports JSON or SSE with `stream: true` |
| GET/HEAD | `/api/v1/reference/pool` | No | Sanitized shared reference/analysis measurements for Beta and AIFRED 4; licensed audio and owner secrets are never returned |
| GET/HEAD | `/v1/reference/pool` | No | Alias of the sanitized shared reference pool |
| POST | `/api/v1/analysis/submit` | No | Browser analysis/reference gate submission |
| POST | `/api/v1/analyzer/submit` | No | Alias of analysis submission |
| GET | `/api/v1/catalog/list` | No | Catalog with controlled media URLs |
| GET/HEAD | `/api/v1/downloads/plugin?asset=setup\|zip\|macos` | No | Allowlisted R2 release download |
| GET/HEAD | `/api/v1/assets/audio/catalog/<file>` | No | Catalog stream; Range supported; `download=1` requests attachment |
| POST | `/api/v1/activity/record` | No | Allowlisted public activity event; cannot forge admin/server events |
| POST | `/api/v1/inquiries/submit` | No | Contact inquiry persistence in activity KV |
| GET | `/api/v1/content/get` | No | Website content/config payload |
| GET | `/api/v1/chat/settings` | No | Non-secret client chat settings |

## Reference-pool public schema

`GET /api/v1/reference/pool` returns `aifred.reference-pool.public.v1` with a bounded `records` array. Each record may expose the reference ID, timestamp, duration, measurement payload and sanitized classification/utility fields. It intentionally omits licensed audio objects, repository credentials, storage credentials, admin secrets and original private storage paths.

The source of truth is the Cloudflare `AIFRED_REFERENCE_POOL` KV binding. Beta and AIFRED 4 consume the same contract rather than maintaining channel-specific cloud copies.

## Admin session and operations

`POST /api/v1/admin/login` accepts JSON `username` and `password`. Success returns a signed bearer session. All `/api/v1/admin/*` data/operation routes require `Authorization: Bearer <session>`.

Key admin routes:

- `GET /api/v1/admin/dashboard/state`
- `GET /api/v1/admin/ops/status`
- `GET /api/v1/admin/logs/list`
- `GET /api/v1/admin/inquiries/list`
- `GET /api/v1/admin/sales/list`
- `GET /api/v1/admin/catalog/list`
- `GET /api/v1/admin/reference/list`
- `GET /api/v1/admin/export/site`
- `GET /api/v1/admin/export/tracks`
- `GET/POST /api/v1/admin/api/config`
- `GET/POST /api/v1/admin/api/test`
- `POST /api/v1/admin/chat/settings/save`
- `POST /api/v1/admin/catalog/upload`
- `POST /api/v1/admin/reference/upload`
- `POST /api/v1/admin/files/read|write|list|delete|upload`

## Authentication domains

Do not use one universal credential for unrelated authorities.

- Public reference/catalog/download reads: no owner secret.
- Admin console: signed AIFRED admin session.
- Website model provider: provider secret managed server-side or locally by the user's selected provider configuration.
- Cloudflare deployment/API management: Cloudflare credential or native Git integration.
- GitHub repository write operations: scoped GitHub credential.
- R2 external S3 tooling: optional bucket-scoped S3 credential.

See [Ecosystem Configuration](ECOSYSTEM_CONFIGURATION.md).

## Local AifredIntelligenceHost API

Beta uses `http://127.0.0.1:8787`; AIFRED 4 / Official uses `http://127.0.0.1:8788`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | host/channel/schema and provider/model availability |
| POST | `/chat` | message plus strict `FilteredMixContext` |
| GET/POST | `/v1/settings` | redacted settings read / configured provider changes |

The local Intelligence Host remains separate from the Cloudflare control plane.

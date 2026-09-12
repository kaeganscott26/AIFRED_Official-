# AIFRED Administration Guide

The web `/ops` console, Android Admin, desktop Admin, Beta plugin, and Official
plugin share the same application API and production deployment authority:
`https://north3rnlight3r.com/api/v1`. Credentials and provider secrets remain
server-side.

| Capability | Android | `/ops` | Windows/macOS Admin |
| --- | --- | --- | --- |
| Authenticated live status | Yes | Yes | Yes, through `/ops` |
| Analytics, downloads, logs, inquiries | Yes | Yes | Yes, through `/ops` |
| Catalog/reference/track analysis | Yes | Yes | Yes |
| Site and track exports | Yes | Yes | Yes |
| Approved website text source | Read, validate, commit | No | No |
| Registered backend commands | Yes | No | No |
| Local diagnostics | Android only | No | No |

## Android Admin

The Compose app has Chat, Upload, and Command tabs. Upload restores catalog
audio metadata and licensed-reference intake through controlled R2 routes.
Command restores the server action registry, authenticated allowlisted commands,
catalog/sales/reference/log/inquiry/dashboard actions, exports, and the eight
approved Official website text-file controls. Chat restores server chat-settings
load/save and provider configuration/test controls while keeping phone chat
request-driven over HTTP.

The app never sends a shell command to the backend for execution. The backend
allowlist is explicit, authenticated, and argument-free. Local diagnostic
actions are separate, read-only, non-root phone actions. Website source editing
requires the current Git blob SHA and cannot create/delete/traverse arbitrary
paths or upload binary website assets.

## `/ops`

Open `/ops` on the canonical site and sign in. It provides Overview, Analytics,
Downloads, Track Analysis, API, Logs, Inquiries, Exports, FORGE, and Archive
panels. Operational responses are authenticated and `no-store`; refresh is
manual. `/ops` has no terminal parser and does not replace Android’s registered
command surface.

## Provider and deployment boundaries

Provider tests are explicit actions only. AIFRED measurements, snapshots,
FilteredMixContext, session state, and evidence rules remain AIFRED-owned; the
provider only interprets them. Production deployment is the Pages project
`aifred-site`; `aifred-api-staging` is isolated smoke infrastructure and is
not a second `/api/*` production router.

For command details see [Administrator Command Reference](ADMIN_COMMAND_REFERENCE.md).
For Cloudflare bindings and current live evidence see [backend_map.md](../backend_map.md).

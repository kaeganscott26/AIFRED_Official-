# Official backend map

This map describes source ownership. It does not claim that production traffic has moved.

## Target request path

```text
north3rnlight3r.com/*      -> Cloudflare Pages -> apps/website
north3rnlight3r.com/api/*  -> aifred-api Worker -> infra/cloudflare/aifred-api
```

The dedicated Worker is implemented and locally validated as the replacement backend. Production cutover is pending an authorized staging deployment, smoke tests, rollback capture, and route change. The public Beta repository remains the live fallback until those steps are complete.

## Source ownership

| Surface | Official source | Runtime owner | Current migration status |
| --- | --- | --- | --- |
| website HTML/CSS/JS/assets | `apps/website/` | Cloudflare Pages | implemented in source; production authority not verified |
| public and authenticated API | `infra/cloudflare/aifred-api/` | dedicated Cloudflare Worker | locally validated migration candidate |
| Android Admin | `apps/admin-android/` | installed Android application | controlled website editor implemented; device validation pending |
| desktop Admin | `apps/admin-desktop/` | installed desktop application | source owner; production compatibility requires staging validation |
| web operations console | `apps/website/ops/` | Pages plus Worker API | source owner; production compatibility requires staging validation |
| VST3 | `plugin-aifred/` | DAW process | Official/flagship channel |
| local provider transport | `tools/AifredIntelligenceHost/` | localhost channel host | uses canonical API/client headers; provider remains replaceable |
| shared measurements | `shared-dsp/`, `aifred_engine/`, `BufferHunter/`, `aifred_filter/` | plugin process | pinned by `shared-core.lock.json`; measurement truth remains local |

## Worker storage and services

The Worker configuration declares D1, R2, KV, Queue, Analytics Engine, and rate-limit bindings. Ollama or another provider is reached through the configured provider route. Secret values stay in Cloudflare secret storage and are never committed.

Android website editing uses an authenticated Worker boundary. It can list an exact allowlist, read and validate text source, and update an existing file with its expected Git blob SHA. The Worker holds the GitHub credential; the APK does not. Arbitrary paths, deletes, binary uploads, and host-filesystem access are excluded.

## Traffic policy

- The VST makes no periodic Cloudflare request merely because it is open.
- Android dashboard refresh is bounded, foreground-only, and lifecycle-aware.
- Android chat starts on user Send, not with a keepalive session.
- Hidden web operations tabs do not poll continuously.
- Website analytics is batched.

See [Cloudflare production](docs/CLOUDFLARE_PRODUCTION.md), [migration checklist](docs/CLOUDFLARE_MIGRATION_CHECKLIST.md), and [API reference](docs/API_REFERENCE.md).

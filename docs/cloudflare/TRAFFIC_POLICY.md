# Production API traffic policy

The production API is request-driven and should be quiet while clients are idle. The canonical
base is `https://north3rnlight3r.com/api`; `workers.dev` is not a client endpoint.

## Caller audit (2026-09-08)

| Caller | Previous behavior | Production policy |
| --- | --- | --- |
| Official VST reference client | Fetch on first opening Reference mode and manual Refresh | Retained; never called from the audio callback and never periodic |
| Official VST Intelligence Host | Local health ping every five seconds to `127.0.0.1:8788` | Retained as local process health only; it does not call Cloudflare or Ollama |
| Official VST chat | User action only | Adds stable client/channel/version/purpose headers and an idempotency key; no automatic retries |
| Android Admin dashboard | Full production dashboard every eight seconds while signed in | Changed to immediate foreground load plus 60-second foreground-only refresh; hidden activities make no requests; manual refresh remains |
| Android Admin chat | Opened a WebSocket and sent `Session start` during screen startup | Removed; model catalog loads once and chat is HTTP only after Send; concurrent Send actions are suppressed |
| Android website source | Unsafe broad file routes were available | Load, validate, commit, and status are explicit user actions against eight approved Official text files; no polling |
| Web Ops | Initial load and manual Refresh | Retained; no interval or hidden-tab polling exists |
| Windows/macOS Desktop Admin | Button-driven calls or embedded Web Ops | Retained; no timer or background refresh exists |
| Website public data | Same-origin discrete requests | Public model/release/reference reads are edge-cached; public analytics must use bounded batches |

The JUCE editor's 60 Hz timer drains realtime-safe local UI state. It is not a network timer.
Android's 200 ms playback-position loop reads only the local `MediaPlayer` while audio is playing.

## Layered request defense

1. Cloudflare always-on DDoS protection.
2. One consolidated zone-level rate-limit rule for the five expensive POST paths. The zone is on
   the Free plan, which currently permits one rate-limiting rule, so route-specific enforcement is
   performed in the Worker.
3. Worker Rate Limiting bindings keyed by authenticated client/session where possible:
   chat 15/minute, analysis 10/minute, analytics batches 20/minute, inquiry 5/minute,
   admin login 5/minute, reference submission 20/minute, authenticated admin reads 60/minute.
4. Bounded body/schema/auth/idempotency checks before provider or storage work.
5. Queue/Analytics Engine/D1/R2/Ollama only after the request passes the earlier layers.

The source-controlled edge rule is `infra/cloudflare/aifred-api/scripts/configure-edge-rate-limit.mjs`.
The current OAuth token can inventory rulesets but lacks zone WAF edit scope; applying this script
requires a narrowly scoped token with `Zone WAF:Edit` for `north3rnlight3r.com`.

## Cache and storage policy

- `/api/health`: constant-time, no-cache, and no bindings/provider calls.
- `/api/v1/models`: 15-minute public cache plus one-hour stale window.
- `/api/v1/releases` and `/current`: 15-minute public cache plus one-hour stale window.
- `/api/v1/references`: five-minute public cache plus 15-minute stale window; the structured index is in D1 and does not list KV/R2.
- Admin, chat, analysis, login/logout, inquiries, and analytics are `no-store`.
- R2 requests resolve an allowlisted/known key and never list buckets.
- Each API request writes one Analytics Engine point and queues a sanitized metric. The Queue
  consumer groups identical dimensions into minute rollups before a D1 batch transaction.
- Analytics clients submit 1–50 events under one idempotent batch request. KV is not an event log.

## Idle acceptance test

After cutover, keep the ordinary website, VST, and admin surfaces idle for at least five minutes.
Use `/api/v1/admin/analytics` and Worker Logs to verify:

- ordinary website: no repeating API traffic;
- VST: no Cloudflare traffic without Reference/Chat/Analysis user action;
- Android Admin: at most one dashboard request per visible minute and none while hidden;
- Web/Desktop Ops: no periodic traffic unless a deliberate refresh is enabled later;
- no provider calls or Ollama generation while idle;
- no GitHub/source-control calls without an explicit Android Admin action;
- unexpected routes/clients are identifiable by hashed client key, route, purpose, status,
  rate-limit outcome, and cache status.

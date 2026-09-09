# Cloudflare pre-migration inventory

Captured on 2026-09-08 before the `aifred-api` production cutover. This is the recovery record for the full backend reset. Secret values are intentionally excluded.

## Authority and zone

- Cloudflare account: `Kaeganscott26@gmail.com's Account`
- Zone: `north3rnlight3r.com` (`66dfa87495207b3272df1882ac0dcc18`)
- Zone status/type: active/full
- Authoritative nameservers: `phil.ns.cloudflare.com`, `samara.ns.cloudflare.com`
- Registrar configuration and nameservers were not changed.
- Full BIND-style export: [north3rnlight3r.com.pre-migration.zone](north3rnlight3r.com.pre-migration.zone)

## DNS records

Cloudflare TTL `1` means automatic. No record had a comment or tag.

| Name | Type | Content | TTL | Proxied | Priority |
|---|---|---|---:|---|---:|
| `north3rnlight3r.com` | CNAME | `aifred-site.pages.dev` | Auto | yes | - |
| `www.north3rnlight3r.com` | CNAME | `aifred-site.pages.dev` | Auto | yes | - |
| `north3rnlight3r.com` | MX | `route1.mx.cloudflare.net` | Auto | no | 52 |
| `north3rnlight3r.com` | MX | `route2.mx.cloudflare.net` | Auto | no | 95 |
| `north3rnlight3r.com` | MX | `route3.mx.cloudflare.net` | Auto | no | 100 |
| `north3rnlight3r.com` | TXT | `v=spf1 include:_spf.mx.cloudflare.net ~all` | Auto | no | - |
| `cf2024-1._domainkey.north3rnlight3r.com` | TXT | Cloudflare Email Routing DKIM public key; exact value retained in zone export | Auto | no | - |
| `_dmarc.north3rnlight3r.com` | TXT | `v=DMARC1; p=none; rua=mailto:a5200b5d05db4bb7a1f0cb02050d13db@dmarc-reports.cloudflare.net` | Auto | no | - |

There were no `api` or `ollama` DNS records, CAA records, or verification TXT records in the zone at capture time.

## Website and Pages

- Pages project: `aifred-site`
- Custom domains: `north3rnlight3r.com`, `www.north3rnlight3r.com` (both active)
- Pages subdomain: `aifred-site.pages.dev`
- Git source: `kaeganscott26/AIFRED`, branch `main`
- Build destination: `apps/website`
- Pages Functions: enabled (`pages-worker--12950378-production`)
- Existing Pages deployments and website assets were retained.
- Production bindings:
  - KV: `AIFRED_REFERENCE_POOL`, `AIFRED_SALES_LOG`
  - R2: `AIFRED_DOWNLOADS`, `AIFRED_REFERENCE_BUCKET`
  - Secret/variable names: `AIFRED_ADMIN_PASSWORD_SHA256`, `AIFRED_ADMIN_SESSION_SECRET`, `AIFRED_ADMIN_USERNAME`, `AIFRED_API_TOKEN`, `AIFRED_CHAT_PROVIDER`, `AIFRED_PLUGIN_RELEASE_TAG`, `AIFRED_RELEASE_VERSION`, `Cloudflaireapi`, `GITHUB_TOKEN`, `OLLAMA_BASE_URL`, `OLLMA_MODEL`

## Workers and routing

- Worker script: `aifred-api`
- Created/last uploaded: 2026-09-08
- Deployment source: dashboard template/upload
- Bindings/secrets: none
- Worker routes: none
- Worker custom domains: none
- Account workers.dev subdomain: `aifred-site.workers.dev`

## Email

- Cloudflare Email Routing: enabled, synchronized, unlocked
- Verified destination: `north3rnlight3rofficial@outlook.com`
- Literal rule: `north3rnlight3rofficial@north3rnlight3r.com` -> verified Outlook destination
- Catch-all rule: all other recipients -> verified Outlook destination
- Required MX/SPF/DKIM records match the Email Routing DNS endpoint.
- Exactly one root SPF record exists.
- DMARC is monitoring-only (`p=none`).
- Mail records are retained unchanged during backend cutover.

## Storage and bindings

| Product | Resource | Pre-migration state | Intended migration decision |
|---|---|---|---|
| KV | `AIFRED_REFERENCE_POOL` (`8a120701767e474f928d1af7037cd68a`) | retained production data | retain for low-frequency reference metadata |
| KV | `AIFRED_SALES_LOG` (`2c66da7795b54135a4d67e514b97491f`) | historical activity/sales records | retain read-only during migration; do not use as an event firehose |
| R2 | `aifred-downloads` | retained production objects | retain for release/download objects |
| R2 | `aifred-reference-pool` | retained production objects | retain for reference assets |
| D1 | `assets` (`30af13ab-6117-41c3-9ffd-aa3bedfe92e3`) | zero tables; unrelated/unused | retain until ownership is established |
| Queues | none | absent | create a bounded event-ingestion queue if required by the new Worker |
| Analytics Engine | no binding discovered | absent from Worker and Pages configs | create a dedicated dataset binding for aggregate events |
| Service bindings | none | absent | none required for initial cutover |

No R2 object, KV key, or historical record was deleted.

## Tunnel and Access

- Tunnel `aifred-ollama` (`d4c779b6-a550-4058-b4de-3368451045c3`) was healthy with four active connections.
- The tunnel was remotely managed but had no stored ingress configuration and no zone DNS hostname.
- Access applications present: `All preview URLs`, `Warp Login App`, `aifred-site - Cloudflare Pages`, and `App Launcher`.
- Existing Access applications and policies were retained.

## Zone security state

- DNSSEC: active (ECDSAP256SHA256, SHA-256 digest)
- Always Use HTTPS: on
- Automatic HTTPS Rewrites: on
- Minimum TLS: 1.3
- TLS 1.3 / 0-RTT / HTTP3 / Brotli: enabled
- SSL/TLS mode: **Flexible**
- HSTS: enabled, 180 days, no includeSubDomains, preload flag on, nosniff on

Flexible SSL and pre-existing HSTS are recorded as risks. The API route cutover must not change HSTS until all required hostnames are validated. Full (strict) requires a compatible origin path and certificate validation before activation.

## Deployment credentials

Cloudflare does not expose secret values. The inventory records binding names only. The Pages deployment currently references a GitHub token and backend/admin/provider secrets; none were copied into source. The new Worker must receive newly generated values through Worker Secrets, and stale deployment/tunnel credentials must be revoked only after replacement validation.

## External recovery

Verified Git bundles were created outside both repositories under:

`C:\Users\North\Documents\Projects\AIFRED-recovery\cloudflare-reset-20260908`

The bundles capture clean Official `e445faaa` and Beta `d0e6755e` histories before tracked migration work.

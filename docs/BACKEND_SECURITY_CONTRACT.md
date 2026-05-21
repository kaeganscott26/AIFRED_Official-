# Backend and Security Contract

This document defines backend and security requirements before any production routing is implemented.

## Secret Rules

Never commit secrets.

Never hardcode secrets.

Never paste secrets into docs, screenshots, prompts, logs, reports, README files, or source code.

Secrets include:

- OpenAI API keys
- GitHub tokens
- Cloudflare tokens
- PayPal tokens
- admin tokens
- backend signing keys
- mailer tokens
- database credentials
- R2 credentials
- OAuth secrets
- private URLs that grant access

## Config Rules

Use:

- `.env.example`
- local ignored config files
- deployment secrets
- user settings
- secure OS storage where appropriate

Do not use:

- real `.env` in repo
- hardcoded personal paths
- hardcoded developer endpoints
- one-machine-only assumptions

## Required Backend Routes

Before implementation, each backend route must be documented with:

- purpose
- auth requirement
- request shape
- response shape
- failure behavior
- privacy/data note
- rate/abuse consideration

Planned backend areas:

- plugin status check
- optional OpenAI proxy if used
- local/backend config status
- consent-based metadata intake
- reference metadata intake
- admin deployment trigger
- website content update
- beat catalog update
- support/inquiry route
- release/download metadata

## Cloudflare Rule

Cloudflare is infrastructure, not the product.

Cloudflare config must not become a second source of truth.

Project names, Wrangler config, Pages config, R2 buckets, KV namespaces, and docs must agree before deployment.

Known drift to resolve before production:

- `north3rnlight3r`
- `aifred-site`
- duplicated website configs
- duplicated wrangler files
- old deploy workflows

## GitHub Actions Rule

No automatic deploy/build workflows in flagship until approved.

When added:

- start manual-only
- use `workflow_dispatch`
- avoid burning minutes on every README edit
- separate test, build, package, deploy
- never deploy from an unvalidated branch
- never publish artifacts that fail acceptance gates

## Privacy Rule

Consent-based metadata intake must be explicit.

Do not collect by default:

- raw audio
- personal project names
- exact local file paths
- user identity
- private notes
- API keys

May collect only with consent:

- anonymized metrics
- genre/style tag if user provides it
- plugin version
- export trend stats
- reference-pool pass/fail metadata
- system capability class if needed

Consent must be:

- explicit
- understandable
- reversible
- not hidden

## Security Acceptance Gate

Before backend production:

- no secrets in repo
- `.env.example` only
- ignored local config files verified
- Cloudflare project names aligned
- route docs complete
- admin auth defined
- consent flow defined
- failure behavior documented
- deployment manual-only unless approved

## Final Rule

Backend supports AIFRED.

Backend must not make AIFRED fragile, invasive, or dependent on perfect online conditions.

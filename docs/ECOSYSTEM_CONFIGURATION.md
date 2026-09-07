# AIFRED Ecosystem Configuration

This document defines where configuration belongs across AIFRED 4, the public Beta, the website, Cloudflare, private admin consoles, and AifredIntelligenceHost.

## One local source of truth, multiple security domains

The operator may keep one **local-only** workspace file at `AIFRED/.env` so both nested repositories can be configured from one place. Use the repository root [`.env.example`](../.env.example) as the name map.

One file does **not** mean one universal secret. Keep these credentials distinct:

- Cloudflare account/API credentials — infrastructure management only.
- GitHub token — repository API operations only.
- AIFRED admin username/password verifier/session secret — owner control plane only.
- OpenAI or compatible provider key — model access only.
- Optional R2 S3 access key/secret — external S3-compatible tooling only.

The public website must never receive owner/admin, GitHub, Cloudflare, provider, or R2 secrets in browser JavaScript.

## Canonical production API

All web/admin clients use one production origin:

```text
https://www.north3rnlight3r.com
```

Canonical public model routes use `/v1/*`. AIFRED website/control-plane routes use `/api/v1/*`.

The shared sanitized reference-pool contract is:

```text
GET /api/v1/reference/pool
```

Beta and AIFRED 4 may consume that same read-only endpoint. The endpoint exposes analysis/reference measurements required by AIFRED while withholding licensed audio objects, owner credentials, repository credentials, and private storage identifiers.

## Cloudflare binding ownership

Pages/Workers access platform storage through bindings, not through a browser/API key:

| Binding | Resource | Responsibility |
| --- | --- | --- |
| `AIFRED_REFERENCE_POOL` | Workers KV | accepted reference/analysis metadata |
| `AIFRED_REFERENCE_BUCKET` | R2 `aifred-reference-pool` | licensed/private reference objects and metadata mirrors |
| `AIFRED_DOWNLOADS` | R2 `aifred-downloads` | release artifacts, catalog media and website-managed assets |
| `AIFRED_SALES_LOG` | Workers KV | activity, inquiries, runtime routing and admin throttling |

A Worker that has an R2/KV binding does not need an S3 access key to use that resource. S3-compatible credentials are only for external tooling that accesses R2 through the S3 API.

## Admin authentication

The website backend owns admin authorization:

1. `/api/v1/admin/login` receives the owner username/password over HTTPS.
2. Cloudflare compares the username and `AIFRED_ADMIN_PASSWORD_SHA256` verifier.
3. `AIFRED_ADMIN_SESSION_SECRET` signs the bounded admin session.
4. Admin requests use the returned bearer session.

The web `/ops`, Android Admin and desktop Admin must all talk to this same backend. Do not put the plaintext admin password or session secret into deployed website assets.

The Android app's editable **API Key / Bearer Token** field belongs to the selected model/provider profile. It is not the Cloudflare deployment token and is not the AIFRED admin session secret.

## Provider independence

AIFRED measurement, observation, deterministic context, session state and bounded memory are AIFRED-owned. A model provider interprets that context; it does not create the underlying state.

LLM conversation requires one supported provider:

- local Ollama; or
- OpenAI; or
- another supported OpenAI-compatible endpoint.

Provider unavailability must not erase DSP measurements, deterministic context, retained session history, or user-exportable context records.

The intelligence architecture limits active reasoning memory to the current session plus the previous nine retained sessions. That contract remains independent of which supported model later interprets an export.

## Cloudflare secrets versus repository files

Checked-in Wrangler files contain non-secret binding names/resource IDs. Sensitive runtime values belong in Cloudflare **Variables and Secrets**, encrypted when appropriate.

For local Pages development, generate/use an ignored `.env` or `.dev.vars`; never commit populated values. Do not maintain both for the same Wrangler working directory.

## GitHub deployment integration

Native Cloudflare Pages Git integration and GitHub repository API access are separate concerns.

- **Pages Git integration** authorizes Cloudflare's GitHub App to build/deploy a selected repository on push. No long-lived Cloudflare API token needs to be placed in GitHub for ordinary Git-triggered deployments.
- **`GITHUB_TOKEN` in the AIFRED Worker** is only for the private owner features that intentionally read/write approved repository paths through the GitHub API. Keep it as a Cloudflare secret and scope it to the minimum repository permissions required.

## Distribution configuration

Never ship the operator `.env`.

Distributions ship only the blank templates under [`config/distribution/`](../config/distribution/). The installed Intelligence Host persists the user's selected provider configuration in the channel-owned local settings directory.

Users must be told clearly:

- AIFRED DSP/observation works without an LLM provider.
- Conversational LLM interpretation requires Ollama or a supported API provider/key.
- AIFRED-owned context/history is separate from the model provider.
- Context exports are portable data and may be supplied by the user to other capable applications such as ChatGPT or Gemini; those applications are not part of AIFRED and their own privacy/usage terms apply.

## Secret rotation rule

When rotating any credential:

1. create the replacement;
2. configure the consuming service;
3. verify the exact operation succeeds;
4. revoke the previous credential;
5. update the local-only workspace `.env`;
6. never commit the value.

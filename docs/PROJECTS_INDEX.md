# AIFRED Project Index

This document defines repo ownership and prevents source-of-truth drift.

## Active Repos

### AIFRED_Official-

Role: Flagship clean-room rebuild source of truth.

Status: Active planning/build repo.

This repo owns the future flagship architecture, documentation contracts, Python truth layer, AI interpretation rules, mode contracts, metric relevance rules, report system, and final flagship implementation.

No old code is automatically trusted.

Old repos may be referenced, but not copied blindly.

### AIFRED

Role: Current operational prototype / last-known-good product monorepo.

Status: Reference and preservation repo.

This repo contains the existing working product stack, including plugin source, website/backend, admin app, installer tools, GitHub Actions, and deployment references.

It is not the flagship source of truth.

It may be used to inspect working build paths, packaging behavior, installer logic, and last-known-good configuration.

No experimental artifact replaces the public/LKG build unless it passes flagship acceptance gates.

## Reference / Legacy Repos

### aifred-plugin

Role: Legacy standalone plugin line.

Status: Reference only unless intentionally revived.

Do not use as current release source of truth.

### aifred-site

Role: Standalone website/backend line.

Status: Reference only unless intentionally migrated.

Must not conflict with flagship website/backend ownership.

### aifred-admin

Role: Standalone admin app line.

Status: Reference for admin features and mobile management workflow.

May overlap with `AIFRED/android_admin`.

### aifred-downloads

Role: Placeholder/public release asset repo.

Status: Not active codebase.

Actual download storage may live in Cloudflare/R2 or official release artifacts.

### kaegan.exe

Role: Separate Unreal horror game project.

Status: Not part of AIFRED flagship.

Do not allow AIFRED agents to modify this repo.

## Source-of-Truth Rule

For the flagship build, `AIFRED_Official-` outranks all other repos.

If another repo conflicts with `AIFRED_Official-`, the flagship docs/contracts win unless the conflict is reviewed and intentionally migrated.

## Migration Rule

Old code may only be migrated after:

1. the purpose is documented
2. the target layer is identified
3. the code is inspected
4. hardcoded paths/secrets are removed
5. fake or placeholder behavior is removed
6. tests or acceptance criteria are added
7. the user explicitly approves the migration

## Agent Rule

Codex and other AI agents may inspect old repos for context, but must not treat old repo architecture as automatically valid.

All migrated behavior must pass the flagship no-drift contract.

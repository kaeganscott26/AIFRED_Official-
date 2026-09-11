# Reference pool import — 2026-09-10

This record contains identifiers and counts only. No credentials or secret values are included.

## Source

- R2 bucket: `aifred-reference-pool`.
- Prefix: `reference-pool/metadata/`.
- Source objects discovered: 22 JSON metadata records.
- Source shape: `id`, `created_at`, `file_name`, `duration_seconds`, `metrics`, and `gate`.
- Every source record had an accepted gate result.

## Destination

- D1 database: `aifred-ops`.
- Authoritative table: `references_catalog`.
- Active rows before historical import: 0.
- Active rows after historical import: 22.
- Stored version: `website-analyzer.v1`.
- The original R2 objects were not modified or deleted and remain the data rollback source.

## Verification

- All 22 R2 object IDs matched their filename UUIDs.
- D1 identity, display name, version, original ISO timestamp, metrics JSON, and classification JSON were checked against every source record after import.
- Round-trip result: PASS for 22 of 22 records.
- The staging public website analyzer created one accepted synthetic record, returned it through `GET /api/v1/reference/pool`, and the exact synthetic row was then removed. The historical count returned to 22.
- Staging Worker version after secret configuration: `17816c14-693c-44d9-8f2a-fe0693490eab`.
- Staging smoke passed all non-provider public, release/download, admin, source-control status, analytics idempotency, and logout checks.

Provider/chat validation remains separate because the protected Ollama Access/Tunnel inputs are not configured.

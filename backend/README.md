# Backend

## Purpose

`backend/` will contain the platform support layer for the flagship rebuild.

Backend supports the platform. It must not become the product, a second source of truth, or a dependency that breaks local metering and reporting.

## What Belongs Here

- Future documented API route contracts
- Future Cloudflare and worker planning
- Future secret-handling documentation
- Future backend security notes
- Future consent-based metadata intake design

## What Does Not Belong Here

- Production backend routes yet
- Cloudflare deploy configs yet
- Real secrets or tokens
- Hardcoded personal paths
- Hidden data collection
- Old backend files copied from reference repos

## Implementation Status

Implementation is not allowed yet.

This folder is Phase 1 skeleton only. Backend implementation must wait for documented route contracts, security review, and explicit approval.

## Controlling Contract

Primary contract: `docs/BACKEND_SECURITY_CONTRACT.md`

Supporting contracts:

- `docs/LOCAL_ONLINE_PARITY_CONTRACT.md`
- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/NO_DRIFT_CONTRACT.md`
- `docs/RELEASE_ACCEPTANCE_GATES.md`


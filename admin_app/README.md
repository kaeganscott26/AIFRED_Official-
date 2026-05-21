# Admin App

## Purpose

`admin_app/` will contain the future owner/admin operations layer for the flagship rebuild.

Admin controls operations. It must not be required for normal plugin use and must not own DSP behavior.

## What Belongs Here

- Future admin app documentation
- Future admin app source after approval
- Future operations workflow notes
- Future admin-only feature planning

## What Does Not Belong Here

- DSP analysis code
- Plugin runtime code
- Website source of truth
- Backend secrets
- Production admin implementation before route contracts exist
- Copied old admin app code without approved migration

## Implementation Status

Implementation is not allowed yet.

This folder is Phase 1 skeleton only. Admin implementation must wait until the plugin spine, backend route contracts, and security model are approved.

## Controlling Contract

Primary contract: `docs/BACKEND_SECURITY_CONTRACT.md`

Supporting contracts:

- `docs/MASTER_IMPLEMENTATION_CHECKLIST.md`
- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/NO_DRIFT_CONTRACT.md`


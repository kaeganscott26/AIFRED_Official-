# Tools

## Purpose

`tools/` will contain future helper scripts and maintenance utilities for the flagship rebuild.

Tools must support verified build, test, packaging, or documentation workflows without becoming hidden product behavior.

## What Belongs Here

- Future local helper scripts after approval
- Future validation utilities
- Future packaging helpers after acceptance gates exist
- Future documentation maintenance tools

## What Does Not Belong Here

- Production DSP code
- Backend routes
- GitHub Actions
- Installer implementation yet
- Secrets or local machine paths
- Cleanup scripts that modify reference repos

## Implementation Status

Implementation is not allowed yet.

This folder is Phase 1 skeleton only. Tool implementation must wait for explicit approval and must remain scoped to the active phase.

## Controlling Contract

Primary contract: `docs/CODEX_HANDOFF.md`

Supporting contracts:

- `docs/MASTER_IMPLEMENTATION_CHECKLIST.md`
- `docs/RELEASE_ACCEPTANCE_GATES.md`
- `docs/NO_DRIFT_CONTRACT.md`


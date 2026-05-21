# Tests

## Purpose

`tests/` will contain future cross-layer and acceptance tests for the flagship rebuild.

Tests preserve trust. They must prove measured facts, mode separation, source labeling, fallback behavior, reports, and release gates.

## What Belongs Here

- Future repository-level tests
- Future acceptance-gate tests
- Future integration tests between approved layers
- Future fixtures only when they are safe and documented

## What Does Not Belong Here

- Production implementation code
- Secrets
- Private audio or user data
- Generated build output
- Tests that assert fake placeholder behavior

## Implementation Status

Implementation is not allowed yet.

This folder is Phase 1 skeleton only. Test implementation begins with the Python Truth Layer phase and expands only as layers are approved.

## Controlling Contract

Primary contract: `docs/RELEASE_ACCEPTANCE_GATES.md`

Supporting contracts:

- `docs/MASTER_IMPLEMENTATION_CHECKLIST.md`
- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/NO_DRIFT_CONTRACT.md`


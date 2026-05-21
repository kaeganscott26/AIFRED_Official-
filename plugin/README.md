# Plugin

## Purpose

`plugin/` will contain the future VST/plugin shell and GUI layer for the flagship rebuild.

The plugin reveals verified state. It must not fake meters, imply stale data is live, or invent analysis values.

## What Belongs Here

- Future plugin source
- Future plugin resources
- Future plugin themes and images
- Future plugin tests
- Future GUI binding work after the truth layer is ready

## What Does Not Belong Here

- Python DSP truth-layer implementation
- Backend routes or Cloudflare configuration
- Fake meter data
- Placeholder values shown as real analysis
- Hardcoded local paths
- Copied prototype plugin code without approved migration

## Implementation Status

Implementation is not allowed yet.

This folder is Phase 1 skeleton only. Plugin work must wait until Python and AI contracts are stable and the user approves moving into the plugin phase.

## Controlling Contract

Primary contract: `docs/RELEASE_ACCEPTANCE_GATES.md`

Supporting contracts:

- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/MODE_CONTRACT.md`
- `docs/NO_DRIFT_CONTRACT.md`
- `docs/MASTER_IMPLEMENTATION_CHECKLIST.md`


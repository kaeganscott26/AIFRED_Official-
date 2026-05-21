# Python Brain

## Purpose

`python_brain/` will contain the factual analysis layer for the flagship rebuild.

Python tells the truth. It measures audio, validates analysis state, selects factual metric relevance, and prepares interpretation packets for other layers.

## What Belongs Here

- Future factual audio-analysis modules
- Future analysis-state and validation logic
- Future metric relevance logic
- Future report data preparation
- Tests, fixtures, and scripts that support factual analysis

## What Does Not Belong Here

- User-facing AI advice
- GUI/plugin source code
- Backend routes
- Cloudflare configuration
- Secrets or local machine paths
- Copied old repo code without approved migration

## Implementation Status

Production implementation is not allowed yet.

This folder currently contains Phase 2 interface contracts, module stubs, and skipped test skeletons only. Real DSP math, file analysis, report writing, persistence, and metric calculations must wait for the next approved implementation phase.

## Local Contracts

- `MODULE_CONTRACT.md`
- `DATA_MODEL_CONTRACT.md`
- `ACCEPTANCE_CRITERIA.md`

## Controlling Contract

Primary contract: `docs/MASTER_IMPLEMENTATION_CHECKLIST.md`

Supporting contracts:

- `docs/NO_DRIFT_CONTRACT.md`
- `docs/MODE_CONTRACT.md`
- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/METRIC_RELEVANCE_CONTRACT.md`
- `docs/REPORT_CONTRACT.md`

# AI Engine

## Purpose

`ai_engine/` will contain the interpretation layer for the flagship rebuild.

AI explains verified facts in context. It must preserve mode separation, source labels, metric relevance, and honest fallback behavior.

## What Belongs Here

- Future prompts
- Future AI provider adapters
- Future local/online/no-AI routing
- Future interpretation response contracts
- Future AI configuration examples

## What Does Not Belong Here

- DSP or factual metric calculation
- Plugin GUI code
- Backend route implementations
- Secrets, real API keys, or private tokens
- Canned advice presented as product behavior
- Copied old prompts without review

## Implementation Status

Implementation is not allowed yet.

This folder is Phase 1 skeleton only. AI implementation must wait until Python facts and interpretation packet contracts are stable.

## Controlling Contract

Primary contract: `docs/LOCAL_ONLINE_PARITY_CONTRACT.md`

Supporting contracts:

- `docs/MODE_CONTRACT.md`
- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/METRIC_RELEVANCE_CONTRACT.md`
- `docs/NO_DRIFT_CONTRACT.md`


# AI Engine

## Purpose

`ai_engine/` will contain the interpretation layer for the flagship rebuild.

Python calculates facts. AI explains facts.

The AI engine must consume verified Python Truth Layer interpretation packets and preserve active mode, source labels, confidence, freshness, metric relevance, limitations, warnings, and privacy rules.

## Current Status

Phase 4A is contract phase only.

No AI implementation exists yet.

## Relationship To Python Truth Layer

The Python Truth Layer remains the source of truth for factual analysis. The AI engine may eventually explain verified packet facts in context, but it must not invent metrics, override source state, recalculate DSP, or hide unavailable/limited data.

## What Belongs Here

- future AI adapter contracts
- future OpenAI adapter interfaces
- future local/Ollama/LM Studio adapter interfaces
- future no-AI fallback interfaces
- future adapter routing contracts
- future prompt-policy documentation
- future safe configuration documentation

## What Does Not Belong Here

- DSP or factual metric calculation
- Python Truth Layer metric implementation
- backend route implementations
- plugin, VST, or GUI code
- secrets, API keys, private tokens, or committed `.env` files
- hardcoded local model paths
- canned responses presented as product behavior
- copied old prompts without review

## Not Implemented Yet

- No OpenAI calls.
- No Ollama calls.
- No LM Studio calls.
- No local model loading.
- No NoAIAdapter behavior.
- No adapter router behavior.
- No generated final AI responses in code.
- No canned response logic.

## Controlling Contract

Primary contract: `ai_engine/AI_ADAPTER_CONTRACT.md`

Supporting contracts:

- `docs/LOCAL_ONLINE_PARITY_CONTRACT.md`
- `docs/MODE_CONTRACT.md`
- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/METRIC_RELEVANCE_CONTRACT.md`
- `docs/NO_DRIFT_CONTRACT.md`

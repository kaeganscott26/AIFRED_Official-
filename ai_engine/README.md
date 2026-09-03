# AI Engine

## Purpose

`ai_engine/` will contain the interpretation layer for the flagship rebuild.

Python calculates facts. AI explains facts.

The AI engine must consume verified Python Truth Layer interpretation packets and preserve active mode, source labels, confidence, freshness, metric relevance, limitations, warnings, and privacy rules.

## Current Status

The Python files under `ai_engine/` remain contract and validation scaffolding.
They are not a second provider runtime.

The native plugin runtime now has one provider route:

```text
Plugin AnalysisSnapshot
-> AnalysisContextSerializer
-> AifredEngineClient
-> AifredEngine on 127.0.0.1:8787
-> Ollama or a configured OpenAI-compatible provider
```

The local companion implementation is under `tools/AifredEngine/`. Provider
credentials live in the user's engine settings or environment, never in the
plugin or source tree.

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

## Runtime Boundary

- `ai_engine/adapters/` remains non-runtime compatibility scaffolding.
- The plugin does not import or invoke these Python adapters.
- `bridge/` remains available for offline/extended Python workflows and is not
  part of the realtime VST conversation route.
- AifredEngine performs provider routing and returns provider-generated text.
- No deterministic threshold-to-sentence response path is used.

## Controlling Contract

Primary contract: `ai_engine/AI_ADAPTER_CONTRACT.md`

Supporting contracts:

- `docs/LOCAL_ONLINE_PARITY_CONTRACT.md`
- `docs/MODE_CONTRACT.md`
- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/METRIC_RELEVANCE_CONTRACT.md`
- `docs/NO_DRIFT_CONTRACT.md`

# AI Adapters

## Purpose

This folder is reserved for future AI adapter implementations.

No adapter implementation exists yet.

## Future Adapter Roles

- `OpenAIAdapter`: future online/API-backed interpretation adapter.
- `LocalAIAdapter`: future local/Ollama/LM Studio interpretation adapter.
- `NoAIAdapter`: future factual fallback adapter that never pretends to be AI.
- `AdapterRouter`: future routing layer that selects the best available adapter from configuration and runtime status.

## Rules

- No secrets belong here.
- No API keys belong here.
- No hardcoded local model paths belong here.
- No OpenAI calls are implemented yet.
- No Ollama or LM Studio calls are implemented yet.
- No local model loading is implemented yet.
- No canned response logic belongs here.
- No backend, plugin, VST, or GUI behavior belongs here.

Adapters must eventually consume Python Truth Layer interpretation packets and preserve mode, source, confidence, freshness, metric relevance, limitations, warnings, and privacy rules.

# AIFRED 4.0 Runtime Integration

## One Native Conversation Route

```text
DAW processBlock
-> C++ DSP analyzers
-> AnalysisCoordinator
-> AnalysisSnapshot
-> AnalysisContextSerializer (non-audio thread)
-> AifredEngineClient
-> http://127.0.0.1:8787
-> AifredEngine provider router
   -> Ollama
   -> configured OpenAI-compatible provider
```

`processBlock` performs no HTTP, JSON, filesystem, settings, or model work.
The plugin never calls a provider directly. Provider absence affects chat
availability only; live analysis and metering continue independently.

## Conversation Context

`aifred.context.v1` preserves explicit measurement availability. Analyze sends
only the current snapshot. Compare sends frozen Mix A, frozen Mix B, and B-minus-A
deltas. Reference sends the current snapshot, the explicitly selected production
reference, and only directly compatible deltas.

The model-facing spectrum is an eight-region summary derived from the
authoritative full-resolution FFT using mean bin power. This does not replace or
normalize the UI spectrometer. Stored legacy reference bands remain labeled as
legacy data and are never expanded into fabricated high-resolution bins.

## Reference Service

Reference Mode reads the existing `aifred.references.v1` catalog from the
production reference endpoint. Fetching is asynchronous, read-only, timeout
bounded, and clears prior results while refreshing so a failed refresh cannot
silently present stale data as current.

## Adaptation From The Beta

The beta repository supplied the proven loopback engine, provider routing, and
production reference contracts. The flagship implementation adapts those
boundaries to `AnalysisSnapshot` and `ComparisonEngine`. It intentionally does
not copy the beta deterministic `/analyze` route, threshold findings, canned
diagnoses, prompt forms, plugin auto-launch paths, or production website code.

## Local Settings

AifredEngine exposes `GET/POST /v1/settings`. It persists settings below the
current user's application-data directory and returns only whether an API key is
configured, never the key itself. Environment overrides are supported through
`AIFRED_PROVIDER`, `AIFRED_PROVIDER_ENDPOINT`, `AIFRED_PROVIDER_MODEL`, and
`AIFRED_PROVIDER_API_KEY`.

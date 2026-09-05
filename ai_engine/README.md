# Python AI contract experiments

EXPERIMENTAL / NOT NATIVE RUNTIME. LocalAIAdapter and OpenAIAdapter are configuration-aware unavailable stubs; they perform no model calls or API-key reads. NoAIAdapter returns status only. AdapterRouter preserves availability/fallback state. The current native plugin uses tools/AifredEngine instead.

Base/result contracts carry status, source label, mode, used metric families, limitations, warnings and fallback reason. Prompt helpers accept verified interpretation packets and the actual question; they may not invent measurements, leak private paths, or include reference context in Analyze/Compare without selection. Response validation checks mode/source consistency, status, privacy and factual-shape guardrails; passing it does not establish factual model reasoning.

Config objects separate provider identity/endpoint/model and secret-availability metadata. No configuration stub is provider readiness. Test fixtures cover OpenAI/local/no-AI structural parity and fallback, not live inference. See [ownership](../docs/PYTHON_OWNERSHIP.md) and [tests](../docs/TESTING.md). Future LLM work is gated on complete analyzer validation and will consume the new observation/filter contracts, not this experiment as another production brain.

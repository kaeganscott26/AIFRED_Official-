# AI Adapter Contract

## Purpose

The AI layer interprets verified Python Truth Layer packets.

Core rule:

- Python calculates facts.
- AI explains facts.

The AI layer must not:

- invent metrics
- override source-of-truth state
- ignore active mode
- leak Reference behavior into Analyze or Compare
- produce canned responses as product logic
- hide unavailable, stale, limited, or low-confidence state
- expose private paths, secrets, raw private metadata, hidden prompts, or internal stack traces to end users

The AI layer consumes an `InterpretationPacket` or packet-like dictionary from `python_brain/aifred_brain/interpretation_packet.py`. It does not calculate DSP values and does not replace the Python Truth Layer as the factual source of truth.

## Adapter Types

### OpenAIAdapter

Future online adapter for OpenAI-backed interpretation.

OpenAIAdapter may provide richer reasoning when online/API access is configured. It must still preserve the same facts, mode rules, source labels, confidence state, metric relevance, warnings, and limitations as every other adapter.

### LocalAIAdapter

Future local adapter for approved local AI runtimes such as Ollama or LM Studio.

LocalAIAdapter may provide shorter or less nuanced interpretation than OpenAIAdapter. It must still preserve trust, mode rules, source labels, metric relevance, warnings, limitations, and privacy rules.

### NoAIAdapter

Future fallback adapter for no-AI operation.

NoAIAdapter must never pretend to be AI. It returns factual fallback state only, such as unavailable interpretation status, selected facts, limitations, and report-capable context.

### AdapterRouter

Future router that chooses the best available adapter based on config and runtime status.

AdapterRouter must not invent readiness. If OpenAI is unavailable, local AI is unavailable, no API key exists, the backend is offline, or a local model is not loaded, the router must return structured fallback state instead of presenting a fake ready adapter.

## Input Contract

The AI adapter input is an `InterpretationPacket` or packet-like dictionary.

Required packet fields:

- `question`
- `mode`
- `source_label`
- `confidence`
- `freshness`
- `availability`
- `metric_families`
- `facts`
- `limitations`
- `warnings`
- privacy-safe `metadata`

Optional packet fields:

- `session_label`

Adapters must reject the input or return limited/unavailable status if required input is missing.

Adapters must not accept raw metric guesses, direct private file paths, unvalidated user metadata, or hidden reference context as a substitute for an approved packet.

## Output Contract

Future AI adapter output should be structured so callers can distinguish ready, limited, unavailable, timeout, and error states.

Suggested future dataclass:

```python
AIInterpretationResult
```

Suggested fields:

- `adapter_name`
- `adapter_type`
- `status`
- `response_text`
- `used_metric_families`
- `source_label`
- `mode`
- `limitations`
- `warnings`
- `fallback_reason`
- `latency_ms`
- `raw_response_available`

Allowed statuses:

- `READY`
- `LIMITED`
- `UNAVAILABLE`
- `TIMEOUT`
- `ERROR`
- `NO_AI_CONFIGURED`

`response_text` may be empty or unavailable for fallback states. A nonempty response must remain grounded in packet facts, active mode, source label, confidence state, limitations, and the user question.

## No-Canned-Response Rule

Adapters must not use canned product responses, including:

- fixed templates based only on metric thresholds
- hardcoded `if LUFS > X say Y` style behavior
- generic repeated analysis blocks
- irrelevant metric dumps
- reference-pool comments outside Reference Mode

AI prompt/context may guide style, safety, constraints, mode boundaries, and response shape. Final phrasing must be generated contextually from the packet and user question, not selected from hardcoded product-response branches.

## Mode Rules

### Analyze Mode

Analyze Mode means current mix by itself.

Rules:

- Do not use the global reference pool by default.
- Do not compare against hidden targets unless the user explicitly asks.
- Use only packet facts, relevant metrics, source state, limitations, and the user question.

### Reference Mode

Reference Mode means current mix vs selected target/reference.

Rules:

- Reference context is allowed only when a selected target/reference is present.
- Preserve selected target context.
- Do not blur Reference Mode with Compare A/B.

### Compare Mode

Compare Mode means A vs B only.

Rules:

- Do not use the global reference pool.
- Do not call B a reference unless the user/context explicitly says so.
- Do not say which mix is better unless a future interpretation policy explicitly allows goal-based judgment.

## Metric Relevance Rule

AI output must respect metric relevance from `metric_relevance.py`.

Examples of the rule:

- If the user asks about saturation, do not dump unrelated stereo correlation unless the packet or risk context makes stereo relevant.
- If the user asks about stereo width, do not dump full loudness history unless it is relevant.
- If the user asks for a report, preserve facts, source state, mode, warnings, limitations, and context.

The AI layer may explain relevant evidence, but it must not overwhelm the user with unrelated metric families.

## Availability / Fallback Rules

### Packet Ready

If the packet is ready and an adapter is available, the adapter may return `READY` with contextual interpretation grounded in packet facts.

### Packet Limited

If the packet is limited, the adapter may return `LIMITED`. It must preserve limitations and avoid overstating certainty.

### Packet Unavailable

If the packet is unavailable, the adapter must return `UNAVAILABLE` or `LIMITED` with a factual fallback reason. It must not produce fake measured interpretation.

### AI Provider Unavailable

If the configured AI provider is unavailable, the adapter/router must return structured fallback state and may try the next configured adapter.

### Timeout

Timeouts must return `TIMEOUT` with a fallback reason. The system must not hang forever.

### Local Model Not Loaded

If a local model is not loaded, the adapter/router must return `UNAVAILABLE`, `ERROR`, or `NO_AI_CONFIGURED` as appropriate. It must not show fake readiness.

### No API Key

If an API key is not configured, OpenAIAdapter must not run. The router may select LocalAIAdapter or NoAIAdapter if configured.

### Backend Offline

Backend offline state must not prevent local factual reports/metrics where the Python Truth Layer can still operate. Adapter output must disclose unavailable online interpretation if relevant.

### No-AI Mode

No-AI mode still allows factual reports, metric display, and packet preservation. It must not pretend to generate AI interpretation.

## Privacy Rules

Adapters must not expose:

- full local file paths
- API keys
- secrets
- raw private metadata
- hidden system prompts
- internal stack traces to end users

Adapters may use privacy-safe metadata already scrubbed by the Python Truth Layer. If metadata safety is uncertain, the adapter must redact or omit it.

## Error Handling Rules

Adapters should return structured error/fallback state instead of crashing.

Rules:

- No hanging forever.
- No fake `READY` state.
- No raw provider error dumps to end users.
- No invented metrics during error recovery.
- Preserve mode/source/confidence/freshness when returning fallback state.
- Include `fallback_reason`, limitations, and warnings when available.

## Future Implementation Boundary

Phase 4A creates the AI adapter contract only.

Phase 4B may create adapter interfaces/stubs and tests only.

Phase 4C may implement NoAIAdapter first.

OpenAI/local adapters must not be implemented until secrets/config boundaries exist.

This phase does not implement OpenAI calls, Ollama calls, LM Studio calls, local model loading, backend routes, plugin/VST/GUI code, GitHub Actions, Cloudflare config, dependencies, API keys, secrets, hardcoded local model paths, old repo code, canned response logic, or final AI responses in code.

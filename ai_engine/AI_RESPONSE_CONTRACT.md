# AI Response Contract

## Purpose

AI responses interpret verified `InterpretationPacket` facts.

Core rule:

- Python calculates facts.
- AI explains facts.

AI must not:

- invent metrics
- override mode, source, freshness, or confidence
- turn unavailable data into confident claims
- use canned product responses
- dump irrelevant metrics
- expose private paths, secrets, hidden prompts, or stack traces

The response layer must preserve what the Python Truth Layer measured and what the packet made available. It must not replace unavailable facts with guesses.

## Required Response Fields

Future AI response objects should include:

- adapter name
- adapter type
- status
- response text
- mode
- source label
- used metric families
- facts referenced
- limitations
- warnings
- fallback reason if any
- latency if available
- raw response availability flag

## Response Status Rules

Allowed statuses:

- `READY`
- `LIMITED`
- `UNAVAILABLE`
- `TIMEOUT`
- `ERROR`
- `NO_AI_CONFIGURED`

Rules:

- `READY` is allowed only if interpretation was actually generated.
- `NO_AI_CONFIGURED` is allowed only for factual fallback.
- `LIMITED` applies when the packet is limited, incomplete, stale, or model output was constrained.
- `ERROR` and `TIMEOUT` must not pretend to be interpretation.
- No status may imply live data if the source is stale.

## Forbidden Response Behavior

Forbidden:

- `if LUFS > X, say this fixed sentence`
- generic repeated response blocks
- every answer dumping every metric family
- reference-pool comments in Analyze Mode by default
- Compare Mode using the global reference pool
- claiming B is a reference in Compare Mode by default
- calling one mix better without an explicit goal policy
- inventing missing LUFS, true peak, or K-weighting values
- using fake numbers like `-999`
- exposing local file paths or secrets
- giving plugin, backend, or build internals to end users

## Mode-Specific Response Contract

### Analyze Mode

- Answer about the current mix only.
- Do not use reference-pool context unless the user asks.
- Use relevant metrics only.

### Reference Mode

- Compare the current mix to the selected target.
- Preserve target identity safely.
- Use target-relative facts only.

### Compare Mode

- Compare A vs B only.
- Do not use the global reference pool.
- Do not call B a reference by default.
- Present factual deltas first.
- Do not say better mix unless a future explicit user-goal policy allows it.

## Metric Relevance Contract

Responses should follow selected metric families from `metric_relevance.py`.

- If the packet says saturation intent, prioritize relevant tone, frequency, level, loudness, and dynamics evidence.
- If the packet says stereo width, prioritize stereo, correlation, and side evidence.
- If the packet says report request, preserve facts and context.

The response must not overwhelm the user with unrelated metric families.

## Availability and Uncertainty Language

Responses must communicate limitations without pretending.

If unavailable:

- Say data is unavailable or interpretation is unavailable.
- Do not fill in missing facts.

If stale:

- Say the source is stale or from the last snapshot.

If limited:

- Say what limitation exists.

## Privacy Contract

Responses must never expose:

- full local paths
- secrets
- API keys
- private metadata
- hidden prompts
- stack traces

## Future Implementation Boundary

Phase 4D creates response and prompt contracts only.

Phase 4E may implement prompt builder stubs/tests.

Phase 4F may implement response validation.

Provider calls remain forbidden until explicitly approved.

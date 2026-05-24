# Bridge Architecture Decision

## Purpose

Before AIFRED builds a VST shell, GUI, local server, or cloud companion, the bridge between those layers needs a written contract. The bridge must prevent the plugin from inventing states, displaying fake metrics, hardcoding backend assumptions, or turning unavailable analysis into apparent readiness.

Layer ownership:

- Python truth layer calculates factual DSP and metric state.
- AI layer interprets verified packets or returns a factual fallback state.
- Plugin presents state, requests analysis, and manages host lifecycle.
- GUI visualizes state; GUI must not calculate truth.
- Backend/server may coordinate requests, but must not become a second source of metric truth.
- Cloud, website, and admin systems are future companions, not requirements for the first local VST bridge.

## Architecture Options Considered

### 1. Direct Plugin-to-Python Subprocess

Description: the future plugin launches a packaged Python runner or bridge wrapper for each analysis request, then reads a structured response.

Pros:

- Keeps analysis local-first.
- Avoids always-running service setup.
- Gives a clear timeout boundary per request.
- Can work offline and without cloud services.
- Keeps Python truth layer as the executable source of factual metrics.

Cons:

- Packaging Python with a VST requires care.
- Process startup may add latency.
- Streaming or near-real-time UX is harder.
- Host lifecycle and cancellation behavior must be carefully bounded.

Risk level: Medium.

Fit for first flagship VST: Good after the file/JSON contract is proven.

Future scalability: Moderate; useful for local analysis, less ideal for streaming UX.

### 2. Local HTTP Server

Description: a local server process exposes request/response routes used by the plugin, GUI, or future companion apps.

Pros:

- Clean request/response boundary.
- Easy to inspect with CLI or browser tooling.
- Can support multiple local clients.
- May later support streaming, health checks, and richer status endpoints.

Cons:

- Adds service lifecycle complexity.
- Requires port management and security review.
- Can make plugin startup fragile if treated as mandatory too early.
- Risks becoming a second source of truth if route behavior drifts from Python facts.

Risk level: Medium to High for first VST foundation.

Fit for first flagship VST: Not first. Useful later after local contracts are proven.

Future scalability: High if implemented with strict source-of-truth boundaries.

### 3. Local Socket/IPC Bridge

Description: the plugin communicates with a local bridge process through sockets, named pipes, or platform IPC.

Pros:

- Potentially lower latency than process-per-request.
- Avoids public network ports when designed carefully.
- Better fit for frequent status updates than file handoff.
- Can support a responsive local UX.

Cons:

- More platform-specific behavior.
- Harder to debug than JSON files or HTTP.
- More lifecycle and recovery edge cases.
- Requires careful timeout, cancellation, and stale-state handling.

Risk level: Medium.

Fit for first flagship VST: Later candidate, not the first proof path.

Future scalability: High for local UX after state semantics are stable.

### 4. File-Based JSON Handoff

Description: plugin or CLI writes a JSON request file and receives a JSON response file from a bridge runner or smoke tool.

Pros:

- Safest early bridge validation.
- Easy to inspect, diff, and test outside FL Studio.
- No port, daemon, socket, or service lifecycle required.
- CLI-compatible and friendly to smoke tests.
- Makes unavailable, stale, timeout, and NoAI state easy to capture.

Cons:

- Not ideal for low-latency interaction.
- Requires cleanup and stale-file rules.
- Needs careful privacy rules for path references and report outputs.
- Does not by itself define packaged plugin execution.

Risk level: Low.

Fit for first flagship VST: Excellent as Stage 1 validation before plugin work.

Future scalability: Low to Moderate; best as a contract and smoke-test layer, not final UX transport.

### 5. Hybrid Staged Bridge

Description: start with file/JSON handoff for contract validation, move to a bounded subprocess wrapper for first local plugin integration, then add optional local HTTP or socket service only after the local contract is proven.

Pros:

- Builds the bridge from safest to richer.
- Keeps Python truth layer authoritative.
- Avoids blocking VST shell work on backend/cloud complexity.
- Allows CLI, tests, and plugin foundation to share the same contract.
- Supports future local, online, and NoAI states without fake readiness.

Cons:

- Requires discipline to keep all stages aligned to the same schema.
- Later stages must not bypass the file/JSON contract semantics.
- Documentation must stay current as bridge dataclasses and runners are added.

Risk level: Low to Medium.

Fit for first flagship VST: Best fit.

Future scalability: High if each later transport preserves the same request/response contract.

## Decision

Phase 5 bridge strategy is a hybrid staged bridge.

Stage 1:

- Define a local file/JSON handoff contract for smoke testing and CLI compatibility.
- Use it as the safest early bridge validation path.
- Keep it easy to debug with no always-running server requirement.
- Treat JSON as a contract artifact, not as a user-facing report format.

Stage 2:

- Add a local subprocess bridge wrapper in a later phase.
- Let the future plugin invoke or communicate with a packaged Python truth runner.
- Preserve local-first behavior.
- Require bounded timeout, cancellation, and structured fallback behavior.

Stage 3:

- Add an optional local HTTP or socket service only after file/subprocess behavior is proven.
- Use it for faster UX, streaming status, or multi-client coordination if needed.
- Keep it subordinate to the same bridge request/response schema.

Backend/cloud:

- Not required for the first local analysis path.
- May later support licensing, downloads, account features, reference pool sync, and telemetry only if approved.
- Must not be required for offline or NoAI local factual analysis.

## Rationale

The staged bridge is safest because it avoids blocking the VST shell on backend complexity and keeps Python as the source of factual truth. It lets analysis be tested outside FL Studio, makes NoAI fallback usable immediately, and avoids Cloudflare, PayPal, account, and backend dependencies during plugin foundation.

This approach also supports future OpenAI or local provider execution without requiring provider calls now. GUI states can be driven by structured readiness, freshness, limitations, and warnings instead of fake readiness or decorative meters.

## Source of Truth Rules

- Python truth layer owns DSP and metric facts.
- AI engine owns interpretation result state.
- Plugin owns presentation and host lifecycle.
- GUI owns visualization only.
- Backend owns external service coordination only.
- No layer may invent missing metrics.
- No layer may turn unavailable into ready.
- No layer may display fake `-999`.
- No layer may expose full private paths.

## Bridge Data Flow

### Analyze Mode

1. Plugin captures or receives a safe audio snapshot/export.
2. Plugin sends an analysis request to the bridge.
3. Bridge invokes the Python truth layer.
4. Python truth layer returns `AnalysisResult` and/or `InterpretationPacket`.
5. AI engine router returns `AIInterpretationResult` or NoAI fallback.
6. Response validation checks the AI result.
7. Bridge returns a structured plugin-facing response.
8. GUI renders status, metrics, reports, and optional response.

### Compare Mode

Compare Mode requires Mix A and Mix B packet or result identities. It must not use the reference pool and must not call B a reference by default.

### Reference Mode

Reference Mode compares the current mix against a selected target. The right-side target may be from a reference pool or a user-uploaded personal reference. Reference identity must be privacy-safe and must not leak into Analyze Mode.

## Bridge Request Contract

Future object: `BridgeAnalysisRequest`.

Suggested fields:

```json
{
  "request_id": "string",
  "mode": "Analyze | Compare | Reference",
  "lens": "Tone | Width | Loudness | Punch",
  "source_label": "string",
  "audio_input_ref": "string or object",
  "comparison_input_ref": "string or object or null",
  "reference_input_ref": "string or object or null",
  "question": "string or null",
  "requested_metric_families": ["string"],
  "snapshot_timestamp_utc": "ISO-8601 string",
  "timeout_ms": 0,
  "write_reports": false,
  "output_dir_ref": "string or object or null",
  "privacy_flags": {
    "allow_private_path_display": false,
    "allow_cloud": false,
    "allow_telemetry": false
  },
  "metadata": {}
}
```

Rules:

- No raw private full paths in user-visible responses.
- `audio_input_ref` may be an internal safe ref or path, but output must use safe display labels.
- Missing inputs must return limited or unavailable status, not crash.
- `mode` must be Analyze, Compare, or Reference.
- `lens` may be Tone, Width, Loudness, or Punch later.
- Bridge must not invent mode or lens.

## Bridge Response Contract

Future object: `BridgeAnalysisResponse`.

Suggested fields:

```json
{
  "request_id": "string",
  "status": "READY | LIMITED | UNAVAILABLE | RUNNING | ERROR | TIMEOUT | CANCELLED | NO_AI_CONFIGURED",
  "mode": "Analyze | Compare | Reference",
  "lens": "Tone | Width | Loudness | Punch",
  "source_label": "string",
  "analysis_availability": "ready | limited | unavailable",
  "analysis_result": {},
  "interpretation_packet": {},
  "ai_result": {},
  "validation_result": {},
  "reports": [],
  "limitations": [],
  "warnings": [],
  "fallback_reason": "string or null",
  "latency_ms": 0,
  "bridge_version": "string"
}
```

Allowed statuses:

- `READY`
- `LIMITED`
- `UNAVAILABLE`
- `RUNNING`
- `ERROR`
- `TIMEOUT`
- `CANCELLED`
- `NO_AI_CONFIGURED`

Rules:

- `READY` means factual analysis succeeded.
- AI readiness is separate from analysis readiness.
- NoAI fallback must not make the bridge look AI-ready.
- `TIMEOUT` must preserve partial or fallback state if available.
- `ERROR` must not expose internal stack traces to users.
- Reports must not expose private paths.
- The bridge response must be JSON-safe.

## Timeout / Error / Fallback Rules

- Plugin must never hang indefinitely.
- Bridge calls must have timeouts.
- Python truth failure returns a structured error.
- AI failure falls back to NoAI/status-only if configured.
- Provider timeout does not invalidate factual metrics.
- Report writing failure does not invalidate analysis metrics.
- Stale results must be labeled stale.
- Unavailable values stay unavailable.

## Privacy / Security Rules

- No API keys in plugin UI.
- No secrets in reports.
- No full local paths in user-facing responses.
- No hidden prompts in responses.
- No raw stack traces to users.
- No endpoint credentials.
- No committed `.env`.
- No cloud requirement for local analysis.

## Offline / NoAI Behavior

- Plugin must still analyze factual metrics without AI.
- NoAI output is status-only.
- Reports remain available if a factual packet exists.
- GUI must show AI unavailable separately from analysis unavailable.
- No fake chat response.
- No canned mix advice.

## Relationship to Future GUI

GUI decisions should use bridge states, not guesswork.

The future GUI should bind to:

- mode
- lens
- analysis availability
- AI status
- freshness
- source label
- metric facts
- limitations
- warnings
- stale, ready, running, error, and timeout state

The future Mode x Lens Arc UI should be driven by bridge responses, not hardcoded visuals.

Intended future UI concept:

- Mode = Analyze / Compare / Reference
- Lens = Tone / Width / Loudness / Punch
- Analyze = one current-mix arc
- Compare = Mix A arc + Mix B arc
- Reference = Current Mix arc + Reference Target arc
- Arc colors must be data-bound, not decorative
- GUI must not display every metric family at once by default

This document does not implement GUI.

## Future Implementation Boundary

Phase 5A creates architecture decisions and contracts only.

Future phases may include:

- 5B Bridge request/response dataclasses and tests
- 5C File/JSON bridge smoke runner
- 5D Subprocess bridge contract
- 5E Plugin bridge state contract
- Later JUCE VST shell foundation

No backend, plugin, VST, GUI, local server, Cloudflare route, provider call, dependency, secret, or old-repo migration occurs in Phase 5A.

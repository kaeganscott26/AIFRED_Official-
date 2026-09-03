# Plugin / Backend Bridge Contract

## Purpose

This document defines the contract the future plugin, local bridge, optional backend, and GUI must rely on. It exists so the plugin can request analysis and present results without inventing metrics, faking AI readiness, leaking private paths, or depending on cloud systems for local factual analysis.

## Non-Negotiables

- Plugin does not invent metrics.
- Plugin does not generate AI interpretation itself.
- Plugin does not fake readiness.
- GUI does not calculate truth.
- Bridge responses must be structured.
- No private path leaks.
- No secret leaks.
- No dependency on cloud for local factual analysis.

## Modes

### Analyze Mode

Analyze Mode means the current mix by itself. It must not use the reference pool unless explicitly requested.

### Compare Mode

Compare Mode means Mix A vs Mix B. It must not use the reference pool, and it must not call B a reference by default.

### Reference Mode

Reference Mode means current mix vs selected reference target. The target may be a reference-pool item or a user-uploaded personal reference. Target labeling must be privacy-safe.

## Future Lenses

### Tone

Metric families:

- frequency
- tonal_balance
- level if relevant
- dynamics if saturation-related

### Width

Metric families:

- stereo
- correlation
- side/mid
- balance

### Loudness

Metric families:

- level
- loudness
- true peak later
- ceiling/headroom

LUFS and true peak must remain unavailable until implemented.

### Punch

Metric families:

- dynamics
- transients
- crest factor
- window behavior

## Request Schema

Future JSON-like schema:

```json
{
  "request_id": "string, required",
  "mode": "Analyze | Compare | Reference, required",
  "lens": "Tone | Width | Loudness | Punch, required",
  "source_label": "string, required",
  "audio_input_ref": "safe internal input reference, required for Analyze/Reference current mix",
  "comparison_input_ref": "safe internal input reference, required for Compare Mix B",
  "reference_input_ref": "safe internal target reference, required for Reference",
  "question": "string or null",
  "requested_metric_families": ["string"],
  "snapshot_timestamp_utc": "ISO-8601 string or null",
  "timeout_ms": "integer",
  "write_reports": "boolean",
  "output_dir_ref": "safe internal output reference or null",
  "privacy_flags": {
    "allow_private_path_display": false,
    "allow_cloud": false,
    "allow_telemetry": false
  },
  "metadata": {
    "session_label": "privacy-safe string or null",
    "plugin_version": "string or null",
    "host": "privacy-safe string or null"
  }
}
```

Rules:

- `mode` must not be inferred from missing inputs.
- `lens` must not be invented by the bridge.
- Missing inputs return limited or unavailable status.
- Full private paths may be used internally only when required for local file access, never as user-visible labels.
- Output labels must be privacy-safe.

## Response Schema

Future JSON-like schema:

```json
{
  "request_id": "string",
  "bridge_status": "READY | LIMITED | UNAVAILABLE | RUNNING | ERROR | TIMEOUT | CANCELLED | NO_AI_CONFIGURED",
  "analysis_status": "ready | limited | unavailable",
  "ai_status": "READY | LIMITED | UNAVAILABLE | ERROR | TIMEOUT | NO_AI_CONFIGURED",
  "report_status": "not_requested | ready | limited | error",
  "mode": "Analyze | Compare | Reference",
  "lens": "Tone | Width | Loudness | Punch",
  "source_label": "string",
  "freshness": "live | recent | stale | waiting | unavailable",
  "analysis_result": {},
  "interpretation_packet": {},
  "ai_result": {},
  "validation_result": {},
  "metric_families": ["string"],
  "reports": [
    {
      "format": "txt | html | json",
      "display_label": "string",
      "output_ref": "safe internal reference"
    }
  ],
  "limitations": [],
  "warnings": [],
  "fallback_reason": "string or null",
  "latency_ms": 0,
  "stale": false,
  "bridge_version": "string"
}
```

The response must be JSON-safe and must not expose secrets, hidden prompts, raw stack traces, endpoint credentials, or full private paths.

## Status Semantics

`bridge_status` describes bridge execution:

- `READY`: bridge completed and factual analysis is ready.
- `LIMITED`: bridge completed with usable but limited state.
- `UNAVAILABLE`: required bridge capability or input is unavailable.
- `RUNNING`: request accepted and not finished yet.
- `ERROR`: bridge failed with a structured, user-safe error.
- `TIMEOUT`: timeout occurred; partial factual or fallback state may be present.
- `CANCELLED`: request was cancelled.
- `NO_AI_CONFIGURED`: factual analysis may exist, but AI interpretation is not configured.

`analysis_status` describes factual Python analysis only:

- `ready`: factual analysis succeeded.
- `limited`: factual analysis exists with limitations.
- `unavailable`: factual analysis could not be produced.

`ai_status` describes AI interpretation only:

- `READY`: AI interpretation exists and passed validation.
- `LIMITED`: AI result exists but is limited.
- `UNAVAILABLE`: AI capability is unavailable.
- `ERROR`: AI path failed safely.
- `TIMEOUT`: AI path timed out.
- `NO_AI_CONFIGURED`: NoAI/status-only fallback is active.

`report_status` describes report writing only:

- `not_requested`: no report was requested.
- `ready`: requested reports were written.
- `limited`: some report outputs were written or reports have limitations.
- `error`: report writing failed, but factual analysis may still be valid.

These statuses must not be collapsed into one fake `ready` flag.

## UI Binding Rules

The future GUI should bind to:

- bridge_status
- analysis_status
- ai_status
- selected mode
- selected lens
- metric families
- limitations
- warnings
- stale state

Unavailable state must be visually distinct from zero. Zero values must not be treated as missing.

## Report / Export Rules

- Reports use factual packet/result data.
- Report writing is separate from analysis success.
- Export history and progress memory are factual only.
- No motivational coaching.
- No AI memory soup.

## Test Requirements For Future Bridge Implementation

Future bridge implementation must include tests for:

- Analyze request returns factual result.
- Compare request preserves A/B identity.
- Reference request preserves current/target identity.
- NoAI fallback returns status-only response.
- Provider unavailable does not break factual analysis.
- Timeout returns structured response.
- Invalid mode rejected.
- Invalid lens rejected.
- Missing input returns unavailable or limited.
- Zero values preserved.
- No fake `-999`.
- No private paths.
- No secrets.
- JSON serialization roundtrip.

## Phase Boundary

The file/JSON Python bridge remains a contract-backed offline and extended-analysis path. It is not the native realtime VST provider route.

The implemented native conversation route is `AnalysisSnapshot -> AnalysisContextSerializer -> AifredEngineClient -> loopback AifredEngine -> selected provider`. AifredEngine owns provider calls and settings; the VST owns neither provider secrets nor provider-specific calls. The production reference service remains a separate read-only input used only when Reference Mode is active.

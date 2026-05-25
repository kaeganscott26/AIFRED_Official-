# AIFRED Flagship Master Implementation Checklist

Purpose: provide the complete no-drift build order from empty flagship repo to distributable product.

## Prime Rule

Build the spine first.

GUI last.

Do not skip ahead.

## Phase 0 — Pre-Code Setup

Required files before code:

- `README.md`
- `AGENTS.md`
- `docs/PROJECTS_INDEX.md`
- `docs/NO_DRIFT_CONTRACT.md`
- `docs/MASTER_IMPLEMENTATION_CHECKLIST.md`
- `docs/MODE_CONTRACT.md`
- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/METRIC_RELEVANCE_CONTRACT.md`
- `docs/REPORT_CONTRACT.md`
- `docs/LOCAL_ONLINE_PARITY_CONTRACT.md`
- `docs/BACKEND_SECURITY_CONTRACT.md`
- `docs/CODEX_HANDOFF.md`
- `docs/RELEASE_ACCEPTANCE_GATES.md`

Acceptance gate:

The repo explains the product before the product is coded.

## Phase 1 — Clean Repo Skeleton

Create:

- `python_brain/`
- `ai_engine/`
- `backend/`
- `plugin/`
- `admin_app/`
- `website/`
- `tools/`
- `tests/`
- `docs/`

Each folder gets a README before implementation.

No production code yet.

## Phase 2 — Python Truth Layer

Build manually before Codex touches the VST.

Required modules:

- `audio_loader.py`
- `level_metrics.py`
- `loudness_metrics.py`
- `stereo_metrics.py`
- `frequency_metrics.py`
- `tonal_balance.py`
- `dynamics_metrics.py`
- `transient_metrics.py`
- `analysis_state.py`
- `metric_relevance.py`
- `compare_ab.py`
- `reference_compare.py`
- `export_history.py`
- `progress_memory.py`
- `interpretation_packet.py`
- `report_writer.py`
- `config_paths.py`
- `privacy.py`
- `validation.py`

Acceptance gate:

Python can analyze files, compare A/B, select relevant metrics, produce factual state, and write readable reports without the VST existing yet.

## Phase 3 — Python Validation

Use known proof files.

Tests must prove:

- peak detection
- clipping detection
- loudness calculation
- crest factor calculation
- stereo correlation
- frequency-band energy
- dynamic range/transient estimation
- Analyze mode data isolation
- Reference mode target comparison
- Compare mode A/B-only behavior
- report writing
- stale/unavailable state handling

No plugin work until this passes.

## Phase 4 — AI Engine Contract

Build after Python facts are stable.

Required pieces:

- mode router
- metric relevance router
- source-of-truth labeler
- OpenAI adapter
- local/Ollama/LM Studio adapter if stable
- no-AI adapter
- interpretation packet input
- response contract
- fallback behavior

Acceptance gate:

OpenAI and local outputs do not need identical intelligence, but both preserve the same trust value.

## Phase 5 — Backend / Plugin Bridge and Security

Only after local truth and interpretation contracts exist.

### Phase 5A - Backend / Plugin Bridge Contract Decision

Status: completed.

Scope:

- Architecture documentation only.
- No backend implementation yet.
- No plugin implementation yet.
- No JUCE/VST implementation yet.
- No GUI implementation yet.
- No local server implementation yet.
- No Cloudflare routes.
- No provider calls.

Decision:

- Use a hybrid staged bridge.
- Stage 1: file/JSON handoff contract for smoke testing and CLI compatibility.
- Stage 2: local subprocess bridge wrapper.
- Stage 3: optional local HTTP or socket service after file/subprocess behavior is proven.
- Backend/cloud is not required for the first local analysis path.

Created contracts:

- `docs/BRIDGE_ARCHITECTURE_DECISION.md`
- `docs/PLUGIN_BACKEND_BRIDGE_CONTRACT.md`
- `docs/PHASE_5_STATUS.md`

### Phase 5B - Bridge Request/Response Dataclasses and Tests

Status: completed.

Scope:

- Bridge contract dataclasses only.
- Bridge serialization helpers only.
- Bridge shape validation helpers only.
- Synthetic bridge contract tests only.
- No backend implementation yet.
- No plugin implementation yet.
- No JUCE/VST implementation yet.
- No GUI implementation yet.
- No local server implementation yet.
- No subprocess bridge execution yet.
- No file/JSON runner behavior yet.
- No Cloudflare routes.
- No provider calls.

Created contract code:

- `bridge/__init__.py`
- `bridge/bridge_contract.py`
- `bridge/tests/__init__.py`
- `bridge/tests/test_bridge_contract.py`

### Phase 5C - File/JSON Bridge Smoke Runner

Status: completed.

Scope:

- File/JSON bridge smoke runner only.
- Request JSON write/read helpers.
- Response JSON write/read helpers.
- Request and response JSON roundtrip helpers.
- Synthetic LIMITED / UNAVAILABLE smoke response from a request.
- Sanitization and validation before/after JSON roundtrip.
- Temporary-file tests only.
- No backend implementation yet.
- No plugin implementation yet.
- No JUCE/VST implementation yet.
- No GUI implementation yet.
- No local server implementation yet.
- No subprocess bridge execution yet.
- No Cloudflare routes.
- No provider calls.

Created smoke code:

- `bridge/file_json_bridge.py`
- `bridge/tests/test_file_json_bridge.py`

Phase 5 checklist:

- 5A Bridge architecture decision completed.
- 5B Bridge request/response dataclasses and tests completed.
- 5C File/JSON bridge smoke runner completed.

Next tasks:

- 5D Subprocess Bridge Contract
- 5E Plugin Bridge State Contract
- 5F Bridge Integration Smoke Audit
- Later JUCE VST Shell Foundation

### Phase 5B+ - Backend and Security Planning

Required:

- `.env.example`
- secrets documentation
- Cloudflare route map
- plugin status endpoint contract
- optional OpenAI proxy contract
- metadata/reference intake contract
- admin deployment trigger contract
- support/inquiry contract

No secrets committed.

No hardcoded user-specific endpoints.

## Phase 6 — Plugin/VST Shell

Only after Python and AI contracts are stable.

Codex may help here, but must follow `AGENTS.md`.

Required:

- VST loads in FL Studio
- GUI shell opens
- settings panel exists
- source-of-truth status visible
- mode switch visible
- no fake meter data
- no hardcoded paths
- no stale beta behavior

## Phase 7 — GUI and Meter Binding

The GUI must reveal verified state only.

Required:

- Halo view
- Tone meter
- Width meter
- Loudness meter
- Punch/dynamics meter
- chat panel
- report export button
- status labels
- mode indicator
- waiting/unavailable/stale states

Acceptance gate:

If numeric data is zero, unavailable, stale, or unmapped, the visual meter must not imply a valid filled reading.

## Phase 8 — Reports

Required formats:

- `.txt`
- `.html`

Reports must include:

- session/track name
- timestamp
- active mode
- user question
- source of truth
- confidence state
- relevant metrics
- interpretation summary
- suggested actions
- tradeoffs
- before/after comparison if available
- save path

JSON may exist internally only.

## Phase 9 — Admin App

Build after plugin spine is stable.

Admin app owns operations, not DSP.

Responsibilities:

- website content updates
- beat catalog metadata
- release/download metadata
- backend status/config views
- support/inquiry management
- deployment trigger flow
- admin-only authentication

Admin app must not be required for normal plugin use.

## Phase 10 — Website

Website presents the platform.

Responsibilities:

- product page
- download/release page
- docs/manual
- beat catalog
- support/inquiries
- privacy/consent explanation
- optional demo/Ask AIFRED

No duplicate website source of truth.

## Phase 11 — Distribution

Before release:

- clean installer
- clean uninstall/reinstall
- FL Studio scan pass
- VST3 artifact archived
- versioned release notes
- no secrets
- no hardcoded paths
- no CI surprise triggers
- manual workflow only until stable

## Final Release Standard

Zero known release-blocking bugs.

Zero fake behavior.

Zero trust-breaking defects.

No drift.

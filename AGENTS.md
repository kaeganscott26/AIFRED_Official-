# AIFRED Official agent instructions

Read workspace `AGENTS.md`, `docs/ARCHITECTURE.md`, `shared-dsp/README.md`, `docs/DEVELOPMENT.md`, `docs/REPOSITORY_CONSTRUCTION.md`, and—when touching intelligence—`intelligence/README.md`, `intelligence/PHASES.md`, `.codex/skills/aifred-intelligence/SKILL.md`, plus the README in every intelligence subfolder being changed.

## Current machine ownership

`shared DSP analyzer -> EngineSnapshot -> BufferHunter -> ObservationSnapshot -> aifred_filter -> FilteredMixContext -> AifredIntelligenceHost`

Preserve DSP precision, realtime safety, frontend identity and plugin/state IDs. GUI positions are continuous float32; only text/model presentation rounds. No duplicate algorithm, raw snapshot model path, Python runtime or analyzer fallback.

## Intelligence architecture law

The intelligence layer begins **after `FilteredMixContext`**. It consumes DSP truth and may organize, correlate, retrieve, explain and reason about that truth. It must never redefine measurement truth.

The LLM/provider is replaceable reasoning infrastructure. It is not measurement, memory, session state, freshness, retention, evidence authority or permissions authority.

Implementation order is fixed:
1. grounded conversational intelligence;
2. session context and ten-session memory;
3. read-only DAW/session awareness;
4. autonomous maintenance of AIFRED-owned intelligence state.

Do not collapse phases or expose unimplemented future capability.

### Permanent no-mutation rule

AIFRED may read, search, inspect, compare, correlate, navigate, explain and maintain its own data. It may **never** alter audio, gain, mixer state, routing, automation, mute/solo/bypass state, plugin parameters, plugin inventory or production decisions.

Agentic behavior is maintenance-only: freshness checks, stale-context invalidation, compaction, deduplication, ten-session rotation, eviction, bounded retrieval/indexing, integrity checks and context-packet assembly.

Active intelligence memory is hard-bounded to the current session plus the previous nine retained sessions. Session 11 evicts session 1 from active reasoning memory. Export/archive data does not silently expand that window.

Personality is presentation only. It never weakens evidence/uncertainty policy.

## Repository/release rules

Keep both repositories independently reproducible with their pinned shared-source inventory. Use canonical platform output, exact artifacts and recoverable promotion. Follow current user scope/authorization. Expose no unimplemented future tools/profiles. Report automation separately from installed/DAW validation. Git is the source archive; no legacy/archive source, force reset/push, secrets or generated output in commits.

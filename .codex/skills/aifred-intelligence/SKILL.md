# AIFRED Intelligence Layer Skill

Use this skill for any task under `intelligence/` or any change that connects `FilteredMixContext`, `AifredIntelligenceHost`, provider reasoning, session memory, DAW awareness, or intelligence maintenance.

## Read first

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/AIFRED_FILTER.md`
4. `docs/BUFFER_HUNTER.md`
5. `intelligence/README.md`
6. `intelligence/PHASES.md`
7. the README in every intelligence subfolder touched by the task

## Architecture boundary

```text
DAW AUDIO
 -> aifred_engine
 -> EngineSnapshot
 -> BufferHunter
 -> ObservationSnapshot
 -> aifred_filter
 -> FilteredMixContext
 -> INTELLIGENCE ONLY AFTER THIS POINT
```

The existing DSP machine is authoritative. Intelligence consumes truth; it does not redefine truth.

## Hard rules

- Do not change FFT normalization, loudness, true peak, RMS, crest, correlation, M/S, width, spectrum-band derivation, BufferHunter statistics, observation windows, or DSP profiles while implementing intelligence unless a separate DSP task identifies a reproducible failing measurement and explicitly authorizes that change.
- Do not place model, network, filesystem, SQL, serialization, logging, or locks in `processBlock`.
- Do not send raw/instantaneous engine snapshots to the model as mix state.
- Do not invent reference information or upsample legacy coarse references into nonexistent detail.
- Do not make the LLM authoritative for memory, session identity, freshness, retention, evidence, or permissions.
- Do not build one giant prompt with the entire database. Use bounded context and typed tools.
- Do not allow AIFRED to alter the mix. No faders, gain, routing, automation, mute/solo/bypass, plugin parameter changes, insert/remove, or audio processing.
- Agentic behavior is AIFRED-state maintenance only: prune, compact, deduplicate, rotate, evict, validate, retrieve, index, and assemble context.
- Active intelligence memory is hard-bounded to current session + previous nine sessions.
- Personality never overrides evidence/uncertainty policy.
- Keep provider code behind `intelligence/providers/` and keep existing host lifecycle/HTTP/settings code boring.

## Phase discipline

Implement only the requested phase. Do not pre-implement later phases.

- Phase 1: grounded current-mix conversation.
- Phase 2: session history + ten-session memory.
- Phase 3: normalized read-only DAW/session awareness.
- Phase 4: autonomous maintenance of AIFRED-owned intelligence state.

## Required change report

For every intelligence implementation task, report:
- phase and exact scope;
- contracts added/changed;
- authoritative input data used;
- tool capabilities added;
- persistence/memory impact;
- evidence/uncertainty behavior;
- tests run and results;
- explicit confirmation that no DSP algorithm or DAW audio state was changed.

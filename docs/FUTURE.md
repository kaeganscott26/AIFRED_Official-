# Future architecture

## Next gate: intelligence layer

The next project begins after the current machine is accepted:

```text
DAW audio
  -> aifred_engine
  -> EngineSnapshot
  -> BufferHunter
  -> ObservationSnapshot
  -> aifred_filter
  -> FilteredMixContext
  -> IntelligenceCore
```

The intelligence layer is now structurally scaffolded under [`../intelligence/`](../intelligence/). The scaffold is documentation/ownership only; dotted/future runtime nodes remain unimplemented until their phase begins.

Permanent rules:
- intelligence consumes the deterministic `FilteredMixContext` boundary and cannot redefine measurements;
- incompatible profile/measurement epochs are never merged silently;
- missing reference/DAW detail remains unavailable rather than fabricated;
- intelligence never enters the audio callback;
- AIFRED never alters audio, mixer state, routing, automation, plugin parameters, mute/solo/bypass state or production decisions;
- agentic behavior is maintenance of AIFRED-owned context/memory only.

## Intelligence phases

1. **Grounded conversational intelligence** — reason about the current valid mix state with typed read-only tools and evidence-bound responses.
2. **Session context and ten-session memory** — track meaningful session events, comparison anchors, previous advice/decisions, and retain only the current session plus the previous nine summaries.
3. **Read-only DAW/session awareness** — normalize whatever project/track/mixer/route/plugin/transport metadata the host can legitimately expose; unavailable capability remains explicit.
4. **Autonomous intelligence maintenance** — freshness checks, compaction, deduplication, ten-session rotation/eviction, context retrieval/budgeting and integrity repair. This phase manages AIFRED's understanding, not the mix.

See [`../intelligence/PHASES.md`](../intelligence/PHASES.md) for scope and completion gates.

## Memory boundary

Active reasoning memory is deliberately bounded:

```text
current session + previous 9 sessions = 10 maximum
```

When an eleventh session enters active memory, the oldest retained session is evicted. User-owned exports/archives may preserve records, but they do not silently re-enter active reasoning memory.

## Final gate: Babylon GUI

Babylon remains the final project phase. The present `MetricDetail` and spectrum contracts prepare clickable meter views for peak, loudness, spectrum, correlation, crest, and stereo inspection. The final GUI consumes accepted intelligence contracts; it does not become a second intelligence implementation.

## Related

- [Architecture](ARCHITECTURE.md)
- [AIFRED Filter](AIFRED_FILTER.md)
- [DSP Configuration](DSP_CONFIGURATION.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Intelligence map](../intelligence/README.md)
- [Intelligence phases](../intelligence/PHASES.md)

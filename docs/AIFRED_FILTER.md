# aifred_filter

[Filter.cpp](../shared-dsp/src/Filter.cpp) converts `ObservationSnapshot` data into deterministic `FilteredMixContext`. It does not generate prose, genre opinions, artistic scores, mastered flags, targets, or measurement thresholds.

## Input and output

The filter consumes an observation plus its profile/configuration identity and an optional reference distribution. [Pipeline](../shared-dsp/src/Pipeline.cpp) adds product channel, version, plugin instance, session, compare state, and bounded conversation continuity after filtering.

Each metric retains its machine ID, display name, unit, definition, publication precision, observed distribution, coverage, count, trend, source ownership, emphasized profile, and optional reference relationship. Spectrum bands also retain centre, geometric boundaries, and named frequency region.

## Observation states

Context reports `unavailable`, `signal_inactive`, `insufficient_observation`, or `available`. Metric trends report `unavailable`, `stable`, `rising`, or `falling` after BufferHunter establishes enough evidence.

## Reference compatibility

A reference must match schema, profile ID, profile revision, and sample rate. The filter reports an explicit reason:

- `no_reference`
- `reference_unavailable`
- `schema_mismatch`
- `profile_mismatch`
- `sample_rate_mismatch`
- `compatible`

Compatible measured distributions yield `inside_reference_distribution` or `outside_reference_distribution`, with the detailed relationship retaining below/above direction. Missing or incompatible records remain unavailable. The filter never creates high-resolution bins from coarse legacy reference bands.

Delivery-standard states such as `approaching_standard_limit` and `standard_violation` remain unavailable until a later, documented compliance policy defines the standard and limit.

## Transport host boundary

Only `aifred.filtered-mix.v1` reaches `AifredIntelligenceHost`. The host validates channel and request identity, forwards to the configured provider, and echoes instance/session identity. It does not recalculate or reinterpret DSP.

## Related

- [Architecture](ARCHITECTURE.md)
- [BufferHunter](BUFFER_HUNTER.md)
- [DSP Configuration](DSP_CONFIGURATION.md)
- [Future](FUTURE.md)
- [Testing](TESTING.md)

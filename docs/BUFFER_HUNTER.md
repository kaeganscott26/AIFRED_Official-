# BufferHunter

BufferHunter owns temporal observation. It consumes `EngineSnapshot` values and never remeasures audio. The processor-owned [Pipeline](../shared-dsp/src/Pipeline.cpp) keeps BufferHunter alive when the editor closes.

## Epoch lifecycle

BufferHunter starts a new epoch when it sees:

- a new engine epoch from profile change, manual reset, sample-rate/channel preparation, nonfinite reset, or major transport seek/loop
- a profile ID or revision mismatch
- a sample-rate mismatch
- a gap in published sample coverage

Compatible stop/resume retains history. Silence retains the last useful observations while `signalActive` and `fresh` change. Editor close/reopen has no effect.

## Storage and statistics

[BufferHunter.h](../shared-dsp/include/aifred/BufferHunter.h) stores at most 300 frames. Each profile trims that ring to its configured observation duration. At 10 Hz the active windows contain 150, 200, 250, or 150 frames.

For each valid metric and band, BufferHunter reports:

- latest, median, P10, P90, minimum, and maximum
- sample-derived coverage seconds and count
- rising, falling, stable, or unavailable trend

Trend requires at least 30 valid samples and five seconds of coverage. A conservative regression threshold accounts for serial correlation. Integrated loudness, LRA, and true peak publish their latest programme values instead of medians.

`correlationBelowZeroSeconds` accumulates only frames with valid negative correlation. Stereo Phase Diagnostic keeps its 100 ms live meter in `EngineSnapshot`; BufferHunter supplies persistence, range, and trend.

## Freshness and sufficiency

Each profile defines an observation duration and a one-second freshness policy. Sufficiency comes from accumulated active sample coverage. Silence does not fabricate zero-valued frames. Publication stalls age the observation and clear active signal state.

## Tests

[Core tests](../shared-dsp/tests/core_tests.cpp) cover capacity, per-profile window enforcement, sample-time duration, deterministic median/range, negative-correlation persistence, silence retention, freshness expiry, stop/resume, profile and sample-rate epochs, manual reset, transport discontinuity, and SPSC ordering.

## Related

- [Architecture](ARCHITECTURE.md)
- [DSP Configuration](DSP_CONFIGURATION.md)
- [AIFRED Filter](AIFRED_FILTER.md)
- [Testing](TESTING.md)

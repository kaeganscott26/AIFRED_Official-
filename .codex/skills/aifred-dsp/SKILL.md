---
name: aifred-dsp
description: Implement or debug AIFRED realtime audio analysis, snapshots, and truthful meter mappings.
---

# AIFRED DSP

Read [the construction guide](../../../docs/REPOSITORY_CONSTRUCTION.md) before implementation. It owns planned architecture; [current architecture](../../../docs/ARCHITECTURE.md) owns present behavior.

CURRENT: DAW buffer -> native DSP -> AnalysisSnapshot -> GUI/context serializer.
PLANNED: aifred_engine -> BufferHunter -> stable engineering GUI and aifred_filter -> future intelligence. Intelligence is not a dependency of metering.

## Realtime rules

- Avoid allocation in steady-state `processBlock`.
- Never lock a mutex in `processBlock`.
- Do no networking, disk IO, model work, or realtime-thread logging.
- Keep analysis bounded and leave host audio unchanged.
- The UI reads coherent snapshots only.

## Metric rules

- Retain physical units in raw metrics: dBFS, dB, LUFS, correlation, and defined width ratio.
- Base timing and windows on sample counts, never callback counts.
- Calculate compared metrics from the same signal, channels, and measurement interval.
- Do not normalize measurements into display coordinates before the presentation layer.
- Represent unavailable data with explicit validity, never magic numeric sentinels.

## Host rules

- FL Studio playhead positions may be irregular.
- Never assume `hostTime += blockSize` exactly.
- Normal playback must not trigger repeated analysis resets.
- Reset only for an explicit lifecycle or user action defined by the current contract.
- Validate incoming channel count, sample count, pointers, and amplitude before trusting results.

## GUI rules

- Every displayed value maps directly to `AnalysisSnapshot`.
- Labels and units must describe the actual measurement.
- Meter orientation and range must match the metric semantics.
- Define intentional silence, stopped, invalid, and live behavior.
- GUI smoothing is presentation only and never changes the authoritative value.

## Debugging rule

When a meter looks wrong, trace this chain in order:

```text
DAW BUFFER -> DSP INPUT -> RAW METRIC -> SNAPSHOT -> UI MAPPING
```

Never begin by randomly modifying the formula.

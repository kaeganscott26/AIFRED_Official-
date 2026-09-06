# DSP configuration

## Contract

[Contracts.h](../shared-dsp/include/aifred/Contracts.h) separates `MeasurementConfiguration` from `PresentationConfiguration`. The engine reads measurement settings. The frontend reads presentation settings. Presentation changes do not reset the engine or BufferHunter epoch and cannot change FFT power, telemetry, loudness, true peak, or stereo measurements.

The four profiles are the analyzer modes. AIFRED does not expose separate HQ or Linear Phase modes and does not combine profiles with arbitrary measurement overrides.

## Profile table

| Setting | Mix Balanced | Spectrum Surgical | Mastering Precision | Stereo Phase Diagnostic |
|---|---:|---:|---:|---:|
| Stable ID | `MIX_BALANCED` | `SPECTRUM_SURGICAL` | `MASTERING_PRECISION` | `STEREO_PHASE_DIAGNOSTIC` |
| Identity / revision | `MIX_BALANCED.r1` | `SPECTRUM_SURGICAL.r1` | `MASTERING_PRECISION.r1` | `STEREO_PHASE_DIAGNOSTIC.r2` |
| FFT size / bins | 2048 / 1025 | 8192 / 4097 | 8192 / 4097 | 2048 / 1025 |
| Overlap | 75% | 75% | 75% | 75% |
| Window | periodic Hann | periodic Hann | periodic Hann | periodic Hann |
| Power averaging | 0.4 s | 2.0 s | 3.0 s | 0.4 s |
| Peak release | 0.5 s | 1.5 s | 2.0 s | 0.5 s |
| Peak hold | 2.0 s | 4.0 s | 5.0 s | 2.0 s |
| RMS window | 400 ms | 400 ms | 400 ms | 400 ms |
| Stereo window | 400 ms | 400 ms | 400 ms | 100 ms |
| Momentary / short-term | 400 ms / 3 s | 400 ms / 3 s | 400 ms / 3 s | 400 ms / 3 s |
| Integrated / LRA / true peak | enabled | enabled | required | enabled |
| Observation duration | 15 s | 20 s | 25 s | 15 s |
| Snapshot cadence | 10 Hz | 10 Hz | 10 Hz | 10 Hz |
| Default viewport | -96..0 dBFS | -96..0 dBFS | -96..0 dBFS | -96..0 dBFS |
| Drawing smoothing | 0.34 | 0.24 | 0.28 | 0.34 |
| Peak spectrum trace | off | on | on | off |
| Expected CPU | moderate | high | high | moderate |
| Reaction | balanced | deliberate spectrum | stable programme | fast stereo |

All profiles retain the complete engineering metric set. The required-metric policy marks the measurements central to each workflow without disabling useful supporting meters.

## Mix Balanced

Use Mix Balanced for general mixing. Its 2048-point FFT and short spectrum time constants keep the display responsive, while a 15-second BufferHunter window supports sustained context. It is the fallback for missing or invalid saved profile state.

## Spectrum Surgical

Use Spectrum Surgical for resonance and frequency-placement work. The 8192-point FFT provides the highest configured frequency resolution. Longer power averaging, release, and peak hold stabilize fine spectral inspection. RMS, loudness, true peak, and stereo meters keep their established definitions.

Spectrum Surgical is the deliberate high-resolution choice. A separate HQ switch would duplicate this profile and create ambiguous identities, so AIFRED does not provide one.

## Mastering Precision

Use Mastering Precision for final-stage metering. It requires the BS.1770 loudness suite, true peak, RMS, crest, correlation, and high-resolution spectrum. The 25-second BufferHunter window stabilizes section-level observations. Integrated loudness and LRA keep their programme definitions; BufferHunter does not replace or shorten them.

## Stereo Phase Diagnostic

Use Stereo Phase Diagnostic for live phase, balance, M/S, side-to-mid, width, and vectorscope work. Its 100 ms stereo window resolves phase changes quickly. Live correlation and width come from `EngineSnapshot`; BufferHunter retains longer-term correlation distribution, trend, extrema, and time below zero.

## Linear-phase decision

The active analyzer uses an FFT/STFT with a periodic Hann window. A linear-phase toggle has no meaningful role in that measurement. A legitimate linear-phase feature would require a documented analysis-only FIR filter bank or crossover view with latency and CPU semantics. AIFRED does not implement that separate algorithm, so the UI exposes no Linear Phase option. Spectrum Surgical is the closest professional analysis feature under an accurate name.

## Presentation settings

The current UI exposes four spectrum floors: `-120`, `-96`, `-72`, and `-48 dBFS`, all with a `0 dBFS` ceiling. The selected range persists in plugin state. Missing or invalid state restores `-96..0 dBFS`. Profile defaults also specify line/fill drawing, drawing-only smoothing, grid density, label density, and optional peak trace.

Changing a profile starts a measurement epoch. Changing the viewport does not.

## Source and tests

- [Typed contract](../shared-dsp/include/aifred/Contracts.h)
- [Engine profile activation](../shared-dsp/src/Engine.cpp)
- [Spectrum configuration](../shared-dsp/src/Spectrum.cpp)
- [Official state persistence](../plugin/src/PluginProcessor.cpp)
- [Profile acceptance tests](../shared-dsp/tests/core_tests.cpp)
- [Frontend contract tests](../tests/frontend_contract_tests.cpp)
- [State contract tests](../tests/state_contract_tests.cpp)

## Related

- [Architecture](ARCHITECTURE.md)
- [Shared DSP](../shared-dsp/README.md)
- [BufferHunter](BUFFER_HUNTER.md)
- [Testing](TESTING.md)

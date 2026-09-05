# Repository construction guide

PLANNED architecture. The current product remains the native C++ analyzer and .NET companion described in ARCHITECTURE.md. None of the shared-engine folders implement runtime behavior yet.

## Authority and implementation sequence

Official owns the new shared analyzer design. Beta supplies an independent frontend and reference behavior. Neither old C++ DSP nor either existing AifredEngine implementation is the implementation source for the new engine. Implement from documented algorithms and external evidence. Preserve old behavior as test fixtures; record intentional differences against standards. Do not merge repositories, consume sibling source trees or create another Python production brain.

Sequence: define shared contracts and baseline tests; implement aifred_engine; implement BufferHunter; implement aifred_filter factual relationships; integrate both existing frontends through adapters; add DSP profiles and matching GUI configuration; validate the complete analyzer; only then scaffold and implement the future LLM/context/tool layer. Each implementation task should have bounded file ownership and a measurable exit gate.

## Audio and realtime law

DAW LIVE AUDIO BUFFER -> aifred_engine -> BufferHunter -> aifred_filter -> future LLM context/intelligence.

aifred_engine owns authoritative signal measurements. It contains documented DSP, not genre opinions, prompts, prose diagnoses, arbitrary quality scores or artistic judgment. Profiles configure shared algorithms; they do not duplicate RMS/FFT/LUFS implementations.

processBlock publishes bounded measurement state through a safe preallocated handoff. No inference, network/HTTP/web work, filesystem, SQL, blocking mutexes, unbounded allocation, tools, prompts or heavy non-realtime aggregation may run there. Keep host audio unchanged. Prepare storage off-thread. Specify queue capacity, overflow accounting, publish cadence, reset handling and shutdown; a GUI timer must not own acquisition.

## One truth and precision

EngineSnapshot -> BufferHunter -> ObservationSnapshot -> stable GUI engineering values, Compare, Reference and aifred_filter.

High-frequency animation may consume precise live measurements through an explicitly defined presentation branch. Engineering labels and intelligence share observation semantics. Display slope, normalization, smoothing and rounding never overwrite measurements.

Retain the precision required by algorithms. Do not integerize audio, FFT, RMS, loudness or correlation. Round only after measurement and observation. Define typical values, percentiles/ranges and rounding policy for each metric. Do not present average LUFS readings as integrated loudness. Keep enough decimals for correlation/ratios. An observed range must derive from the actual observation window; examples are not fabricated samples.

## BufferHunter

Consume engine measurements outside the audio thread, independent of editor lifetime. Publish typical value, observed range/min/max where meaningful, trends, validity, freshness, sample-time coverage, active profile/version, reset epoch, reference selection and explicitly known session context. Never change engine facts.

Use audio sample time and per-metric update identity; avoid counting a repeated measurement once per GUI tick. Define weighting, window duration, warmup, gaps, overflow, transport stop, silence and stale states. Preserve useful stopped values but label them as stopped/stale. No observation may mix incompatible profile epochs.

## aifred_filter

Combine observations, selected reference, active DSP profile, known session metadata and future bounded tool/context information. Classify factual relationships such as inside/outside a reference distribution, approaching a defined threshold, unavailable and insufficient observation. Every classification includes the source, units, rule/version and supporting observation. It does not write canned chatbot answers. The future LLM chooses communication from the user's question and available facts.

Analyze means the current mix alone; Compare means Mix A versus Mix B, with no hidden reference pool; Reference uses only the selected target. A file's commercial origin does not turn Compare B into Reference. Never infer genre targets as measured facts.

## Algorithms and profiles

Each metric must cite a documented algorithm, recognized metering standard or established signal-analysis method with operands, units, windows, channel policy and validation tolerances. Legitimate families: sample peak, RMS, ITU-R BS.1770-compatible true peak, momentary/short-term/integrated loudness, EBU loudness range, FFT/STFT, L/R correlation and energy balance, M/S energy, crest with paired windows, and measured vectorscope source data.

Verify the applicable ITU/EBU publications and official test signals before implementation. Proper true peak requires reconstruction/interpolation validated against the standard; simple linear interpolation must not be relabeled dBTP. Professional products can provide behavioral comparisons; do not claim proprietary FabFilter/Voxengo/iZotope/Waves replication.

Initial planned profiles:

| Profile | Purpose | Candidate configuration, not an implemented preset |
|---|---|---|
| MIX_BALANCED | General mixing/default | Hann FFT 2048 or 4096, 75% overlap, defined RMS/stereo windows, shared loudness/peak algorithms |
| SPECTRUM_SURGICAL | Resonance and low-frequency inspection | Hann FFT 8192, 75% overlap, average/peak spectra; display tilt separate from facts |
| MASTERING_PRECISION | Detailed master evaluation | FFT 4096-8192 plus validated true peak, momentary/short/integrated loudness and LRA |
| STEREO_PHASE_DIAGNOSTIC | Phase and channel-energy inspection | Correlation distribution, L/R and M/S energy, vectorscope source pairs; FFT 2048 or 4096 |

Later candidates: TRACKING_FAST (FFT 1024/50% overlap, responsive displays), REFERENCE_LONG_TERM (matched longer observation distributions), LOUDNESS_COMPLIANCE (verified EBU/ATSC/custom delivery requirements), and K-System display calibration if justified. Tentative observation durations, such as 5-10 seconds for tracking or 10-20 seconds for mixing, require metric-specific validation and are not universal confidence thresholds.

Profile parameters may include FFT size/window/overlap, spectral averaging/release/hold, RMS integration, loudness modes, correlation/stereo windows and visualization settings. Every snapshot carries profile ID/version. A switch closes the incompatible observation epoch, starts a new one, propagates identity to the filter, and later to model context. Define pending/warmup behavior and safe off-thread preparation before adding GUI controls.

## Spectrum contract

Preserve high-resolution FFT/STFT bins for the hero analyzer. Derive telemetry from those same bins with documented band boundaries, energy normalization, weighting and handling above Nyquist. Thirty telemetry bands never replace the high-resolution spectrum.

Intended centers in Hz:

20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250, 350, 450, 600, 750, 850, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, 18000, 20000.

850 Hz is the added center completing the set of 30; it is not the last center in ascending frequency order. This exact set is AIFRED telemetry, not an ITU, EBU or vendor standard. Current Official still publishes 1025 bins and seven compatibility bands, with an eight-region model summary. The 30-center scaffold is unimplemented.

## Future intelligence gate

After analyzer validation, design an MCP-style audio context router inspired by FORGE's bounded memory/context/tool model. AIFRED must not become an autonomous shell/filesystem agent. Candidate capabilities: current observation, active DSP profile, selected reference, Compare state, bounded history, verified transport/session metadata, host-provided mixer/routing/plugin inventory, trusted plugin documentation lookup, bounded reference lookup and user-controlled memory.

Host-wide topology requires an actual host/API mechanism. Unknown information stays unavailable. Identify provenance, permission, freshness, instance and session for each capability. Personality text cannot override measurements or grant capabilities.

Planned user-customizable identity structure, with no files loaded by today's runtime:

| Future file | Responsibility |
|---|---|
| SOUL.md | Identity, purpose, conversational principles and personality |
| HEARTBEAT.md | Runtime/context conventions; periodic behavior only if separately implemented |
| SKILLS.md | Bounded audio/DAW capabilities actually available |
| MEMORIES.md | User-controlled durable preferences/context and memory policy |

Creating these files later does not authorize autonomous behavior. DSP/observation facts outrank identity and memory text. Do not create a second provider implementation in Python.

## Validation and replacement gates

Before replacing current code, build a baseline from the current commit, run existing tests, retain input/output fixtures and validate FL Studio behavior. Archive the old engine outside both repositories with a Git bundle, source, dependencies, test evidence and binary hashes; verify recovery. Keep secrets/user data separate.

Test algorithms against analytic signals and external standards evidence across sample rates and block sizes. Test realtime bounds, allocations, handoff coherence, overflow, no-editor operation, mono/stereo, anti-phase, above-full-scale samples, invalid samples, silence, stop/resume, reset, profile changes and multiple instances. Prove both frontends consume the same shared implementation. GUI tests must prove labels and visualization derive from the intended facts. Keep model integration disabled until the analysis-to-GUI acceptance gates pass.

Select the shared-package distribution mechanism in that implementation task: versioned dependency/artifact with an explicit revision. Neither repository may compile from an absolute sibling checkout. Channel IDs/install migrations need their own approved compatibility plan; see COEXISTENCE.md.

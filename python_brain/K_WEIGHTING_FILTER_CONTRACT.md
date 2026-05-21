# K-Weighting Filter Contract

## Purpose

K-weighting is required before trustworthy LUFS-style loudness can exist.

RMS and unweighted window mean-square are not LUFS. They are useful factual level or energy facts, but they do not include the perceptual weighting step required by a BS.1770-style loudness path.

Phase 3E creates the K-weighting/filter design contract and interface placeholders only. It does not implement filter coefficients, K-weighting processing, LUFS, integrated loudness, gating, or true peak.

## What K-Weighting Does

K-weighting shapes the signal before loudness energy is measured.

Clarifications:

- unweighted mean-square is not LUFS
- filtered mean-square is a required step toward LUFS
- K-weighting is not EQ advice
- K-weighting is not a creative tone-shaping process
- K-weighting belongs inside the measurement engine only
- K-weighting output must not be presented as final loudness by itself

## Future Filter Chain Direction

The future filter chain should include:

- high-pass behavior
- high-shelf/pre-filter behavior
- sample-rate-aware coefficient handling
- per-channel filtering before loudness energy calculation
- clear unsupported-sample-rate behavior
- no output labeled LUFS until the full loudness path is approved

No coefficients are committed in Phase 3E.

## Coefficient Policy

K-weighting coefficients must be verified before implementation.

Do not invent or approximate coefficients.

No coefficients should be committed unless:

- source is documented
- sample-rate handling is defined
- tests exist
- tolerance is defined
- implementation phase is explicitly approved

## Future Implementation Options

Option A: manual standard-library biquad implementation with documented coefficients.

Option B: approved dependency if accuracy/testing requires it.

No dependency is approved in Phase 3E.

## Required Future Tests

Before K-weighting implementation is accepted, future tests must prove:

- silence remains silence
- filter output length matches input length
- invalid sample rate is rejected
- invalid samples are rejected
- mono input can be filtered
- stereo/interleaved input can be handled safely
- filter does not create fake LUFS values
- coefficients are documented
- known proof signals produce expected behavior within documented tolerance
- no advice text is generated
- no old repo behavior is copied blindly

## Failure Conditions

Release-blocking failures:

- LUFS calculated without K-weighting
- RMS relabeled as LUFS
- K-weighting coefficients invented without source
- true peak claimed from sample peak
- unsupported sample rate silently accepted
- filter changes private metadata
- filter generates advice
- filter depends on hardcoded local paths

## Phase Boundary

Phase 3E creates filter contract and interface placeholders only.

Phase 3F may implement generic biquad/filter primitives only, but not final LUFS, if explicitly approved.


# K-Weighting Coefficient Decision Contract

## Purpose

Phase 3G prevents invented coefficients, fake loudness, and accidental RMS-to-LUFS drift.

K-weighting coefficients must be verified before being committed.

No coefficient values are approved in this phase.

No LUFS output may exist until coefficient source, sample-rate behavior, and tests are approved.

## Approved Source Requirement

Future coefficients must come from a traceable source.

Acceptable future sources may include:

- official ITU-R BS.1770 specification text or tables where accessible
- well-established standards documentation
- verified equations derived from the standard
- dependency or library reference only if the dependency is approved later

Do not paste actual coefficients in Phase 3G.

Source notes must identify the standard name, source reference, supported sample rates, coefficient precision, and test tolerance.

## Sample-Rate Policy

Initial support should be limited to common production rates:

- `44100`
- `48000`

Optional later rates:

- `88200`
- `96000`
- `176400`
- `192000`

Unsupported sample rates must fail clearly or return an unavailable state. They must not be silently approximated.

## Tolerance Policy

Future tests must define:

- coefficient precision tolerance
- filter-output tolerance
- loudness-result tolerance once LUFS exists

Tests must avoid fake exactness. Floating-point comparison should use documented tolerances that match the coefficient source and implementation precision.

AIFRED must not create fake confidence percentages such as `87% confident`. Confidence remains a practical availability/source state, not a numeric guess.

## Test Signal Policy

Future tests may use safe generated signals:

- generated silence
- generated impulse
- generated DC-like constant if needed
- generated sine waves
- generated stereo/interleaved synthetic signals

Future tests must not use:

- private songs
- copyrighted commercial audio
- old repo audio
- DAW project audio
- user personal mixes unless explicitly approved

## Future Implementation Sequence

Required order:

1. Generic biquad primitives exist and pass tests.
2. Coefficient source is documented.
3. Supported sample rates are selected.
4. Coefficient values are added with source notes.
5. Coefficient validation tests are added.
6. K-weighting processing tests are added.
7. Filtered mean-square tests are added.
8. Only then may momentary and short-term loudness be implemented.
9. Integrated loudness and gating come later.
10. True peak remains separate.

## Failure Conditions

Release-blocking failures:

- coefficients invented without source
- coefficient source missing
- unsupported sample rate accepted silently
- filter output labeled LUFS
- RMS or mean-square labeled LUFS
- K-weighting produces advice text
- private paths or private test files used
- dependency added without approval
- old repo behavior copied blindly

## Phase Boundary

Phase 3G creates the coefficient decision contract and placeholder tests only.

Phase 3H may add verified coefficient values for selected sample rates only if explicitly approved.

Phase 3H must still not implement final LUFS unless separately approved.

# Loudness Algorithm Contract

## Purpose

Loudness is more sensitive than simple peak and RMS math.

AIFRED must not fake LUFS, derive LUFS by relabeling RMS, or show placeholder loudness values as if they were measured. Loudness values must come from an approved algorithm with documented limitations, test coverage, and honest unavailable states.

Phase 3B implemented sample peak, RMS, crest factor, clipping state, and ceiling margin. Those are useful level facts, but they are not LUFS.

## Loudness Definitions

### RMS

Root mean square is an energy-style average of sample amplitude over a chosen signal or window. RMS is useful for basic level evidence, but it is not perceptual loudness and must not be labeled as LUFS.

### dBFS

dBFS means decibels relative to digital full scale. A full-scale sample peak is `0 dBFS`. Values below full scale are negative. dBFS can describe sample peak or RMS, but the label must state what is being measured.

### LUFS

LUFS means Loudness Units relative to Full Scale. LUFS is a perceptual loudness measurement defined by a loudness standard, commonly ITU-R BS.1770-style measurement. LUFS is not the same as RMS or sample peak.

### Momentary Loudness

Momentary loudness is a short-window loudness measurement, typically over approximately 400 ms. It should be unavailable or limited when the signal is too short for the approved window.

### Short-Term Loudness

Short-term loudness is a longer-window loudness measurement, typically over approximately 3 seconds. It should be unavailable or limited when the signal is too short for the approved window.

### Integrated Loudness

Integrated loudness is a program-level loudness measurement over the full approved signal duration. It uses gating in BS.1770-style workflows and must not be produced from insufficient data without a limitation label.

### Loudness Range

Loudness range describes loudness variation across a program. It is not the same as dynamic range, crest factor, or peak-to-RMS difference.

### True Peak

True peak estimates inter-sample peak behavior, usually requiring oversampling or a standards-aware method. AIFRED must not claim true peak from sample peak alone.

### Sample Peak

Sample peak is the highest absolute decoded sample value. Phase 3B implements this as a factual level metric. Sample peak is not true peak and not LUFS.

## Approved Algorithm Direction

Flagship LUFS should follow an ITU-R BS.1770-style approach.

Future implementation steps:

1. Decode normalized PCM.
2. Apply a K-weighting filter.
3. Calculate mean square energy.
4. Apply channel weighting where appropriate.
5. Calculate momentary loudness over approximately 400 ms windows.
6. Calculate short-term loudness over approximately 3 second windows.
7. Calculate integrated loudness with gating.
8. Represent unavailable or insufficient-duration states honestly.

## Dependency Decision

No loudness dependency is approved in Phase 3C.

Decision options for a future implementation phase:

- Option A: implement BS.1770-style loudness manually using Python standard library and `math` only.
- Option B: later approve a dedicated loudness dependency if accuracy requires it.

No dependency is approved yet.

## Minimum Future Test Requirements

Before loudness implementation is accepted, tests must prove:

- silence returns unavailable/`None` where appropriate, not fake values
- short files produce limited or unavailable state where required
- sine/test tones produce stable expected results within documented tolerance
- momentary windows behave consistently
- short-term windows behave consistently
- integrated loudness does not equal RMS
- LUFS and dBFS are not confused
- no fake `-999` values
- no advice text
- no reference-pool behavior
- no AI interpretation

## Failure Conditions

Release-blocking loudness failures:

- LUFS value invented from RMS
- LUFS mislabeled when only RMS exists
- true peak claimed without oversampling or approved true-peak implementation
- integrated loudness produced from too-short signal without a limitation label
- silence reported as a fake loudness number
- local path or private data leakage
- loudness module generates advice
- loudness module invokes reference-pool behavior
- loudness module performs AI interpretation

## Phase Boundary

Phase 3C creates the loudness contract and placeholder tests only.

Phase 3D may implement either:

- `loudness_metrics.py` basic windowing helpers only, or
- an approved BS.1770-style implementation slice

Phase 3D must happen only after explicit approval.


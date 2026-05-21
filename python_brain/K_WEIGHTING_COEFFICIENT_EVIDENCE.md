# K-Weighting Coefficient Evidence Pack

## Purpose

Phase 3H prepares the evidence structure for verified K-weighting coefficients.

No coefficient values are approved in this phase.

No coefficient values are committed in this phase.

No LUFS output exists in this phase.

No K-weighting processing exists in this phase.

This phase exists to prevent invented coefficients and fake loudness.

## Required Evidence Before Coefficients

Future coefficient implementation must include:

- source name
- source version or standard revision if available
- source URL or citation if available
- whether the source is official, standards-derived, or dependency-derived
- supported sample rates
- coefficient precision
- tolerance policy
- implementation notes
- verification tests
- reviewer approval note

## Evidence Table Template

| Status | Sample Rate | Source Name | Source Type | Source Reference | Coefficient Precision | Output Tolerance | Approved For Implementation | Notes |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| Not Approved | 44100 | TBD | TBD | TBD | TBD | TBD | No | Evidence required before implementation. |
| Not Approved | 48000 | TBD | TBD | TBD | TBD | TBD | No | Evidence required before implementation. |
| Not Approved | 88200 | TBD | TBD | TBD | TBD | TBD | No | Optional later rate; evidence required. |
| Not Approved | 96000 | TBD | TBD | TBD | TBD | TBD | No | Optional later rate; evidence required. |
| Not Approved | 176400 | TBD | TBD | TBD | TBD | TBD | No | Optional later rate; evidence required. |
| Not Approved | 192000 | TBD | TBD | TBD | TBD | TBD | No | Optional later rate; evidence required. |

Do not include coefficient values in this table.

## Approved Source Types

Allowed future source types:

- Official ITU-R BS.1770 source
- Standards-derived equation source
- Reviewed engineering reference
- Approved dependency reference

Rejected source types:

- unsourced blog post
- copied old repo behavior
- AI-generated coefficients
- guessed coefficients
- memory-based coefficients
- undocumented forum snippets

## Manual Verification Checklist

Before coefficients may be added:

- source reviewed
- sample rate supported
- coefficient precision documented
- output tolerance documented
- generated proof signals defined
- no private audio used
- no old repo coefficients copied blindly
- tests written before implementation
- reviewer approval added to evidence table
- implementation phase explicitly approved

## Future Implementation Gate

Phase 3I may add coefficient values only for approved sample rates with documented evidence.

If no approved source exists, Phase 3I must not implement coefficients.

If only `48000` Hz is approved, only `48000` Hz may be implemented.

If `44100` Hz and `48000` Hz are approved, only those two may be implemented.

Unsupported sample rates must fail clearly or return unavailable.

## Failure Conditions

Release-blocking failures:

- coefficient values added without approval
- coefficient values added without source
- coefficients copied from old repo without review
- unsupported rates approximated silently
- filter output labeled LUFS
- RMS or mean-square labeled LUFS
- test audio uses private or copyrighted material
- dependency added without approval
- old repo behavior migrated blindly

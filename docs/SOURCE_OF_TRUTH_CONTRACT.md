# Source-of-Truth Contract

AIFRED must always know what it is answering from.

Trust requires visible source labeling.

## Valid Source Labels

- Live Buffer
- Last Snapshot
- File Analysis
- Compare A/B
- Reference Mode
- Export History
- Saved Report
- General Advice
- Meter-Only Fallback
- No-AI Fallback

## Required Behavior

Every AI response, report, and major GUI state must be traceable to a source.

AIFRED must not imply live analysis when using stale or cached data.

AIFRED must not imply file analysis when using general advice.

AIFRED must not imply reference comparison unless Reference Mode is active or the user explicitly asks.

AIFRED must not imply A/B comparison unless Compare Mode is active.

## Confidence Labels

Do not use fake precision like “87% confidence.”

Use practical confidence states:

### High

Current data is available, recent, and stable.

Example reason:

“Live buffer active; meter window contains enough signal for stable level and stereo readings.”

### Medium

Data is usable but limited.

Example reason:

“Short snapshot; loudness and dynamics may not represent the full track.”

### Low

Data is stale, incomplete, or unavailable.

Example reason:

“No current buffer data; response uses last snapshot.”

## GUI Requirements

The GUI must show:

- active mode
- source label
- AI/backend status
- stale/waiting/unavailable state when applicable

Waiting state must not look like zero.

Zero must not look like unavailable.

Unavailable must not look like a valid reading.

## Report Requirements

Reports must include:

- source label
- timestamp
- analysis duration/window if applicable
- mode
- confidence state
- limitations

## Failure Conditions

This contract fails if:

- the AI answers as if data is live when it is not
- a GUI meter is filled from stale/unavailable data
- a report omits source context
- Compare and Reference source labels blur together
- user cannot tell whether the answer is measured or general advice

## Final Rule

AIFRED must not only be correct.

AIFRED must make its source of truth obvious.

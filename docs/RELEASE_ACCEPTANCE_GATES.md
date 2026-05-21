# Release Acceptance Gates

This document defines the minimum standard for any AIFRED release candidate.

## Release Philosophy

AIFRED is not release-ready because it builds.

AIFRED is release-ready when it is trustworthy.

## Gate 1 — Repository Integrity

Pass criteria:

- docs/contracts exist
- source-of-truth index exists
- `AGENTS.md` exists
- old repos are labeled reference only
- no unknown generated junk committed
- no unreviewed migrated code
- no secrets committed
- no hardcoded personal paths

## Gate 2 — Python Truth Layer

Pass criteria:

- audio loader works
- peak/RMS tests pass
- LUFS tests pass
- crest factor tests pass
- stereo/correlation tests pass
- frequency band tests pass
- dynamics/transient tests pass
- Compare A/B tests pass
- Reference tests pass
- metric relevance tests pass
- report writer tests pass
- unavailable/stale state tests pass

## Gate 3 — Interpretation Layer

Pass criteria:

- Analyze mode does not reference pool unless asked
- Reference mode uses selected target
- Compare mode stays A vs B only
- source-of-truth label appears
- stale data is disclosed
- relevant metrics only
- no canned response behavior
- no raw JSON as main user output
- OpenAI/local/no-AI behavior documented

## Gate 4 — GUI/Meter Trust

Pass criteria:

- no fake meters
- no placeholder values
- waiting is distinct from zero
- zero is distinct from unavailable
- stale is distinct from live
- filled bars match verified numeric state
- source label visible
- mode visible
- status labels truthful
- GUI resizes/readable in FL Studio

## Gate 5 — Plugin Host Validation

Pass criteria:

- installs cleanly
- FL Studio scans VST3
- plugin opens without crash
- audio processing does not crash
- meters respond to real signal
- AI/chat path responds or fails gracefully
- reports save
- settings persist
- uninstall/reinstall path works

## Gate 6 — Backend/Online/Offline

Pass criteria:

- local mode works or degrades gracefully
- OpenAI mode works if configured
- no-AI mode works
- backend unavailable does not kill metering
- no secrets exposed
- config paths portable
- privacy/consent behavior documented

## Gate 7 — Reports

Pass criteria:

- `.txt` report saves
- `.html` report saves
- report includes source label
- report includes active mode
- report includes relevant metrics
- report includes tradeoffs/warnings
- report does not preserve fake meter values
- report path is user-understandable

## Gate 8 — Distribution

Pass criteria:

- artifact versioned
- release notes written
- installer tested on clean machine
- no accidental GitHub Actions burn
- no automatic deploy unless approved
- public/LKG build not overwritten by experimental artifact
- archive created
- rollback path defined

## Final Release Blockers

Do not release if any exist:

- fake meter
- stale state shown as live
- hardcoded secret
- hardcoded developer path
- plugin crash in FL Studio
- no install/uninstall path
- Analyze/Reference/Compare mode leak
- AI invents metrics
- reports missing
- no fallback when AI unavailable
- unclear source of truth

## Final Standard

Zero known release-blocking bugs.

Zero fake behavior.

Zero trust-breaking defects.

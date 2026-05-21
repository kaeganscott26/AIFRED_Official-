# Report Contract

AIFRED reports are trust infrastructure.

A report preserves what was measured, what was asked, what was recommended, and what changed.

## Purpose

Reports prevent lost validation moments.

Reports turn AIFRED into a decision record and learning record.

## Required User-Facing Formats

- `.txt`
- `.html`

Optional internal sidecars:

- `.json`

JSON is allowed for internal state or metadata.

JSON is not the primary user-facing report.

## Required Report Fields

Every report must include:

- product/version
- timestamp
- session/track name if available
- active mode
- user question
- source-of-truth label
- confidence state
- analysis duration/window
- relevant metrics
- factual flags
- interpretation summary
- suggested actions if requested
- tradeoffs/warnings
- compare/reference context if applicable
- save path
- limitations

## Optional Report Fields

When available:

- before/after metrics
- plugin chain recommendation
- user-selected plugin constraints
- reference target name
- Mix A/Mix B filenames
- export history trend
- progress notes
- next-session reminder

## Save Location Rules

Preferred location:

`<DAW Project Folder>/AIFRED Reports/`

Fallback if project folder is unavailable:

`Documents/AIFRED Reports/`

If the plugin cannot infer a safe path, ask the user to choose one.

Do not silently save to obscure temp folders.

## Report Tone

Reports should read like a real engineer’s session note.

They should be clear, direct, and practical.

Avoid:

- generic AI filler
- fake certainty
- raw debug dumps
- unexplained abbreviations
- JSON-first output
- hype language

## Before/After Reports

Before/after reports must include:

- before metrics
- after metrics
- delta summary
- what improved
- what got worse
- practical tradeoff
- whether the change served the user’s stated goal

Example tradeoff:

“This move raised perceived loudness and improved ceiling safety, but reduced transient contrast. Keep it if loudness is the goal; back it off if punch matters more.”

## Chain Recommendation Reports

If the user requests a plugin chain, the report must include:

- plugin names
- order
- starting settings
- why each plugin is included
- what metric/problem it targets
- risk warning
- expected outcome
- save timestamp

## Failure Conditions

Report system fails if:

- recommendations disappear after the session
- reports are raw JSON only
- reports omit source-of-truth state
- reports omit active mode
- reports do not save consistently
- reports preserve fake or unmapped meter values
- reports make claims not backed by measured data or general engineering knowledge

## Final Rule

Reports preserve the truth.

If AIFRED helped make a decision, that decision should be recoverable later.

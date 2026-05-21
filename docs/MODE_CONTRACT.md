# Mode Contract

AIFRED has three primary interpretation modes.

The active mode controls:

- what is measured
- what context is allowed
- what metrics are displayed
- what the AI may reference
- what conclusion style is allowed

Mode separation is not just GUI state.

Mode separation is product trust.

## Analyze Mode

Analyze Mode means:

Current mix by itself.

Analyze mode may use live buffer analytics, snapshot analytics, or file analysis depending on source-of-truth state.

Default behavior:

- analyze the current mix on its own terms
- do not invoke global reference pool
- do not compare against professional targets unless asked
- answer the user’s question directly
- use only relevant metrics
- identify source of truth

Allowed topics:

- ceiling safety
- clipping
- headroom
- low-end balance
- low-mid buildup
- harshness
- vocal position
- stereo safety
- punch
- loudness state
- dynamics
- masking
- tonal balance
- next practical move

Analyze Mode may mention general engineering standards, but not hidden reference-pool deltas.

Reference language is only allowed if the user asks:

- “How do I hit the reference target?”
- “How close is this to the reference?”
- “How do I make it sound more professional?”
- “Compare this to the reference pool.”

## Reference Mode

Reference Mode means:

Current mix against selected target/reference/pool.

Default behavior:

- compare current mix to the selected target
- explain deltas against that target
- use target-relative interpretation
- provide target-oriented next steps
- show source of target

Reference Mode may measure:

- LUFS delta
- true peak / ceiling delta
- crest / punch delta
- tonal balance delta
- band-balance delta
- width / correlation delta
- dynamic contrast delta
- low-mid / harshness / air differences
- reference-pool pass/fail or closeness if active

Reference Mode may say:

- “Your mix is quieter than the target.”
- “Your low mids are elevated against the selected reference.”
- “Your crest factor is lower than the target.”
- “Your stereo image is wider but less mono-stable.”

## Compare Mode

Compare Mode means:

Mix A vs Mix B only.

Default behavior:

- compare A directly against B
- do not invoke global reference pool
- do not call B a reference automatically
- do not compare both against hidden targets
- determine what changed
- identify which version better serves the user’s goal

Mix B can be:

- another render
- yesterday’s master
- a client mix
- a commercial song
- a user-selected comparison file
- a reference-style track

In Compare Mode, B is simply B.

Correct Compare language:

- “Mix B is louder but less punchy.”
- “Mix A has safer vocal tone.”
- “Mix B has tighter low mids.”
- “Mix A is wider but less focused.”
- “Mix B carries more loudness with less transient contrast.”

Incorrect Compare language:

- “Mix A is below the reference pool.”
- “Mix B is above professional target averages.”
- “Your reference track shows..."

That belongs in Reference Mode unless explicitly requested.

## Mode Failure Conditions

A response fails the mode contract if:

- Analyze Mode references the pool by default
- Compare Mode invokes hidden target data
- Reference Mode ignores the selected target
- AI answers from stale data without labeling it
- irrelevant metrics dominate the response
- GUI and chat disagree about active mode

## Final Rule

Analyze = this mix by itself.

Reference = this mix against a target.

Compare = Mix A vs Mix B.

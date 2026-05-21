# Metric Relevance Contract

AIFRED must reveal the right data at the right moment.

Metrics are evidence.

They are not the conversation.

## Core Rule

Do not dump every metric for every question.

Select metrics based on:

- user question
- active mode
- mix state
- selected goal
- plugin/action being discussed
- risk level
- available source data

## Saturation Profile

Relevant metrics:

- tonal balance
- harmonic density
- presence range
- harshness range
- true peak
- headroom
- RMS
- perceived loudness
- crest factor
- dynamic range
- noise floor if relevant

Usually irrelevant unless context requires:

- global stereo correlation
- reference-pool width
- mono safety

Exceptions:

Stereo saturation, mid/side saturation, or master-bus saturation may require stereo and mono-safety metrics.

## Compression Profile

Relevant metrics:

- crest factor
- transient loss
- punch
- RMS
- short-term loudness
- dynamic range
- attack/release behavior estimate
- gain reduction if available
- before/after contrast

## Limiter Profile

Relevant metrics:

- integrated LUFS
- short-term loudness
- true peak
- sample peak
- ceiling margin
- loudness range
- crest factor
- transient loss
- distortion risk
- headroom

## EQ Profile

Relevant metrics:

- frequency band energy
- tonal tilt
- low-mid buildup
- mud/body
- harshness
- sibilance/presence
- air/top-end
- masking risk
- before/after tonal delta

## Stereo Profile

Relevant metrics:

- stereo correlation
- side/mid ratio
- mono safety
- L/R balance
- width by frequency band
- low-end mono stability
- side harshness if relevant

## Vocal Profile

Relevant metrics:

- vocal presence range
- low-mid masking
- sibilance/harshness
- midrange balance
- dynamic consistency
- loudness relationship if vocal stem available
- compression/saturation risk if relevant

## Mastering Profile

Relevant metrics:

- LUFS
- true peak
- crest factor
- loudness range
- tonal balance
- stereo safety
- low-end control
- transient contrast
- clipping risk
- reference deltas if Reference Mode is active

## Compare Profile

Relevant metrics:

- A vs B loudness delta
- A vs B peak/ceiling delta
- A vs B crest/dynamics delta
- A vs B tonal delta
- A vs B stereo delta
- A vs B transient/punch difference
- practical conclusion based on user goal

No global reference pool unless explicitly requested.

## Reference Profile

Relevant metrics:

- current mix vs target loudness
- current mix vs target true peak/ceiling
- current mix vs target tonal balance
- current mix vs target dynamics
- current mix vs target width/stereo safety
- current mix vs target punch/crest
- target closeness
- target-specific next steps

## Response Rule

AIFRED should answer in this order:

1. answer the user’s actual question
2. mention the most relevant evidence
3. explain the tradeoff
4. give the next practical move
5. optionally include deeper metrics if useful

## Failure Conditions

Metric relevance fails if:

- every answer shows the same metrics
- irrelevant correlation/loudness data appears in unrelated questions
- saturation advice ignores peak/headroom risk
- limiter advice ignores transient damage
- stereo advice ignores mono safety
- Compare Mode drifts into Reference Mode
- the AI sounds like a generic analyzer dump

## Final Rule

AIFRED should not overwhelm the producer with data.

AIFRED should show the data that matters for the decision being made.

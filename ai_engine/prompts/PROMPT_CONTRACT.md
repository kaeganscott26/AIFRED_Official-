# Prompt Contract

## Purpose

Prompt building converts an `InterpretationPacket` into model context.

It does not generate final responses itself.

Prompt builders prepare structured context for future adapters. They must preserve packet facts, mode, source label, freshness, confidence, relevant metric families, limitations, warnings, and the user question.

## Prompt Inputs

Allowed prompt inputs:

- packet facts
- mode
- source label
- freshness
- confidence
- selected metric families
- limitations
- warnings
- user question
- relevant history if explicitly included later

Forbidden prompt inputs:

- secrets
- API keys
- full local paths
- private metadata
- stale hidden state
- old repo assumptions
- unrelated metric dumps

## Prompt Shape

Future prompts should include:

- role/system constraints
- packet facts
- mode rules
- metric relevance rules
- output contract
- forbidden behavior list
- user question

## No-Canned-Response Rule

Prompt fragments may constrain behavior but must not become fixed final answer templates.

Allowed:

- `Do not invent metrics.`
- `Use only relevant metric families.`
- `Respect Analyze/Reference/Compare mode.`

Forbidden:

- `If peak is above X, say exactly...`
- fixed paragraphs reused across every answer
- generic response blocks that ignore the user question

## Local / Online Parity

OpenAI and local model prompts may differ in length/detail, but both must enforce the same:

- mode rules
- no-invention rules
- metric relevance rules
- source-of-truth rules
- privacy rules
- response structure

## Future Boundary

Phase 4D creates prompt contract only.

No provider prompts are sent in this phase.

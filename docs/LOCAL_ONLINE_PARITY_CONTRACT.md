# Local / Online / No-AI Parity Contract

AIFRED must remain useful in every operating state.

## Supported States

- Online + OpenAI/API available
- Offline + local AI available
- No API configured
- No AI engine available
- Meter-only fallback

## Product Effect Rule

OpenAI and local models do not need identical intelligence.

They must preserve the same trust value.

Same facts.

Same mode rules.

Same metric relevance.

Same warnings.

Same source labeling.

Same no-BS engineering tone.

Same useful outcome.

## OpenAI Mode

OpenAI mode may provide:

- deeper reasoning
- richer nuance
- better edge-case handling
- longer context understanding
- better complex tradeoff explanations

OpenAI mode still must obey all contracts.

It may not invent metrics.

## Local Mode

Local mode may be:

- shorter
- leaner
- faster
- less nuanced

But it must still be:

- grounded in verified data
- mode-aware
- practical
- honest about limitations
- responsive within a few seconds when possible

If local model performance is weak, reduce context rather than hang.

## No-AI Mode

No-AI mode must still be useful.

It should provide:

- truthful metering
- factual flags
- saved reports
- clear status
- no fake interpretation
- no pretend AI response

No-AI mode should say interpretation is unavailable instead of pretending.

## Fallback Rules

If OpenAI fails:

- try local if configured
- otherwise use No-AI fallback

If local fails:

- use No-AI fallback
- do not hang
- do not leave GUI in ambiguous “ready” state

If backend fails:

- plugin analysis should still function locally if possible
- reports should still save locally if possible

## Status Labels

Allowed examples:

- OpenAI Connected
- Local AI Connected
- No AI Configured
- Metering Active Only
- Backend Unavailable
- Local Model Loading
- Last Response Failed
- Offline Mode

Do not show “ready” if the engine cannot respond.

## Failure Conditions

Parity fails if:

- local mode gives random generic advice
- OpenAI mode ignores mode rules
- No-AI mode pretends to interpret
- UI says local AI ready while the model is unavailable
- backend failure kills basic metering
- local model hangs without fallback

## Final Rule

The model is not the product.

The verified data + contracts + interpretation system are the product.

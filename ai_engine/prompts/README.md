# AI Prompts

## Purpose

This folder is reserved for future prompt fragments and prompt-policy documentation.

No production prompts exist yet.

## Future Prompt Topics

- system/developer prompt fragments
- mode rules
- source-of-truth rules
- response constraints
- no-canned-response policy
- metric relevance policy
- privacy rules
- fallback behavior

## Rules

- Prompts must not contain secrets.
- Prompts must not contain API keys.
- Prompts must not expose hidden local paths.
- Prompts must not become hardcoded response templates.
- Prompts must not include fixed product responses selected only from metric thresholds.
- Prompts must not override Python Truth Layer facts.

Future prompts may guide style and constraints, but final AI phrasing must remain contextual to the interpretation packet and user question.

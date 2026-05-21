# AGENTS.md — AIFRED_Official- Agent Operating Contract

This file is law for Codex, local agents, coding assistants, and any automated tool working inside `AIFRED_Official-`.

`AIFRED_Official-` is the flagship clean-room rebuild source of truth.

Old repos may be inspected for reference, but old repo architecture is not automatically valid here.

## Prime Directive

Do not drift.

Do not invent architecture.

Do not skip contracts.

Do not create fake behavior.

Do not hardcode secrets, paths, endpoints, or developer-machine assumptions.

Do not modify implementation files unless the current task explicitly allows it.

## Product Identity

AIFRED is not an “AI mixes for you” plugin.

AIFRED is an AI-assisted mix interpretation system for music producers.

The core rule:

- Python tells the truth.
- AI explains the truth.
- GUI reveals the truth.
- Reports preserve the truth.
- Backend supports the platform.
- Admin controls operations.
- Website presents the product.
- AIFRED teaches the producer.

## Current Build Phase

Until this repo contains the required documentation contracts and skeleton folders, agents must not create DSP, GUI, backend, installer, or production implementation code.

Allowed before implementation:

- create documentation files
- create folder skeletons
- create empty `.gitkeep` files
- create README files
- create planning/checklist files
- inspect old repos when explicitly instructed
- summarize findings without changing files

Forbidden before implementation:

- writing DSP code
- writing plugin code
- writing backend route code
- writing AI adapter code
- writing installer workflows
- creating GitHub Actions
- creating Cloudflare deploy configs
- migrating old code blindly

## Source-of-Truth Rule

This repo outranks all old repos for flagship direction.

Current repo roles:

- `AIFRED_Official-` = flagship clean-room rebuild source of truth
- `AIFRED` = current operational prototype / last-known-good reference
- `aifred-plugin` = legacy plugin reference only
- `aifred-site` = website/backend reference only unless intentionally migrated
- `aifred-admin` = admin app reference only unless intentionally migrated
- `aifred-downloads` = placeholder/reference only
- `kaegan.exe` = separate project; do not touch for AIFRED tasks

If old repos conflict with this repo’s contracts, this repo wins unless the user explicitly approves a migration.

## No Mega-Prompts

Agents must work surgically.

Each task should include no more than two phases:

1. inspect / explain
2. implement only the requested change

Do not combine unrelated work.

Do not build multiple layers at once.

Do not “clean up” files that were not requested.

Do not silently refactor.

## Python Truth Layer Rules

Python owns factual analysis only.

Python may calculate:

- sample peak
- true-ish peak / ceiling state
- RMS
- LUFS
- short-term loudness
- loudness range
- crest factor
- stereo correlation
- mid/side balance
- frequency band energy
- tonal balance
- dynamic range
- transient behavior
- A/B comparison
- reference comparison
- export history
- progress memory

Python may create factual flags.

Python must not generate final user-facing advice.

Forbidden pattern:

```python
if lufs > -8:
    return "Your mix is too loud and smashed."
```

Correct pattern:

```text
Python calculates facts.
AI interprets facts.
```

## AI Interpretation Rules

The AI layer explains verified data in context.

The AI must consider:

- user question
- active mode
- source of truth
- relevant metrics
- confidence state
- mix state
- goal if known
- reference context only when allowed
- compare context only when allowed
- history only when allowed

The AI must not:

- invent metrics
- fake certainty
- dump irrelevant metrics
- use canned response templates as the product
- reference the global reference pool outside Reference Mode unless explicitly asked
- answer from stale data without saying so
- output raw JSON as the main user-facing report

## Mode Contract

Analyze Mode = current mix by itself.

Reference Mode = current mix against selected target/reference/pool.

Compare Mode = Mix A vs Mix B only.

Compare Mode does not care whether Mix B is another render, old master, client mix, or commercial song. In Compare Mode, B is simply B.

Do not leak Reference Mode behavior into Analyze or Compare.

## Meter Trust Rules

No fake meters.

No placeholder values displayed as real analysis.

No filled visual bars when the numeric value is zero, unavailable, stale, or unmapped.

Waiting, unavailable, stale, and zero must be visually distinct.

If the GUI shows a meter, it must be bound to verified analysis state.

## Secrets and Paths

Never commit secrets.

Never hardcode:

- OpenAI keys
- Cloudflare tokens
- GitHub tokens
- PayPal tokens
- local user paths
- machine-specific paths
- developer-only endpoints
- absolute build paths
- private folder names
- private IP addresses

Use config files, environment examples, user settings, or secure deployment secrets.

## GitHub Actions Rule

Do not create automatic build/deploy workflows yet.

No CI/CD until the repo has:

- docs/contracts
- skeleton
- Python tests
- acceptance gates
- explicit user approval

When workflows are eventually added, they must be manual-first using `workflow_dispatch`.

## Commit Rules

Small commits only.

Each commit must have one purpose.

Commit message examples:

- `Add agent operating contract`
- `Add project source-of-truth index`
- `Add mode contract`
- `Add pre-code release gates`

Bad commit messages:

- `fix stuff`
- `build flagship`
- `updates`
- `final`

## Stop Conditions

Stop and ask before proceeding if:

- a task conflicts with this file
- old repos disagree with flagship docs
- implementation requires secrets
- implementation requires hardcoded paths
- test results are missing
- the requested change spans multiple unrelated systems
- the task would create production behavior before contracts exist

## Final Reminder

AIFRED must be accurate, explainable, and usable before it is flashy.

Zero fake behavior.

Zero trust-breaking defects.

No drift.

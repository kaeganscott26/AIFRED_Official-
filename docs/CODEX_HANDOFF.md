# Codex Handoff Contract

This document defines how Codex or any coding agent may work on `AIFRED_Official-`.

## Agent Role

Codex is a tool.

Codex does not own the architecture.

Codex may help with:

- scaffolding
- file creation
- small implementation tasks
- tests
- routing
- refactoring when explicitly requested
- build scripts when approved
- GUI shell work when the spine is ready
- packaging when acceptance gates exist

Codex may not:

- invent DSP math
- invent product behavior
- change the mode contract
- change the source-of-truth contract
- modify Python math without approval
- add fake UI data
- hardcode secrets
- hardcode local paths
- create automatic CI/CD without approval
- migrate old repo code blindly
- collapse multiple phases into one big change

## Prompt Shape

Every Codex prompt should be small.

Preferred prompt structure:

1. inspect current files relevant to this task
2. explain what you found
3. implement only the requested change
4. list files changed
5. list tests/validation performed
6. stop

## Maximum Scope

A prompt should cover no more than two phases.

Good:

“Create `docs/MODE_CONTRACT.md` and update README link. Do not touch implementation files.”

Good:

“Create `python_brain/README.md` and empty package skeleton. Do not implement metrics yet.”

Bad:

“Build the whole Python brain, AI engine, plugin GUI, backend, and installer.”

## Required Pre-Work Before Implementation

Before writing code, Codex must confirm:

- relevant contract exists
- target folder exists
- task is within current phase
- no secrets are required
- no hardcoded paths are required
- no old repo code is being copied blindly

## Change Report

Every Codex output must include:

- files changed
- files inspected
- summary of changes
- assumptions made
- tests run or not run
- next recommended step
- any contract risk

## Rejection Conditions

Reject or revert Codex output if it:

- touches unrelated files
- rewrites architecture
- creates fake meters
- adds canned response logic
- references old repos as authority
- creates hidden dependencies
- adds CI/CD early
- hardcodes secrets or paths
- skips documentation
- fails to explain changes

## Commit Rule

Commit only after review.

Small commits only.

One purpose per commit.

## Final Rule

Codex does boring work around verified decisions.

Codex does not make flagship decisions.

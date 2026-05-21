
# Python Brain

## Purpose

'python_brain/' contains AIFRED's Python Truth Layer.

----

This layer is responsible for factual audio-analysis preparation, validation, safe file loading, portable local paths,
metric readiness checks, and future DSP measurment support.

"Python tells the truth."

That means this folder should only expose facts that can be directly loaded, validated, measured, or explicitly marked 
as unavailable. It must not invent metrics, pretend unfinished DSP is complete, or generate final user-facing advice.

____
----

## Current Implementation Status

This folder has moved beyond contracts-only scaffolding.

Current implementation includes:

- Safe WAV metadata loading (.mp3 coming_soon)

- Normalized WAV PCM buffer loading

- Audio input validation helpers

- Portable AIFRED path resolution

_ Report directory path resolution

- Metric result state validation

- Analyze / Reference / Compare mode boundary validation

- Loudness window infrastructure

- Mean-square window helper calculations

- Loudness availability labels

- Generic biquad coefficient and filter-state primitives

- Generic mono and interleaved biquad sample processing

----
----

# Current intentionally unavailable implementation includes:

- Final LUFS calculation

- BS.1770 integrated loudness

- Momentary LUFS

- Short-term LUFS 

- Loudness range

- True peak / dBTP

- Verified K-weighting coefficient lookup

- K-weighting filter application

- Final user-facing mix advice

Unavailable features must raise 'NotImplementedError' or return explicit unavailable state. They must not return fake placeholder values.

## Folder Responsibilities 

----

'python_brain/' may contain:


- Factual audio loading

- Factual audio metadata extraction

- Validated PCM sample preparation

- DSP helper primitives 

- Metric availability checks

- Metric relevance prepartation

- Analysis state validation

- Report data prepartation 

- Tests, fixtures, and scripts that support factual audio analysis

----

----

'python_brain/' must not contain:

- GUI/plugin source code

- Backend routes

- Cloudflare configuration

- Payment logic

- Secrets

- Developer-machine absolute paths

- Final AI-generated user advice

- OpenAI/Ollama/LM Studio provider calls

- Fake DSP results 

- Fake LUFS

- Fake true peak

- Copied old repo code without approved migration

____


## Major Modules

### 'aifred_brain/__init__.py'

Defines the Python Truth Layer package boundary.

This package must not generate final user-facing advice, call AI providers, create backend routes,
or implement plugin behavior.

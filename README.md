# AIFRED_Official-


AIFRED is an AI-assisted mix interpretation system for music producers.

It is not an "AI mixes for you" plugin.

AIFRED's purpose is to help porducers understand hwat their tools are doing, measure their progress over time, and make more confident mix decisions.

Processing changes the sound.
AIFRED changes the producer.

---

## Current Status

This repository is the official flagship rebuild workspace for AIFRED VST. 

The current public/protype versions of AIFRED proved the concept, but the flagship build is being rebuilt cleanly from locked architecture.

Old repos may be used as reference only.

This repo is the new source of truth for AIFRED VST. 

___

## Product Thesis

Most producers do not get stuck because they lack plugins.

They get stuck because they do no know wheter the move they just made actually helped.

AIFRED shortens that loop:

1. The producer makes a mix decision.

2. AIFRED measures what changed.

3. AIFRED explains why that change matters.

4. The producer connects the action to the outcome.

Over time, this turns every mix decision into repeatability and consistancy.

Producers spend less time learning how to mix and master and spend more time being creative leading to better music.

___


## Core Architecture

AIFRED is built around a strict seperation of responsibility:

- Python tells the truth.

- AI explains the truth.

- The GUI reveals the truth.

- Reports preserve the truth.

- The backend supports the platform.

- The admin app controls operations.

- The website presents the product.

___

## Python Truth Layer

The Python layer is responsible for factual audio analysis only.

It calculates real signal data such as:

- Sample peak

- True peak / ceiling state

- RMS

- LUFS (integrated / short-term)

- Loudness Range (LU)

- Crest Factor {(dB) = 20 log10 (Peak_Value % RMS_Value)}

- Stereo Correlation

- Mid / Side balance

- Frequency band energy distribution

- Tonal Balance

- Dynamic Range 

- Transient behavioral analysis

- A / B comparison 

- Reference comparison 

- Export Mix History (Last 10 Mix Sessions)

- Progressive Memory

---

AI Interpretation Layer

The AI layer recieves verified data from the truth layer and explains it in context.

The AI MUST consider:

- User question

- Active mode

- Relevant metrics

- Mix state

- DSP mathematics

- Reference Context (reference_pool or user_reference)

- Compare Context if applicable

- Export / history context if applicable (Up to 10 mix sessions)

- User goal if stated

The AI output must always stay non-deterministic. No pre-determined responses / phrases shall be used by the AI interpretation level.

___

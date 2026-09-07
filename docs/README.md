# AIFRED documentation

## Start here

- [Product and operator overview](../README.md)
- [Current implementation status](IMPLEMENTATION_STATUS.md)
- [Architecture and ownership](ARCHITECTURE.md)
- [Intelligence architecture map](../intelligence/README.md)

## What is AIFRED?

AIFRED is a transparent plugin that measures DAW audio, observes measurements over bounded time, and publishes deterministic engineering context. [Architecture](ARCHITECTURE.md) defines the active pipeline and phase boundary.

## DSP and analysis

- [Shared DSP algorithms](../shared-dsp/README.md): engine, spectrum, loudness, true peak, stereo, and 30-band telemetry
- [DSP profiles and presentation](DSP_CONFIGURATION.md): the four validated modes and their exact settings
- [Testing](TESTING.md): automated coverage and manual comparison limits

## Observation

- [BufferHunter](BUFFER_HUNTER.md): lifetime, epochs, freshness, bounded statistics, and persistence

## Semantics

- [aifred_filter](AIFRED_FILTER.md): deterministic states, reference compatibility, and `FilteredMixContext`

## Intelligence

- [Intelligence layer](../intelligence/README.md): authoritative post-`FilteredMixContext` ownership map
- [Intelligence phases](../intelligence/PHASES.md): implementation order and completion gates
- [Ecosystem configuration](ECOSYSTEM_CONFIGURATION.md): local `.env`, Cloudflare, GitHub, admin and provider ownership
- [Production API](API_REFERENCE.md): public/reference/admin route contracts

## Runtime

- [Installation](INSTALLATION.md): VST3 and Intelligence Host ownership
- [Beta and Official coexistence](COEXISTENCE.md): paths, ports, IDs, and migration limits
- [Future architecture](FUTURE.md): intelligence and Babylon gates

## Build and release

- [Build](BUILD.md): compiler prerequisites, targets, and canonical output
- [Distribution](DISTRIBUTION.md): stage, manifest, verification, promotion, and recovery
- [End-user configuration template](../config/distribution/README.md): provider setup without bundled secrets
- [Development](DEVELOPMENT.md): source and Git discipline
- [Repository construction](REPOSITORY_CONSTRUCTION.md): authoritative locations and prohibited dependencies

## Operations

- [Cloudflare production](CLOUDFLARE_PRODUCTION.md): Pages, KV, R2, bindings and deployment ownership
- [Admin guide](ADMIN_GUIDE.md): private operational clients
- [Ops guide](OPS_GUIDE.md): production operations surface
- [Administrator command reference](ADMIN_COMMAND_REFERENCE.md): generated allowlisted command map

## Debugging

- [Debugging guide](DEBUGGING.md): symptom to owner, source, and test
- [Testing](TESTING.md): commands and evidence boundaries

## Related

- [Architecture](ARCHITECTURE.md)
- [DSP Configuration](DSP_CONFIGURATION.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Future](FUTURE.md)

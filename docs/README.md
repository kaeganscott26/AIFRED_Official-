# AIFRED documentation

## Start here

- [Product and operator overview](../README.md)
- [User guide](USER_GUIDE.md)
- [Current implementation status](IMPLEMENTATION_STATUS.md)
- [Architecture and ownership](ARCHITECTURE.md)
- [Repository map](REPOSITORY_MAP.md)
- [Backend map](../backend_map.md)
- [Website and Cloudflare map](../website_map.md)
- [Changelog](../CHANGELOG.md)

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

## Configuration and future phases

- [Ecosystem configuration](ECOSYSTEM_CONFIGURATION.md): local `.env`, Cloudflare, GitHub, admin and provider ownership
- [Production API](API_REFERENCE.md): public/reference/admin route contracts
- [Future architecture](FUTURE.md): intelligence and Babylon remain behind the migration gate

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
- [Cloudflare migration checklist](CLOUDFLARE_MIGRATION_CHECKLIST.md): staging, rollback, production, and Beta retirement gates
- [2026-09-10 cutover readiness](cloudflare/2026-09-10-cutover-readiness.md): current staging evidence and production blockers
- [Admin guide](ADMIN_GUIDE.md): private operational clients
- [Ops guide](OPS_GUIDE.md): production operations surface
- [Administrator command reference](ADMIN_COMMAND_REFERENCE.md): generated allowlisted command map

## Debugging

- [Debugging guide](DEBUGGING.md): symptom to owner, source, and test
- [Testing](TESTING.md): commands and evidence boundaries

## Related

- [Architecture](ARCHITECTURE.md)
- [Repository Map](REPOSITORY_MAP.md)
- [DSP Configuration](DSP_CONFIGURATION.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Future](FUTURE.md)

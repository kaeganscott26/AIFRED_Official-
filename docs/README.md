# AIFRED documentation

## Start here

- [Product and operator overview](../README.md)
- [Current implementation status](IMPLEMENTATION_STATUS.md)
- [Architecture and ownership](ARCHITECTURE.md)

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

## Runtime

- [Installation](INSTALLATION.md): VST3 and Intelligence Host ownership
- [Beta and Official coexistence](COEXISTENCE.md): paths, ports, IDs, and migration limits
- [Future architecture](FUTURE.md): intelligence and Babylon gates

## Build and release

- [Build](BUILD.md): compiler prerequisites, targets, and canonical output
- [Distribution](DISTRIBUTION.md): stage, manifest, verification, promotion, and recovery
- [Development](DEVELOPMENT.md): source and Git discipline
- [Repository construction](REPOSITORY_CONSTRUCTION.md): authoritative locations and prohibited dependencies

## Debugging

- [Debugging guide](DEBUGGING.md): symptom to owner, source, and test
- [Testing](TESTING.md): commands and evidence boundaries

## Related

- [Architecture](ARCHITECTURE.md)
- [DSP Configuration](DSP_CONFIGURATION.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Future](FUTURE.md)

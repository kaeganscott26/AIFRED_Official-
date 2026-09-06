# Development

Read [Architecture](ARCHITECTURE.md), [DSP Configuration](DSP_CONFIGURATION.md), [Shared DSP](../shared-dsp/README.md), and [Testing](TESTING.md) before changing analysis code.

## Source rules

- Put measurements in `aifred_engine`, temporal statistics in BufferHunter, and deterministic interpretation in `aifred_filter`.
- Keep network, file, JSON, model, reference lookup, locks, and logging out of `processBlock`.
- Preserve plugin/state IDs, frontend identity, physical units, and continuous float32 GUI targets.
- Require a failing test or reproducible measurement before changing a DSP formula. Document the old formula, failure, correction, and rerun evidence.
- Keep Official and Beta independently buildable. Review and version both pinned shared-source copies together.
- Do not expose future profiles, intelligence tools, personality/memory systems, or Babylon controls.

## Git workflow

Before edits, inspect branch status, local/tracking/live remote HEAD, ahead/behind, and the full diff. Preserve unrelated work. Use fast-forward pulls, never force-reset or force-push, and keep generated output and secrets out of commits.

Before release or push, run both channel pipelines, compare the shared-core inventory, review the complete diff, and separate automated evidence from installed and DAW evidence.

## Related

- [Repository Construction](REPOSITORY_CONSTRUCTION.md)
- [Build](BUILD.md)
- [Distribution](DISTRIBUTION.md)
- [Debugging](DEBUGGING.md)

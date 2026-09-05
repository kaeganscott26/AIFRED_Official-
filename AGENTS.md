# AIFRED Official agent instructions

Read workspace AGENTS.md, docs/ARCHITECTURE.md, shared-dsp/README.md, docs/DEVELOPMENT.md and docs/REPOSITORY_CONSTRUCTION.md.

Current ownership: aifred_engine -> EngineSnapshot -> BufferHunter -> ObservationSnapshot -> aifred_filter -> FilteredMixContext -> AifredIntelligenceHost. Preserve DSP precision, realtime safety, frontend identity and plugin/state IDs. GUI positions are continuous float32; only text/model rounds. No duplicate algorithm, raw snapshot model path, Python runtime or analyzer fallback.

Keep both repositories independently reproducible with their pinned shared-source inventory. Use canonical platform output, exact artifacts and recoverable promotion. Follow current user scope/authorization. Expose no unimplemented future tools/profiles. Report automation separately from installed/DAW validation. Git is the source archive; no legacy/archive source, force reset/push, secrets or generated output in commits.

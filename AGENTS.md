# AIFRED Official agent instructions

This repository owns the flagship source and the planned shared analyzer design. Read [the repository construction guide](docs/REPOSITORY_CONSTRUCTION.md) before architectural work. Read [current architecture](docs/ARCHITECTURE.md) before editing existing behavior.

The future direction is DAW audio -> aifred_engine -> BufferHunter -> aifred_filter -> future LLM/context. Current C++ analyzers and .NET AifredEngine remain active until a separate rewrite task replaces them. They provide reference behavior, not implementation code for the new engine.

Preserve live audio, authoritative measurements, explicit validity and realtime safety. GUI/model/personality text never defines DSP facts. No allocation without bounds, locks, I/O, network, inference or tool execution on the audio thread. No fake meters or invented measurement standards.

Follow the user's current task scope. Construction work may change docs/build tooling/scaffolding, but must not change DSP, audio, GUI or provider behavior. Keep Beta and Official independent; preserve plugin IDs and user data. Implement no future feature merely because a scaffold names it.

Git history is the repository archive. Reconcile useful facts before deleting redundant documents; do not create archive/legacy/deprecated directories. Use exact platform output paths and recoverable Trash cleanup. Never use blanket generated-folder deletion.

Run checks appropriate to each change. Report executed results, skips and unvalidated platforms. Do not claim installed-host validation from a successful compile. Keep changes reviewable and commits scoped; no commit/push/deployment unless requested.

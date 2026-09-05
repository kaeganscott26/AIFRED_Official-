# Current Official architecture

CURRENT: AIFRED 4.0.0-alpha.2, native JUCE 8.0.8 VST3 plus .NET 10 Windows companion. The plugin analyzes mono/stereo DAW input without intended signal modification. Python does not participate in this native runtime.

DAW buffer -> PluginProcessor::processBlock -> AnalysisCoordinator -> Level/Loudness/Stereo/Spectrum analyzers -> atomic AnalysisSnapshot -> PluginEditor (60 Hz) -> native meters and embedded WebView visualization.

| Component | Purpose/status | Owner/runtime | Build/output |
|---|---|---|---|
| core/dsp | CURRENT levels (100 ms), short-term K-weighted loudness (3 s/100 ms update), stereo (400 ms/100 ms update), 2048-point Hann FFT | Realtime C++ | CMake Aifred_VST3 and smoke tests |
| core/analysis | CURRENT coordinator, explicit-validity snapshot, comparison deltas | C++ | Same target; snapshots in memory |
| plugin/src/PluginProcessor | CURRENT mono/stereo host adapter, finite-input validation; state save/restore currently empty | Audio processor | VST3 |
| plugin/src/PluginEditor | CURRENT meters, captures, mode selection, question controls | Message thread | VST3 |
| plugin/visualization | CURRENT embedded HTML/CSS/JS/Three assets; presentation only | JUCE WebView | Embedded binary resources |
| AnalysisContextSerializer | CURRENT aifred.context.v1, eight-region mean FFT-bin-power summary | C++, outside audio thread | Linked into VST3 |
| AifredEngineClient | CURRENT asynchronous /health and /chat, process-wide singleton | C++ worker threads | VST3 |
| ReferenceClient | CURRENT asynchronous read-only aifred.references.v1 catalog; process-wide client | C++ background HTTP | VST3; memory catalog |
| Compare | CURRENT editor-owned captured A/B snapshots; B-minus-A deltas | ComparisonEngine / editor | C++ comparison tests |
| tools/AifredEngine | CURRENT /health, /chat, settings, restart acknowledgement; Ollama/compatible routing | .NET Windows process | out/windows-x64/current/AifredEngine |
| python_brain | EXPERIMENTAL offline WAV analysis, validation/report primitives | Python CLI/tests only | Explicit report destination; no VST linkage |
| ai_engine | EXPERIMENTAL configuration/packet validation and unavailable provider stubs | Python tests only | No provider runtime |
| bridge | EXPERIMENTAL dataclasses and file/JSON smoke roundtrip | Python tests only | No audio execution or VST bridge |
| tests, component tests | CURRENT test sources; some Python future cases skipped | CTest/unittest/.NET | out/<platform>/build |
| scripts | CURRENT Windows build/release; other platform/lifecycle scaffolding | Developer tools | build/stage/current |
| core/update, update | EXPERIMENTAL manifest validation/mock contract | C++ header/JSON | No updater |
| core/version | CURRENT build identity | C++ | Embedded version/commit/config |
| Assets, plugin/resources | Tracked brand/assets and resource placeholders | Source assets | Only explicitly listed resources are embedded |
| admin_app, backend, website | UNIMPLEMENTED product scaffolds | No runtime | None |
| shared-dsp | PLANNED shared engine/BufferHunter/filter/profile/snapshot ownership | No runtime or linked targets | None |
| out | GENERATED compiler/candidate/current product trees | Build tooling | Platform-owned output |
| .agents, .codex | CURRENT agent guidance | Developer tooling | None |

AnalysisSnapshot contains sample peak, maximum sample over, RMS, crest, short-term LUFS, M/S side-energy-share width, correlation, signal/clip state, sample clock, sequence, 1025 FFT bins and seven compatibility bands. It does not implement the planned 30-center telemetry/profile system. FFT stereo input is the defined summed signal; preserve current behavior as baseline and validate anti-phase cases before future changes.

The editor stores latestSnapshot separately from smoothed presentation values. A question serializes that snapshot and mode context, then AifredEngineClient posts to loopback .NET AifredEngine, which calls Ollama /api/chat or an OpenAI-compatible /chat/completions endpoint. The provider receives a system instruction plus current question/context; displayed chat history is not transmitted as a durable conversation. No BufferHunter rolling observation layer exists yet. Freshness currently derives from signal/sequence, so halted-host freshness needs future validation.

Analyze sends current facts; Compare sends A, B and deltas; Reference sends the chosen catalog profile and compatible deltas. No global reference data belongs in Compare. Historical reference bands remain labeled as such and are not expanded into invented FFT bins. Reference retrieval failure clears/marks unavailable catalog state. History UI does not establish durable observation history.

Provider absence affects chat availability, not native metering. .NET settings use environment overrides AIFRED_PROVIDER, AIFRED_PROVIDER_ENDPOINT, AIFRED_PROVIDER_MODEL and AIFRED_PROVIDER_API_KEY. Secrets remain local and responses expose only configured-state indicators. Known multi-instance/channel limitations are in COEXISTENCE.md.

PLANNED: [shared construction contract](REPOSITORY_CONSTRUCTION.md). [Python ownership](PYTHON_OWNERSHIP.md) distinguishes retained tests from native runtime authority. No source folder claims an additional production brain.

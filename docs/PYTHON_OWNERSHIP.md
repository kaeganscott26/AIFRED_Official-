# Python ownership

CURRENT native product: no Python process, subprocess or file/JSON bridge connects the VST to its .NET companion. CMake lists C++ sources; AifredEngineClient posts JSON directly to the .NET /chat route. Python contributes tests/offline experiments only. No current reference-catalog ingestion path calls Python; the native ReferenceClient consumes service metadata.

| Files/component | Observed caller/role | Disposition |
|---|---|---|
| python_brain/aifred_brain/audio_loader.py | PCM WAV loader, offline smoke/tests | Keep offline developer/fixture tool |
| level_metrics.py, stereo_metrics.py, frequency_metrics.py | Offline signal measurements called by smoke/tests | Keep testable reference behavior; no native truth authority |
| loudness_metrics.py | Window/availability, generic filter primitives; complete LUFS/true peak unavailable | Keep experimental tests; never describe as native loudness engine |
| analysis_state.py, validation.py, privacy.py, config_paths.py | Validation, metadata/privacy and explicit user paths | Keep developer/offline support |
| tonal_balance.py, dynamics_metrics.py, transient_metrics.py | Partial factual helpers and unavailable future features | Keep tested experiments; not production DSP modules |
| metric_relevance.py, interpretation_packet.py | Offline factual packet selection/schema | Keep contract tests; future production context uses new shared contracts |
| compare_ab.py, reference_compare.py | Offline supplied-state deltas | Keep test/reference support; no background pool ingestion |
| export_history.py, progress_memory.py, report_writer.py | Explicit offline record/report helpers | Keep current tests and user-directed tooling; no native session memory |
| python_brain/scripts/aifred_truth_smoke.py | Explicit developer CLI runs offline truth smoke | Keep; reports use explicit destinations |
| ai_engine/adapters/* | Base result types, NoAI status fallback, structural router, Local/OpenAI stubs | Keep existing contract test suite; stubs perform no provider calls |
| ai_engine/config/*, prompts/*, response_validation.py | Config/packet/response guardrails | Keep experimental contract coverage; do not wire into native provider route |
| bridge/bridge_contract.py, file_json_bridge.py | Data shape and file roundtrip tests only | Keep contract fixtures; not a launched backend |
| */tests/*.py | unittest coverage, including explicit skipped future cases | Keep; report skips separately |
| scripts/common/*.py | Build manifest/promotion and repository checks | Developer tools only; no audio/model behavior |

No Python implementation is removed in this pass because the existing tests/smoke tooling exercise it. Removing those experiments later requires a scoped test-fixture migration, not automatic production adoption. Old phase prose that said Python owns all future DSP was superseded by the construction guide.

Offline semantics: Analyze uses this input alone; Compare uses supplied A/B; Reference requires a selected target. Packets/results carry source, validity, mode and limitations, and scrub private paths. Reports support text/HTML with structured sidecars, timestamps, relevant metrics and availability. The current fallback report root is AIFRED_HOME/Reports or ~/.aifred/Reports; an explicit project destination uses AIFRED Reports. A GUI project-folder picker and native report/history integration remain unimplemented.

Run each suite from the repo root as documented in TESTING.md. Do not equate skipped standards tests or passing stub tests with implemented providers or validated loudness.

# Debugging

Trace meter problems in this order:

```text
DAW buffer -> DSP input -> EngineSnapshot -> ObservationSnapshot
           -> FilteredMixContext or ViewSnapshot -> rendered control
```

| Symptom | Owner to inspect | Source | Test |
|---|---|---|---|
| Audio changes | plugin adapter | [PluginProcessor.cpp](../plugin/src/PluginProcessor.cpp) | [state pass-through](../tests/state_contract_tests.cpp) |
| Wrong FFT frequency/bin count | engine spectrum | [Spectrum.cpp](../shared-dsp/src/Spectrum.cpp) | [core FFT tests](../shared-dsp/tests/core_tests.cpp) |
| Spectrum looks clipped at the floor | presentation | [PluginEditor.cpp](../plugin/src/PluginEditor.cpp), [WebView renderer](../plugin/visualization/visualizer.js) | [frontend contracts](../tests/frontend_contract_tests.cpp) |
| 30-band value looks wrong | power integration | [Spectrum::extractBands](../shared-dsp/src/Spectrum.cpp) | [core telemetry tests](../shared-dsp/tests/core_tests.cpp) |
| Live phase meter feels slow | engine stereo window and frontend source | [Engine.cpp](../shared-dsp/src/Engine.cpp), [ViewSnapshot.h](../plugin/src/ViewSnapshot.h) | [diagnostic response tests](../shared-dsp/tests/core_tests.cpp) |
| Observation resets unexpectedly | engine/BufferHunter epoch | [Engine.cpp](../shared-dsp/src/Engine.cpp), [BufferHunter.cpp](../shared-dsp/src/BufferHunter.cpp) | [epoch tests](../shared-dsp/tests/core_tests.cpp) |
| Old observation appears under a new profile | identity adapter | [Pipeline.cpp](../shared-dsp/src/Pipeline.cpp) | [profile epoch tests](../shared-dsp/tests/core_tests.cpp) |
| Reference is unavailable | filter compatibility | [Filter.cpp](../shared-dsp/src/Filter.cpp) | [filter tests](../shared-dsp/tests/core_tests.cpp) |
| Host health fails | channel transport | [IntelligenceClient.cpp](../shared-dsp/src/IntelligenceClient.cpp), [HostSettings.cs](../tools/AifredIntelligenceHost/HostSettings.cs) | [host contracts](../tools/AifredIntelligenceHost.Tests/Program.cs) |
| Update stops before install | release/install recovery | [release.py](../scripts/common/release.py), [install-ownership.ps1](../scripts/common/install-ownership.ps1) | [release tests](../scripts/tests/test_release.py) |

Do not adjust a DSP formula to correct a drawing issue. Record the raw snapshot value, current profile/revision, sample rate, signal fixture, and failing assertion before changing measurement code.

## Related

- [Testing](TESTING.md)
- [Architecture](ARCHITECTURE.md)
- [DSP Configuration](DSP_CONFIGURATION.md)
- [Installation](INSTALLATION.md)

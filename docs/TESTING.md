# Testing

## Canonical commands

Official:

```powershell
pwsh -NoProfile -File scripts/windows/build.ps1 -Action test
```

Beta runs the same C++/.NET/Python checks plus its API/archive Node suites and website checks:

```powershell
pwsh -NoProfile -File scripts/windows/build.ps1 -Action test
```

Run the independent generated-fixture comparison when FFmpeg is available:

```powershell
python -B scripts/common/validate_meter_reference.py
```

## Automated coverage

| Area | Evidence |
|---|---|
| Peak, RMS, crest, silence, clipping | [core tests](../shared-dsp/tests/core_tests.cpp) |
| BS.1770 K weighting, M/ST/I, gates, LRA | [core tests](../shared-dsp/tests/core_tests.cpp), [FFmpeg fixture](../scripts/common/validate_meter_reference.py) |
| True-peak reconstruction | [core tests](../shared-dsp/tests/core_tests.cpp), FFmpeg fixture |
| FFT mapping, Parseval, averaging configuration, 1025/4097 bins | [core tests](../shared-dsp/tests/core_tests.cpp) |
| Exact 30 centres, 850 Hz, geometric power integration | [contracts](../shared-dsp/include/aifred/Contracts.h), [core tests](../shared-dsp/tests/core_tests.cpp) |
| Correlation, M/S, balance, width, 100 ms diagnostic response | [core tests](../shared-dsp/tests/core_tests.cpp) |
| BufferHunter capacity, windows, statistics, trends, freshness, epochs | [core tests](../shared-dsp/tests/core_tests.cpp) |
| aifred_filter units, regions, states, reference compatibility | [core tests](../shared-dsp/tests/core_tests.cpp) |
| SPSC ordering and overflow | [core tests](../shared-dsp/tests/core_tests.cpp) |
| Frontend live/observed ownership and click-ready metadata | [frontend tests](../tests/frontend_contract_tests.cpp) |
| Profile and presentation persistence, old-state fallback, pass-through | [state tests](../tests/state_contract_tests.cpp) |
| Intelligence Host identity and provider routing | [host tests](../tools/AifredIntelligenceHost.Tests/Program.cs) |
| Repository links/layout and shared parity | [repository check](../scripts/common/check_repository.py), [shared-core check](../scripts/common/check_shared_core.py) |
| Release failure preservation and ownership | [release tests](../scripts/tests/test_release.py) |
| Stage/current/install hashes | [release verifier](../scripts/common/release.py), [install ownership](../scripts/common/install-ownership.ps1) |

The profile tests compare exact configuration and observable FFT/window/observation/stereo behavior. They do not accept profile names as proof.

## Evidence limits

CTest and JUCE module-info generation prove compiled contracts and VST3 factory enumeration. They do not prove DAW scanning, realtime CPU under host load, UI rendering in a host, or equivalence with proprietary analyzers.

The generated FFmpeg fixture compares a 48 kHz stereo 1 kHz two-plateau programme. Its tolerances are `0.15 LU` integrated, `0.3 dB` true peak, and `1 LU` LRA. It is an independent implementation comparison, not complete ITU/EBU certification.

## Manual validation still required

- FL Studio scan, load, pass-through, state restore, profile switching, and simultaneous Beta/Official loading
- Waves, Voxengo SPAN, FabFilter, and iZotope/Ozone comparisons with matched settings and source audio
- full EBU loudness test set and true-peak edge cases
- realtime CPU profiling for all four profiles
- macOS and Linux build, package, install, and runtime validation

## Related

- [Architecture](ARCHITECTURE.md)
- [DSP Configuration](DSP_CONFIGURATION.md)
- [Debugging](DEBUGGING.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)

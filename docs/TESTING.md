# Testing

CURRENT Windows wrapper: scripts/windows/build.ps1 -Action test builds native targets, runs CTest and the .NET contract executable, then the three Python suites. No model credentials or network provider are needed for these tests.

```sh
ctest --preset windows-release
dotnet run --project tools/AifredEngine.Tests/AifredEngine.ContractTests.csproj -c Release
python -B -m unittest discover -s python_brain/tests
python -B -m unittest discover -s ai_engine/tests
python -B -m unittest discover -s bridge/tests
python -B scripts/common/check_repository.py
```

CMake registers aifred_dsp_smoke, aifred_comparison_tests and aifred_integration_contract_tests. DSP smoke primarily uses 48 kHz and 512-sample blocks, covering analytic levels, stereo/spectrum, validity, clipping and reset behavior. These tests do not certify all rates, block sizes or standards. Python contains intentionally skipped future tests; list them separately from passing cases.

After construction changes, verify exact staged VST3 structure, plugin/engine manifest hashes and source identity. Test release promotion failure/rollback without real installed data. Check changed files and documentation links; no DSP/GUI/provider implementation changes belong in construction diffs.

Release gates still require FL Studio load, real signal metering, editor close/reopen, stop/resume, saved-session behavior, multiple instances, channel coexistence and installation/uninstallation checks. Compile success is not host validation. Signing/notarization, macOS and Linux are NOT VALIDATED here. See the construction guide for the future expanded algorithm/observation/profile acceptance matrix.

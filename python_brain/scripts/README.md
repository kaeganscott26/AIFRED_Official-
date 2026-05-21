# Python Brain Scripts

Scripts in this folder are helper-only.

They may eventually assist with local validation, fixture generation, or report inspection, but they must not become hidden product behavior.

Rules:

- no production DSP hidden in scripts
- no secrets
- no hardcoded local paths
- no modification of old repos
- no silent cleanup
- no deployment behavior
- no generated outputs committed without review

## Truth Layer Smoke Runner

`aifred_truth_smoke.py` is a small factual CLI smoke test for the Python Truth Layer.

Purpose:

- run existing truth-layer modules together
- use a generated safe synthetic WAV when no input is provided
- optionally analyze a user-provided WAV file
- optionally write factual `.txt` and `.html` reports

Run with a generated synthetic WAV:

```powershell
python python_brain/scripts/aifred_truth_smoke.py
```

Run with JSON output:

```powershell
python python_brain/scripts/aifred_truth_smoke.py --json
```

Write factual reports:

```powershell
python python_brain/scripts/aifred_truth_smoke.py --write-reports --output-dir ./scratch/reports
```

Run with a WAV file:

```powershell
python python_brain/scripts/aifred_truth_smoke.py --input path/to/file.wav --question "Should I add saturation?"
```

This script is not AI interpretation, chat output, plugin behavior, GUI behavior, or VST behavior. It prints and writes factual smoke-test output only.

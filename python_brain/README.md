# Offline Python analysis experiments

EXPERIMENTAL: these modules support offline WAV smoke tests, fixtures, factual state/privacy validation and report helpers. They are not called by the current VST or .NET provider route and must not become a second production DSP engine.

See [per-module ownership](../docs/PYTHON_OWNERSHIP.md) and [test commands](../docs/TESTING.md). audio_loader accepts the implemented PCM/WAV path; level/stereo/frequency helpers have focused tests. Complete loudness/true-peak and several semantic features remain unavailable. Generic biquad code is not evidence of verified K-weighting coefficients.

Metric results retain units and explicit availability. Inputs and comparison records retain source/mode/window metadata. Never map unavailable measurements to valid-looking sentinels or prose advice. Reference inputs must be explicit; Compare B has no automatic reference-pool meaning. Keep fixtures small, reproducible and licensed; generate analytic signals where possible. Report writes require explicit developer/user invocation.

Future standards work must document coefficient source, supported sample rates, precision, filter response and external-test tolerances. [Loudness contract](LOUDNESS_ALGORITHM_CONTRACT.md) scopes the existing experiment; the new production architecture belongs to the shared C++ design in the construction guide.

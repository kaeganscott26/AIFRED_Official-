# Development

Inspect branch, HEAD, upstream, working changes, remotes and source ownership before editing. Keep both repositories independently buildable. Do not copy dependencies or runtime implementation from an absolute sibling path. Separate construction work from DSP/GUI/model changes.

Use [architecture](ARCHITECTURE.md), [build](BUILD.md), [testing](TESTING.md), [installation](INSTALLATION.md), [distribution](DISTRIBUTION.md) and [channel ownership](COEXISTENCE.md). New documents need a clear owner; update these documents instead of adding phase logs. Git history holds superseded plans. Keep generated reports under out/<platform>/build/reports and outside canonical instructions.

CURRENT means source implements the feature; it does not certify a release. EXPERIMENTAL means code/tests exist outside the supported native runtime. PLANNED describes a design contract. UNIMPLEMENTED means no executable feature exists. Record skipped tests and untested platforms explicitly.

Preserve user settings, reference data, website assets, model files, deployment config and credentials. Examples should name configuration variables without values. System installation destinations differ from machine-specific checkout paths. User-profile editor settings and synthetic privacy-test paths are not product build configuration.

Run `python -B scripts/common/check_repository.py` for read-only canonical-path and Markdown-link checks. Generated developer reports belong below out/<platform>/build/reports.

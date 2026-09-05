# Distribution

CURRENT: scripts/windows/build.ps1 assembles the unchanged Windows product in out/windows-x64/stage, runs repository tests, checks exact bundle paths and component hashes, then promotes stage to current. Build-only operations do not install or contact a model. The release helper is developer tooling, not a Python analysis runtime.

The platform build root holds compiler output, .NET intermediates and packaging scratch. Stage contains a candidate. Current contains the one validated artifact set. A pipeline lock prevents concurrent Windows wrapper runs. A failed configure/build/test leaves current untouched. Promotion verifies the candidate and existing current, moves current to a recoverable previous slot, promotes stage, verifies it, then recycles previous. An interruption leaving previous/current requires inspection or the restricted rollback command; it must not trigger blind removal.

`manifest.json` uses schema aifred.release.v1 and records product, channel, semantic version, full Git SHA, dirty state, source diff hash, platform, architecture, host/CMake/.NET toolchain, plugin path, engine path, installer where available and SHA-256 for every component. dspProfileSchemaVersion is null until the future shared engine implements it. Hashes establish integrity, not signing, standards compliance or DAW compatibility. Public packages must not include private config, source checkout paths, user data or secrets.

```sh
python -B scripts/common/release.py verify --platform windows-x64 --location current
```

Version changes replace current instead of creating versioned build directories. The compiler keeps its incremental cache; the pipeline does not recycle gigabytes of dependencies after each build. Recycle old generated roots only after verifying they contain no unique source/user data and the new current passes validation. Reject junctions/symlinks and paths outside the exact generated owner. Use Windows Recycle Bin, macOS Trash or gio trash where available; the helper uses a recorded external quarantine when Linux Trash tooling is unavailable. Recycling does not reclaim disk space until the user empties Trash.

No source archives belong inside Git. Git history preserves removed documentation. Before a future engine replacement, create and verify an external source/binary baseline archive with commit, dependencies, tests and hashes. This pass does not replace an engine.

BUILD, INSTALL, UNINSTALL, UPDATE and ROLLBACK have separate responsibilities. See [installation](INSTALLATION.md) and [coexistence](COEXISTENCE.md). Future updaters must verify channel ownership, package integrity and host shutdown, preserve rollback, and keep user data. The plugin must never overwrite its loaded bundle. No automatic updater is implemented by this scaffolding.

macOS/Linux promotion and installation are SCAFFOLDED / NOT VALIDATED. Packaging from those platforms must pass native validation before any release claims.

The Windows wrapper holds an exclusive pipeline lock. Invoke release helpers through that wrapper; standalone concurrent staging/promotion calls are unsupported. The manifest hashes the complete non-ignored source/config working tree, including newly added files, and records dirty state. macOS currently assembles one candidate package in stage; full manifest/promotion remains SCAFFOLDED / NOT VALIDATED. Linux and Official macOS have no complete release route.

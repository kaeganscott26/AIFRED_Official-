# Distribution

## Windows release pipeline

```text
build -> tests -> stage -> manifest -> verify -> promote current
```

[build.ps1](../scripts/windows/build.ps1) and [release.py](../scripts/common/release.py) own this pipeline. `stage` is a candidate. `current` is the single verified release. Promotion verifies the candidate, verifies any existing current release, moves the old current to recoverable `previous`, promotes stage, and verifies the new current before recycling the old release.

The v2 manifest records product/channel/version, Git SHA, dirty state, normalized source-tree hash, platform/toolchain, profile schema and revisions, shared-core version, context schema, runtime channel/port, exact component paths, and SHA-256 for every file.

Official current contains:

- `Aifred.vst3`
- `AifredIntelligenceHost`
- `manifest.json`
- `.aifred-stage.json`

`release.py verify --platform windows-x64` checks inventory, exact hashes, required files, host channel ownership, and stage equality with the exact compiler VST3. Failed validation leaves the prior current release intact. Retained recovery directories block another promotion until a developer inspects them.

Generated `out`, stage/current artifacts, recovery directories, archives, and credentials stay out of Git.

## Related

- [Build](BUILD.md)
- [Installation](INSTALLATION.md)
- [Testing](TESTING.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)

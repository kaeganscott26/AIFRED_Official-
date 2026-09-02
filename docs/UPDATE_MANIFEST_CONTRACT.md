# AIFRED update foundation

The VST may check for update metadata only from a message or background thread.
Update work is forbidden on the realtime audio path.

The manifest fields are:

- `version`: semantic AIFRED product version.
- `channel`: `alpha`, `beta`, or `stable`.
- `download`: HTTPS location of an external-updater-compatible package.
- `sha256`: SHA-256 of that downloaded package.
- `minimumUpdaterVersion`: oldest updater allowed to apply it.

`update/mock-manifest.json` proves the contract only. Its placeholder URL and
digest deliberately prevent it from being mistaken for a release.

The plugin may report availability and ask for consent. It must not replace its
own loaded bundle. A separate updater must download, verify SHA-256, wait until
the DAW has exited, replace the canonical VST3 bundle, and leave the next DAW
launch to load the new version. No silent self-overwrite is permitted.

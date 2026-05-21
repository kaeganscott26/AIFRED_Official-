# Python Fixtures

Fixtures must be safe, small, non-private, and explicitly approved.

Allowed fixture sources:

- synthetic audio generated for tests
- tiny public-domain samples with documented license
- user-approved files prepared specifically for testing

Forbidden fixture sources:

- private songs
- copyrighted commercial audio
- client material
- commercial reference tracks without approval
- personal DAW project files unless intentionally approved
- files containing private metadata
- absolute local paths

Tests should generate temporary synthetic files when possible instead of storing audio fixtures in the repo.

No fixture may imply production analysis is implemented before the Python Truth Layer is approved.

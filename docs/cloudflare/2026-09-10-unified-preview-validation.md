# Unified Pages preview validation — 2026-09-10

## Deployment

- Pages project: `aifred-site`.
- Environment/branch: Preview / `official-unified-recovery`.
- Validated deployment: `20436ef4-2172-431f-ad05-fd9acb07755e`.
- URL: `https://20436ef4.aifred-site.pages.dev`.
- Source revision: `e1b98fd6efb4cc286d9ea81cb6e014ce9e1ec196`.
- Production remained deployment `b2b33ea0-e74e-46a0-a6b5-53fb5c5d4b4e`; no production route or source setting changed.

## Passed

- Pages accepted and compiled the Advanced Mode `_worker.js` bundle.
- `/`, website CSS/JS/config, `/ops`, Ops CSS/JS, `/health`, catalog, reference pool, and models returned their expected content types and successful statuses.
- Headless Edge renders showed the full styled home page and dark styled Ops login panel; the prior Markdown-fence/plain-page corruption is absent.
- Preview requests wrote minute rollups only to `aifred-ops-preview`; production `aifred-ops` remained at its baseline count during the isolation check.
- Beta installer and ZIP returned exact manifest filename, media type, byte length, ETag, release tag, and SHA-256 headers.
- Range `bytes=0-99` returned `206`, exact `Content-Range`, and 100 nonzero bytes.
- Full preview downloads produced 53,964,697-byte and 2,323,863-byte files whose computed SHA-256 values matched the release manifest.
- Bounded download details and daily/lifetime aggregate rows were written to preview D1. KV was not used as the request-event store.
- After the test traffic stopped, preview D1 stayed at nine requests and three bounded download events for more than five minutes; provider calls remained zero. Static review found no repeating website/Ops timer, and no Android chat connection call occurs on startup.
- Android Admin compiled and passed 12 unit tests. A second debug build embedded this preview origin. Windows Admin PowerShell parsed successfully; host endpoint-normalization contracts passed.

## Blocked or partial

- Preview contains `GITHUB_TOKEN` but does not contain `AIFRED_ADMIN_USERNAME`, `AIFRED_ADMIN_PASSWORD_SHA256`, or `AIFRED_ADMIN_SESSION_SECRET`. Per the recovery gate, no remote login was attempted and authenticated dashboard, exports, logout, and source-edit-to-deployment validation are blocked.
- No `AIFRED_API_TOKEN` is present in the observed preview secret names, so authenticated analysis and product chat could not be validated remotely. Models returns a valid empty list because no preview provider model is configured.
- Reference routing is healthy but preview `references_catalog` is empty; no historical KV/R2 metadata was deleted or silently imported.
- No Android device/emulator is attached, so APK install, foreground/background traffic, and in-app control-plane interaction are unverified. No desktop app UI session was run. No DAW/VST host was opened.
- Connected browser automation was unavailable; headless Edge supplied render evidence but not interactive login evidence.

These blockers prevent production promotion and the Pages Git source move. They do not invalidate the locally tested source repair or the unauthenticated preview surface.

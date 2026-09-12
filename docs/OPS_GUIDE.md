# `/ops` Operations Console

Open `/ops` on the canonical Pages site and sign in with the configured AIFRED
administrator account. The page stores the signed session in browser session
storage and sends it only as a bearer token to same-origin APIs.

Panels are Overview, Analytics, Downloads, Track Analysis, API, Logs, Inquiries,
Exports, FORGE, and Archive. Refresh is manual; tables are bounded and times
arrive as UTC ISO-8601. Operational responses are `no-store`.

Exports use `/api/v1/admin/export/site` and `/api/v1/admin/export/tracks`. The
Archive panel is informational because a Pages site cannot read local desktop
archives. `/ops` does not implement a terminal or
`/api/v1/command/run`; registered admin commands are available in Android Admin.

All surfaces use the same Pages backend. `aifred-api-staging` is not a
production `/api/*` route and should only be used for isolated smoke checks.

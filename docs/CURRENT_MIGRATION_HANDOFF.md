# Current AIFRED website/backend handoff

Updated 2026-09-12. This is an active state record, not a task list for
recreating the migration. Secret values are never recorded.

## Source and deployment authority

- Official repository: `kaeganscott26/AIFRED_Official-`, branch `main`.
- Unified source: `apps/website`; router: `apps/website/_worker.js`.
- Production target: Pages project `aifred-site`.
- Staging: `aifred-api-staging`, isolated and not routed to production.
- Pages Git source is Official. Its build output is `apps/website`; deployment
  `db7d9cf9` from commit `bba3238` is active and verified.
- No zone Worker route owns `/api/*`.

## Cloudflare state

Pages has the existing KV, R2, D1, and Analytics bindings required by the
unified backend. Staging has the same storage resources plus its existing
staging Analytics dataset, queue, and rate-limit namespaces. Existing Access
applications and secrets were preserved. The apex Pages domain is registered
but pending because the zone CNAME is missing; the current Wrangler OAuth
credential has zone read but not DNS write permission.

## Restored shared client contract

The canonical API is `https://north3rnlight3r.com/api/v1`. Browser `/ops`,
Android Admin, desktop Admin, Beta, and Official clients use the same origin and
route family. The Pages backend now exposes the Android/admin routes that were
present in the client but absent from the canonical handler: server action
registry, authenticated allowlisted commands, chat settings, provider
configuration/test, catalog/reference upload, catalog removal, and historical
sales. Existing logs, analytics, inquiry, reference, dashboard, export, and
approved-source routes remain in the same backend.

The Android Upload tab is visible again. Chat remains request-driven over HTTP;
the website WebSocket adapter remains available without adding idle polling.
The backend command surface is allowlisted and never executes arbitrary shell,
filesystem, plugin, routing, or audio mutation. Website source editing remains
limited to the approved text-file list and optimistic SHA check.

## Artifact authority

The public website download button uses only the verified Beta repository
`out/windows-x64/current` artifact (`0.3.6`, build source
`ec922b930205f7dc0accdefa733fa357df95bcf6`) stored under the manifest's
`releases/beta/v0.3.6-beta-stable/*` R2 keys. The installer is 53,930,848 bytes
with SHA-256
`d0731bfa6afdf5af02e9429bd03a847d7d06df1e549760c04fe5548bb3ae3421`; the ZIP
is 2,363,132 bytes with SHA-256
`9cbcebbefe1928bbd7f5fd533abbc3136d7fcbcd6059ec72fbb3d108305a8d36`.

The ZIP contains the VST3 and `AifredIntelligenceHost` plus distribution
configuration and README. Shared DSP is compiled into the VST3 binary; it is
not a separate runtime folder. Official alpha artifacts are not exposed. The
download handler returns unavailable instead of redirecting to a stale external
Beta artifact when R2 does not match the manifest.

## Validation boundary

`npm --prefix apps run website:check` covers source/module/assets, backend
contracts, command metadata, and repository construction. Beta current release
verification passed 17 hashed files. Deployment `db7d9cf9` served both current
R2 objects; full-content downloads matched the local Beta current files and
manifest hashes. Android requires the local SDK/JDK build and, separately,
physical-device validation. No DAW scan/load claim follows from website or
Android automation.

## Remaining external step

An authorized Cloudflare DNS administrator must add the apex CNAME to
`aifred-site.pages.dev` (the Pages project already has the pending apex custom
domain). Then verify the apex after DNS propagation. Do not delete the existing
Access applications or staging resources as part of that verification; the
deployment and Pages-hostname checks are complete.

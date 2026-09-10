# AIFRED Administration Guide

All live admin surfaces use `https://north3rnlight3r.com/api` and the protected `/api/v1/admin/*` API. Credentials and provider secrets are not embedded in `/ops` or desktop clients.

| Capability | Android | `/ops` | Windows | macOS |
| --- | --- | --- | --- | --- |
| Authenticated live status | Yes | Yes | Yes | Yes, through `/ops` WebKit |
| Analytics/downloads/logs/inquiries | Yes | Yes | Yes | Yes, through `/ops` |
| Approved website text source | Read, validate, commit | No | No | No |
| Catalog/reference/track analysis | Read-only | Yes | Yes | Yes, through `/ops` |
| Site and track exports | Yes | Yes | Yes | Yes, through `/ops` |
| User-entered admin commands | Yes | No | No | No |
| Local diagnostic registry | Android only | No | No | No |
| Local archive status/search/restore | No | Metadata boundary only | Yes | Yes |
| Manual confirmed archive prune | No | No | Yes | Yes |

## Android Admin

The Compose app has Chat, Upload, and Command tabs. It supports user-triggered chat, local provider profiles, catalog playback, bounded operational refresh, exports, and local diagnostic commands. The Command tab lists eight approved Official website text files, loads content with its Git blob SHA, validates edits, and commits through authenticated `/api/v1/admin/source/*` routes. The Worker holds the GitHub credential; the APK does not.

The mobile editor cannot delete, create, traverse directories, or upload binary website assets. It marks a successful source commit as unverified for deployment. After Pages source authority moves to Official, the operator still checks the Pages deployment before treating an edit as published. Catalog/reference media use separate controlled storage routes.

## `/ops`

`/ops` has Overview, Analytics, Downloads, Track Analysis, API, Logs, Inquiries, Exports, FORGE and Archive panels. The shell is public static HTML but all operational data and exports require backend authentication. Responses are `no-store`; the page is `noindex`. It has no terminal parser.

## Desktop Admin

Windows preserves WinForms. macOS is an AppKit/WebKit shell. Live data comes from the same API or embedded `/ops`; archive controls call `tools/aifred-archive.mjs`. Offline mode covers local archives, never production administration. No direct Cloudflare token is required.

For every Android terminal command, use [Administrator Command Reference](ADMIN_COMMAND_REFERENCE.md). Archive CLI syntax is in [Archive Guide](ARCHIVE_GUIDE.md).

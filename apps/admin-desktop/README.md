# AIFRED Desktop Admin

Desktop Admin combines the authenticated production `/ops` control surface with local AIFRED cold storage. It never contains Cloudflare or admin credentials.

Windows uses `apps/admin-android/tools/windows-admin/AIFRED-Admin-Desktop.ps1`. macOS source is in `macos/`; build with `./apps/admin-desktop/macos/build.sh` or build and install to `~/Applications` with `./apps/admin-desktop/macos/install.sh`. Generated application bundles stay under `out/macos-arm64/build/admin/`.

Remove only the installed macOS application with `./apps/admin-desktop/macos/uninstall.sh`. Archive data and local settings are preserved.

Set `AIFRED_REPO_ROOT` when launching an installed desktop client from outside the repository. `AIFRED_API_BASE_URL` may select a development origin; production defaults to `https://north3rnlight3r.com`. Stored legacy forms ending in `/api`, `/api/v1`, or `/v1` are normalized for compatibility.

Both clients delegate archive operations to `node tools/aifred-archive.mjs`. Search and restore are bounded to 100 records and 1 MiB by default. Permanent archive pruning is deliberately not automated.

The desktop clients do not implement Android's text command parser. Windows presents WinForms buttons; macOS embeds authenticated production `/ops` in WebKit and adds native archive controls. Exact archive ID and interactive confirmation are required to prune.

Windows requires PowerShell/.NET WinForms and Node.js. macOS requires Swift, AppKit/WebKit and Node.js. See [Admin Guide](../../docs/ADMIN_GUIDE.md) and [Archive Guide](../../docs/ARCHIVE_GUIDE.md).

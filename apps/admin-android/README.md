# AIFRED Admin | Private Android Management Console

AIFRED Android Admin is owner-only operational software for the North3rnLight3r
website/backend and catalog. Its production base is
`https://north3rnlight3r.com/api`; it appends `/v1/*` and `/v1/admin/*` from
`BuildConfig.AIFRED_BASE_URL`. Override the base only for development with the
Gradle property `AIFRED_BASE_URL` or ignored `local.properties` key
`aifredBaseUrl`.

The website, Beta and Official clients, Android Admin, desktop Admin, and `/ops`
share the same Pages backend. The Android app does not call the staging Worker
by default.

## Responsibilities

- authenticated owner access, website chat, model selection, and catalog playback;
- catalog audio/metadata upload and licensed-reference upload through controlled R2 routes;
- server action registry and authenticated allowlisted backend commands;
- analytics, downloads, inquiries, activity/logs, references, sales, status, dashboard, and exports;
- provider configuration/test and bounded chat-settings load/save;
- approved Official website text reads, validation, and optimistic source commits;
- separate local-only, non-root Android/Termux diagnostics.

The Upload tab and the restored Command controls use the same `/api/v1` routes
as `/ops`. The phone never executes arbitrary backend shell input. Website
source controls accept only the existing eight approved text files, require a
fresh Git blob SHA, and cannot create/delete/traverse arbitrary paths or upload
binary website assets. The server, not the APK, holds `GITHUB_TOKEN`.

## Technical state

- App version `2.3.0`, version code `243`
- `compileSdk = 35`, `targetSdk = 35`, minimum SDK `29`
- JVM target `17`, Jetpack Compose, OkHttp, Kotlin coroutines
- request-driven HTTP chat; WebSocket is retained for the website adapter only
- local AifredIntelligenceHost remains separate at `127.0.0.1:8788` for Official

The client uses the OpenAI-compatible `/v1/models` and
`/v1/chat/completions` contract. It can use the website route, local Ollama, or
OpenAI according to the selected phone profile. A provider is interpretation
infrastructure; it does not replace AIFRED measurements or FilteredMixContext.

## Build and install

Windows PowerShell:

```powershell
cd apps/admin-android
.\gradlew.bat test assembleDebug
```

Install the generated debug APK locally with ADB:

```powershell
$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
& $adb install -r app\build\outputs\apk\debug\app-debug.apk
```

The release build currently uses debug signing and is private owner tooling;
do not publish it as a public store artifact or GitHub release. Report build,
install, and physical-device/DAW evidence separately.

## Security and traffic

Android cleartext transport is enabled only for local/private provider use; the
production website/API requires HTTPS. Admin sessions are bounded and revoked
server-side. Secrets, passwords, tokens, and private local configuration are
never committed. Chat and provider probes run only from explicit user actions;
there is no periodic Cloudflare API polling from the plugin or app.

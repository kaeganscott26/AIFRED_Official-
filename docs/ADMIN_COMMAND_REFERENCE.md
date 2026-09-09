# AIFRED Administrator Command Reference

This reference is generated and verified against `config/admin-commands.json`, the current backend registry, and Android's generated local registry. Do not hand-edit it; run `node tools/generate-admin-command-reference.mjs`.

Only Android Admin currently has a user-entered command interface. `/ops`, Windows Desktop Admin, and macOS Desktop Admin expose named buttons/panels, not this command parser.

## Quick reference

| Command | Android | `/ops` | Windows | macOS | Purpose |
| --- | --- | --- | --- | --- | --- |
| `action:local:pwd` | Yes | No | No | No | Show the app shell working directory |
| `action:local:files` | Yes | No | No | No | List files in the app shell working directory |
| `action:local:storage` | Yes | No | No | No | Show filesystem usage |
| `action:local:usage` | Yes | No | No | No | Show the current directory size |
| `action:local:identity` | Yes | No | No | No | Show the app-shell identity |
| `action:local:system` | Yes | No | No | No | Show kernel and system details |
| `action:local:processes` | Yes | No | No | No | List processes visible to the app shell |
| `action:local:network` | Yes | No | No | No | Show network addresses and routes |
| `action:local:environment` | Yes | No | No | No | List the local process environment |
| `action:termux:packages` | Yes | No | No | No | List installed Termux packages when available |
| `action:termux:info` | Yes | No | No | No | Show Termux environment information when available |
| `action:android:version` | Yes | No | No | No | Show the Android OS version |
| `action:android:packages` | Yes | No | No | No | List third-party Android packages visible to the app |
| `action:android:logs` | Yes | No | No | No | Show recent logs accessible to the app |
| `action:site:health` | Yes | No | No | No | Check production API health from the device |

## Backend commands

Backend commands require a valid online admin session. The backend also accepts the explicit action alias `action:<command-id>`, which is what Android action buttons submit. Commands take no arguments and are case-sensitive after trimming. Unsupported commands return HTTP 400 / exit code 2.

## Android local registered actions

These registered actions execute bounded, non-root diagnostic shell strings on the Android device. Enter the complete `action:...` value shown. Availability of Android/Termux utilities depends on the device environment. They do not call the production command endpoint.

### local:pwd

Exact Android syntax:

```text
action:local:pwd
```

- Purpose: Show the app shell working directory.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `pwd`.

### local:files

Exact Android syntax:

```text
action:local:files
```

- Purpose: List files in the app shell working directory.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `ls -la`.

### local:storage

Exact Android syntax:

```text
action:local:storage
```

- Purpose: Show filesystem usage.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `df -h`.

### local:usage

Exact Android syntax:

```text
action:local:usage
```

- Purpose: Show the current directory size.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `du -sh .`.

### local:identity

Exact Android syntax:

```text
action:local:identity
```

- Purpose: Show the app-shell identity.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `id`.

### local:system

Exact Android syntax:

```text
action:local:system
```

- Purpose: Show kernel and system details.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `uname -a`.

### local:processes

Exact Android syntax:

```text
action:local:processes
```

- Purpose: List processes visible to the app shell.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `ps -A`.

### local:network

Exact Android syntax:

```text
action:local:network
```

- Purpose: Show network addresses and routes.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `ip addr; ip route`.

### local:environment

Exact Android syntax:

```text
action:local:environment
```

- Purpose: List the local process environment.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `printenv | sort`.

### termux:packages

Exact Android syntax:

```text
action:termux:packages
```

- Purpose: List installed Termux packages when available.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `if command -v pkg >/dev/null 2>&1; then pkg list-installed; else echo 'Termux pkg is not available'; fi`.

### termux:info

Exact Android syntax:

```text
action:termux:info
```

- Purpose: Show Termux environment information when available.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `if command -v termux-info >/dev/null 2>&1; then termux-info; else echo 'termux-info is not available'; fi`.

### android:version

Exact Android syntax:

```text
action:android:version
```

- Purpose: Show the Android OS version.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `getprop ro.build.version.release`.

### android:packages

Exact Android syntax:

```text
action:android:packages
```

- Purpose: List third-party Android packages visible to the app.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `pm list packages -3`.

### android:logs

Exact Android syntax:

```text
action:android:logs
```

- Purpose: Show recent logs accessible to the app.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `logcat -d -t 100`.

### site:health

Exact Android syntax:

```text
action:site:health
```

- Purpose: Check production API health from the device.
- Available in: Android Admin command terminal only.
- Arguments/options: None.
- Authentication: Local/offline owner session; no Cloudflare admin session is used.
- Output: Device shell stdout/stderr.
- Executed local diagnostic: `curl -fsS https://north3rnlight3r.com/api/health`.

## Non-command controls

`/ops` and both desktop clients use controls rather than a text command parser. Desktop archive operations use the separate local CLI documented in [Archive Guide](ARCHIVE_GUIDE.md); those CLI invocations are developer/operator shell commands, not AIFRED admin-terminal commands.

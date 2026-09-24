#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
. "$REPO_ROOT/scripts/macos/common.sh"

require_macos
require_tools swiftc shasum
"$SCRIPT_DIR/build.sh" >/dev/null

APP_SOURCE="$REPO_ROOT/out/macos-arm64/build/admin/AIFRED Admin.app"
APP_PARENT="$HOME/Applications"
install_owned_tree "$APP_SOURCE" "$APP_PARENT" "AIFRED Admin.app"
echo "Installed $APP_PARENT/AIFRED Admin.app"

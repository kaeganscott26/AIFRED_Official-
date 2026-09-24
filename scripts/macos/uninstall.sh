#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common.sh"
require_macos

launchctl bootout "gui/$(id -u)/$HOST_LABEL" 2>/dev/null || true
rm -f "$LAUNCH_AGENT"
remove_owned_tree "$PLUGIN_TARGET" "$PLUGIN_PARENT"
remove_owned_tree "$HOST_TARGET" "$DATA_PARENT"
rmdir "$PLUGIN_PARENT" 2>/dev/null || true
rmdir "$DATA_PARENT" 2>/dev/null || true
echo "AIFRED Official binaries removed. User settings were retained."

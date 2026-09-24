#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
. "$REPO_ROOT/scripts/macos/common.sh"

require_macos
remove_owned_tree "$HOME/Applications/AIFRED Admin.app" "$HOME/Applications"
echo "Removed $HOME/Applications/AIFRED Admin.app"

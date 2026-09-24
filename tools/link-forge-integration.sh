#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/integrations/forge"
DESTINATION="${1:-}"
[[ -n "$DESTINATION" ]] || { echo "Usage: $0 /path/to/FORGE/integrations/aifred" >&2; exit 2; }
PARENT="$(dirname "$DESTINATION")"
mkdir -p "$PARENT"
if [[ -e "$DESTINATION" || -L "$DESTINATION" ]]; then
  [[ -L "$DESTINATION" && "$(cd "$PARENT" && realpath "$DESTINATION")" == "$SOURCE" ]] && exit 0
  echo "Refusing to replace an existing unrelated destination: $DESTINATION" >&2
  exit 1
fi
ln -s "$SOURCE" "$DESTINATION"
echo "Linked $DESTINATION -> $SOURCE"

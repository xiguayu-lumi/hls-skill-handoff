#!/usr/bin/env bash
set -euo pipefail
DEST="${1:-.codex/skills}"
FORCE="${2:-}"
HERE="$(cd "$(dirname "$0")" && pwd)"
NAME="$(basename "$HERE")"
TARGET="$DEST/$NAME"
mkdir -p "$DEST"
if [ -e "$TARGET" ] && [ "$FORCE" != "--force" ]; then
  echo "Target already exists: $TARGET. Re-run with --force only when replacement is intended." >&2
  exit 1
fi
if [ -e "$TARGET" ]; then
  rm -rf -- "$TARGET"
fi
cp -R "$HERE" "$TARGET"
echo "Installed $NAME to $TARGET"
echo "Restart Codex only if the skill does not appear automatically."

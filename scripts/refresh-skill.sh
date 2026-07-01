#!/usr/bin/env bash
# Refresh the vendored composio-cli skill from a Composio CLI GitHub release.
#
# The skill is generated in ComposioHQ/composio and published as the
# `composio-skill.zip` asset on `@composio/cli@*` releases. This script pulls a
# pinned release, extracts the `composio-cli` skill directory, and vendors it
# into plugins/composio/skills/composio-cli.
#
# Usage:
#   scripts/refresh-skill.sh                      # use the pinned default tag
#   scripts/refresh-skill.sh '@composio/cli@0.2.31'   # use a specific tag
#
# Requires: gh (authenticated), unzip.

set -euo pipefail

# Keep in sync with tests/config.py PINNED_SKILL_RELEASE.
DEFAULT_TAG='@composio/cli@0.2.31'
TAG="${1:-$DEFAULT_TAG}"
REPO="ComposioHQ/composio"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$REPO_ROOT/plugins/composio/skills/composio-cli"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "Downloading composio-skill.zip from $REPO @ $TAG ..."
gh release download "$TAG" -R "$REPO" -p 'composio-skill.zip' -D "$tmp" --clobber

echo "Extracting ..."
unzip -o -q "$tmp/composio-skill.zip" -d "$tmp/extracted"

SRC="$tmp/extracted/composio-cli"
if [ ! -f "$SRC/SKILL.md" ]; then
  echo "ERROR: composio-cli/SKILL.md not found in the release asset." >&2
  exit 1
fi

echo "Vendoring into $DEST ..."
rm -rf "$DEST"
mkdir -p "$DEST"
cp -R "$SRC/." "$DEST/"

echo "Done. Vendored composio-cli skill from $TAG."
echo "Remember to update PINNED_SKILL_RELEASE in tests/config.py if the tag changed."

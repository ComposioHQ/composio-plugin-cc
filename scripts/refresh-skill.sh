#!/usr/bin/env bash
# SINGLE-SOURCE BUILD STEP: regenerates the vendored composio-cli skill from the
# pinned STABLE Composio CLI release so the skill is never hand-maintained.
#
# The skill is generated in ComposioHQ/composio and published as the
# `composio-skill.zip` asset on `@composio/cli@*` releases. This script pulls a
# pinned STABLE (non-beta) release, extracts the `composio-cli` skill, and
# vendors ONLY the trimmed fileset we ship into
# plugins/composio/skills/composio-cli:
#   SKILL.md, references/composio-dev.md, references/troubleshooting.md
# (agents/ and references/power-user-examples.md are intentionally dropped).
#
# Usage:
#   scripts/refresh-skill.sh                          # use the pinned default tag
#   scripts/refresh-skill.sh '@composio/cli@0.2.31'   # use a specific STABLE tag
#
# Requires: gh (authenticated), unzip.

set -euo pipefail

# Pinned STABLE release. Keep in sync with tests/config.py PINNED_SKILL_RELEASE
# and .github/workflows/ci.yml.
DEFAULT_TAG='@composio/cli@0.2.31'
TAG="${1:-$DEFAULT_TAG}"
REPO="ComposioHQ/composio"

case "$TAG" in
  *beta*|*alpha*|*rc*|*next*)
    echo "ERROR: '$TAG' looks like a pre-release. Vendor from a STABLE tag only." >&2
    exit 1 ;;
esac

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

echo "Vendoring trimmed fileset into $DEST ..."
rm -rf "$DEST"
mkdir -p "$DEST/references"
cp "$SRC/SKILL.md" "$DEST/SKILL.md"
cp "$SRC/references/composio-dev.md" "$DEST/references/composio-dev.md"
cp "$SRC/references/troubleshooting.md" "$DEST/references/troubleshooting.md"

echo "Done. Vendored trimmed composio-cli skill from $TAG."
echo "If you changed the tag, update PINNED_SKILL_RELEASE in tests/config.py and the tag in .github/workflows/ci.yml."

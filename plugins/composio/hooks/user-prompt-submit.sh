#!/usr/bin/env bash
# UserPromptSubmit hook for the Composio plugin.
#
# When a prompt NAMES a known toolkit, inject a single-line nudge pointing at
# Composio's meta-search (search -> execute). No match -> no output.
#
# The match set is the top-50 toolkits, READ from the cache the SessionStart hook
# warms (via `composio dev toolkits list --limit 50`) — nothing else. No generic
# verbs (they collide with coding vocabulary and over-fire), no static fallback,
# no aliases. If the cache is cold (CLI absent/offline, or the session just
# started) there is no match and the hook is silent.
#
# Pure bash, no network, no composio call on this hot path. Always exits 0.

set -u

CACHE="${TMPDIR:-/tmp}/composio-plugin-toolkits.cache"

# No cache -> nothing to match against -> stay silent.
[ -f "$CACHE" ] && [ -s "$CACHE" ] || exit 0

payload="$(cat)"

# --- extract the prompt ----------------------------------------------------
if command -v jq >/dev/null 2>&1; then
  prompt="$(printf '%s' "$payload" | jq -r '.prompt // empty' 2>/dev/null)"
else
  prompt=""
fi
# jq missing or no .prompt -> match against the whole raw payload.
[ -n "$prompt" ] || prompt="$payload"

# --- normalize: lowercase, non-alnum -> space, pad with spaces -------------
norm="$(printf '%s' "$prompt" \
  | tr '[:upper:]' '[:lower:]' \
  | tr -c 'a-z0-9' ' ')"
norm=" $norm "

# --- match against the top-50 toolkit cache (each line = slug or display name,
#     possibly multi-word), as a space-padded substring so "google calendar"
#     matches too.
matched=0
while IFS= read -r kw; do
  [ -n "$kw" ] || continue
  case "$norm" in
    *" $kw "*) matched=1; break ;;
  esac
done <"$CACHE"

[ "$matched" -eq 1 ] || exit 0

# --- emit one-line nudge as additionalContext ------------------------------
line="You mentioned an app Composio can act on. Resolve the tool just-in-time: \`composio search \"<task>\"\` then \`composio execute\` (managed auth)."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$line" \
    '{hookSpecificOutput:{hookEventName:"UserPromptSubmit",additionalContext:$c}}'
else
  esc="$(printf '%s' "$line" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')"
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$esc"
fi

exit 0

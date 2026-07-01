#!/usr/bin/env bash
# UserPromptSubmit hook for the Composio plugin.
#
# Fast, local, non-blocking. Reads the user's prompt from stdin JSON and matches
# app/toolkit mentions against the CLI-sourced cache that SessionStart maintains
# (${TMPDIR:-/tmp}/composio-plugin-toolkits.cache). On a match it injects a
# minimal pointer to the composio:composio-cli skill and `composio search`.
# No network here; always exits 0 so it can never block a prompt.

set -u

cache="${TMPDIR:-/tmp}/composio-plugin-toolkits.cache"

# --- read stdin (the hook payload) -----------------------------------------
payload="$(cat 2>/dev/null || true)"
[ -z "$payload" ] && exit 0

# --- extract the raw prompt -------------------------------------------------
prompt=""
if command -v jq >/dev/null 2>&1; then
  prompt="$(printf '%s' "$payload" | jq -r '.prompt // empty' 2>/dev/null)"
fi
[ -z "$prompt" ] && prompt="$payload"

# --- normalize: lowercase, non-alphanumerics -> spaces, pad with spaces -----
# Gives us free word-boundary matching (leading/trailing space on both sides).
norm=" $(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9 ' ' ') "

matched=0

if [ -s "$cache" ]; then
  # Match the prompt against the CLI-sourced toolkit names/slugs. Pad each
  # cached entry with spaces and fixed-string grep for word-boundary matching.
  if printf '%s' "$norm" | grep -qFf <(sed -e 's/.*/ & /' "$cache") 2>/dev/null; then
    matched=1
  fi
else
  # Cache absent (SessionStart hasn't run / CLI unavailable): fall back to a
  # MINIMAL generic intent-signal set only.
  for kw in connect integrate integration oauth authenticate; do
    case "$norm" in *" $kw "*) matched=1; break;; esac
  done
fi

[ "$matched" -eq 0 ] && exit 0

# --- matched: inject a minimal pointer (no workflow restated here) ----------
ctx="The user mentioned an app Composio can act on. Composio connects 1000+ apps with managed OAuth (no API keys). Use the 'composio:composio-cli' skill and 'composio search \"<task>\"' to find and run the right tool; prefer the composio CLI over hand-rolled API calls for these apps."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$ctx" \
    '{hookSpecificOutput:{hookEventName:"UserPromptSubmit",additionalContext:$c}}'
else
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$ctx"
fi

exit 0

#!/usr/bin/env bash
# UserPromptSubmit hook for the Composio plugin.
#
# When a prompt NAMES a known external app/toolkit, inject a single-line nudge
# pointing at Composio's meta-search (search -> execute). No match -> no output.
#
# Matches ONLY named toolkits (high precision) — NOT generic action verbs, which
# collide with everyday coding vocabulary (issue/post/sync/connect/email/...) and
# over-fire on ~60% of normal prompts. The general "use Composio for external
# stuff" reminder lives in the SessionStart hook; this per-prompt hook fires only
# on an explicit app mention.
#
# Pure bash, no network, no composio call on this hot path. The toolkit match set
# is READ from a cache warmed by the SessionStart hook (plus a small static
# fallback for when the cache is cold/offline). Always exits 0.

set -u

CACHE="${TMPDIR:-/tmp}/composio-plugin-toolkits.cache"

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

matched=0

# 1) Common app aliases/nicknames not always captured by a toolkit slug.
#    Kept short and collision-safe (no bare single letters like "x").
for kw in twitter tweet gcal gsheet gsheets gdrive; do
  case "$norm" in
    *" $kw "*) matched=1; break ;;
  esac
done

# 2) Toolkit tokens — from the SessionStart cache when warm (each line is one
#    token/phrase: slug or display name, possibly multi-word), else a small
#    static fallback of popular slugs + phrases. Each entry is matched as a
#    space-padded substring so multi-word names ("google calendar") work too.
if [ "$matched" -eq 0 ]; then
  if [ -f "$CACHE" ] && [ -s "$CACHE" ]; then
    while IFS= read -r kw; do
      [ -n "$kw" ] || continue
      case "$norm" in
        *" $kw "*) matched=1; break ;;
      esac
    done <"$CACHE"
  else
    for kw in gmail github slack notion linear googlecalendar "google calendar" \
              googlesheets "google sheets" googledrive "google drive" jira \
              hubspot salesforce discord telegram stripe airtable asana trello \
              zoom calendly figma sentry twitter; do
      case "$norm" in
        *" $kw "*) matched=1; break ;;
      esac
    done
  fi
fi

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

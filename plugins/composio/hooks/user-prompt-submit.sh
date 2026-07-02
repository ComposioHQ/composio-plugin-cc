#!/usr/bin/env bash
# UserPromptSubmit hook for the Composio plugin.
#
# When a prompt looks like it involves an external app or an action-intent verb,
# inject a single-line nudge pointing at Composio's meta-search (search -> execute).
# No match -> no output.
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

# --- action-intent verbs (static, small, stable — NOT app names) -----------
verbs="connect integrate integration oauth authenticate auth send email message schedule calendar reminder post fetch sync notify notification upload download ticket issue toolkit composio"

matched=0

# 1) Action-intent verbs — always checked (single tokens).
for kw in $verbs; do
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
              zoom calendly figma sentry; do
      case "$norm" in
        *" $kw "*) matched=1; break ;;
      esac
    done
  fi
fi

[ "$matched" -eq 1 ] || exit 0

# --- emit one-line nudge as additionalContext ------------------------------
line="This may involve an external app or action — Composio can do it. Resolve the tool just-in-time: \`composio search \"<task>\"\` then \`composio execute\` (managed auth)."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$line" \
    '{hookSpecificOutput:{hookEventName:"UserPromptSubmit",additionalContext:$c}}'
else
  esc="$(printf '%s' "$line" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')"
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$esc"
fi

exit 0

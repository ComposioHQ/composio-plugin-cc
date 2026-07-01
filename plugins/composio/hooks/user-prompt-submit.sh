#!/usr/bin/env bash
# UserPromptSubmit hook for the Composio plugin.
#
# Fast, local, non-blocking. Reads the user's prompt from stdin JSON, does a
# pure-bash keyword match for app/toolkit/integration mentions, and — only on a
# match — injects a short reminder that Composio can perform the action, plus the
# search -> execute -> link workflow. No network on the non-matching hot path.
# Always exits 0 so it can never block a prompt.

set -u

# --- read stdin (the hook payload) -----------------------------------------
payload="$(cat 2>/dev/null || true)"
[ -z "$payload" ] && exit 0

# --- extract the raw prompt -------------------------------------------------
# Prefer a real JSON parser; fall back to the whole payload for matching.
prompt=""
if command -v jq >/dev/null 2>&1; then
  prompt="$(printf '%s' "$payload" | jq -r '.prompt // empty' 2>/dev/null)"
fi
[ -z "$prompt" ] && prompt="$payload"

# --- normalize: lowercase, non-alphanumerics -> spaces, pad with spaces -----
# Gives us free word-boundary matching via glob patterns below.
norm=" $(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9 ' ' ') "

matched=0

# App / toolkit names (substring-safe once space-padded).
for kw in slack github gitlab bitbucket gmail outlook notion linear jira asana \
          trello clickup monday hubspot salesforce zendesk intercom discord \
          telegram whatsapp twilio sendgrid stripe shopify airtable dropbox box \
          figma confluence calendly pagerduty datadog sentry vercel supabase \
          quickbooks reddit youtube twitter zoom composio; do
  case "$norm" in *" $kw "*) matched=1; break;; esac
done

# Multi-word app names + intent phrases.
if [ "$matched" -eq 0 ]; then
  for kw in "google calendar" "google drive" "google sheets" "google docs" "gcal" \
            "microsoft teams" "connect" "integration" "integrate" "oauth" \
            "authenticate" "send an email" "send email" "post to" "create an issue" \
            "create a ticket" "create issue" "toolkit"; do
    case "$norm" in *" $kw "*) matched=1; break;; esac
  done
fi

[ "$matched" -eq 0 ] && exit 0

# --- matched: build the login-status hint (bounded, best-effort) ------------
login_hint="If a toolkit is not connected yet, run 'composio link <toolkit>' (managed OAuth)."
if command -v composio >/dev/null 2>&1; then
  # Bounded whoami so a hung/slow CLI can never delay the prompt.
  ( composio whoami >/dev/null 2>&1 ) & pid=$!
  ( sleep 2; kill -TERM "$pid" 2>/dev/null ) & watcher=$!
  if wait "$pid" 2>/dev/null; then
    login_hint="You appear to be signed in to Composio. If a toolkit is not connected, run 'composio link <toolkit>'."
  else
    login_hint="You may not be signed in. Run 'composio login', then 'composio link <toolkit>' for the app."
  fi
  kill -TERM "$watcher" 2>/dev/null
  wait "$watcher" 2>/dev/null
else
  login_hint="The composio CLI is not installed. Install it with 'curl -fsSL https://composio.dev/install | bash', then 'composio login'."
fi

# --- emit injected context (JSON; additionalContext uses \n line breaks) ----
ctx="Composio can act on the app(s) mentioned above. It connects 1000+ apps (Slack, GitHub, Gmail, Notion, Linear, and more) with managed auth.\nWorkflow: 1) 'composio search \"<task>\"' to find a tool slug (skip if you know it). 2) 'composio execute <SLUG> --get-schema' to inspect inputs, or add '--dry-run' to preview. 3) 'composio execute <SLUG> -d <json>' to run it. 4) On a connection error, 'composio link <toolkit>' and retry.\n$login_hint\nSee the 'composio:composio-cli' skill for full usage. Prefer the composio CLI over hand-rolled API calls for these apps."

# JSON-escape via jq when available; otherwise the text is already safe
# (only \n escapes, no raw quotes/backslashes outside the \" pairs above).
if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$(printf '%b' "$ctx")" \
    '{hookSpecificOutput:{hookEventName:"UserPromptSubmit",additionalContext:$c}}'
else
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$ctx"
fi

exit 0

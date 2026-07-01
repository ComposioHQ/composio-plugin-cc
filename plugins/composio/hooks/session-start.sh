#!/usr/bin/env bash
# SessionStart hook for the Composio plugin.
#
# Emits ONE concise, brand-aligned standing note as injected context: it points
# the agent at Composio's meta-search model (search -> execute) for any task that
# touches an external app, plus a single auth-status line.
#
# Fast, bounded, and non-blocking. Tolerates the CLI being missing, offline, or
# not-signed-in. Always exits 0.

set -u
cat >/dev/null 2>&1 || true   # drain stdin payload; we don't need it

# --- auth-status line ------------------------------------------------------
if ! command -v composio >/dev/null 2>&1; then
  auth="Install the CLI: curl -fsSL https://composio.dev/install | bash, then composio login."
else
  # Bounded whoami so a slow CLI can never stall session start. Sign-in is
  # decided by the EXIT CODE alone (0 = signed in) — never by stdout contents,
  # which vary across CLI versions and can be empty even when authenticated.
  signed_in=1
  ( composio whoami >/dev/null 2>&1 ) & pid=$!
  ( sleep 3; kill -TERM "$pid" 2>/dev/null ) & watcher=$!
  if wait "$pid" 2>/dev/null; then
    signed_in=0
  fi
  kill -TERM "$watcher" 2>/dev/null; wait "$watcher" 2>/dev/null
  if [ "$signed_in" -eq 0 ]; then
    auth="You're signed in to Composio."
  else
    auth="Run \`composio login\` to connect."
  fi
fi

# --- standing note (meta search) -------------------------------------------
line="Composio is available in this session. For any task involving an external app or service (email, calendar, GitHub, Slack, CRMs, docs — 1,000+ apps), resolve the tool just-in-time with \`composio search \"<task>\"\`, then run it with \`composio execute\`. Auth is fully managed. ${auth} See the composio:composio-cli skill for full usage."

# --- emit injected context -------------------------------------------------
if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$line" \
    '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
else
  # Escape backslashes and double quotes for safe JSON embedding.
  esc="$(printf '%s' "$line" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')"
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$esc"
fi

exit 0

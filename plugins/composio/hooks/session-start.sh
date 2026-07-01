#!/usr/bin/env bash
# SessionStart hook for the Composio plugin.
#
# Emits ONE concise availability + auth-status line as injected context.
# Tolerates the CLI being missing or not-logged-in. Always exits 0.

set -u
cat >/dev/null 2>&1 || true   # drain stdin payload; we don't need it

tmp="${TMPDIR:-/tmp}/composio-whoami.$$"

if ! command -v composio >/dev/null 2>&1; then
  line="Composio plugin loaded, but the 'composio' CLI is not installed. Install: 'curl -fsSL https://composio.dev/install | bash', then 'composio login'. Composio connects 1000+ apps (Slack, GitHub, Gmail, Notion, Linear, ...) with managed auth."
else
  # Bounded whoami so a slow CLI cannot stall session start.
  who=""
  ( composio whoami >"$tmp" 2>/dev/null ) & pid=$!
  ( sleep 3; kill -TERM "$pid" 2>/dev/null ) & watcher=$!
  if wait "$pid" 2>/dev/null; then
    who="$(head -c 200 "$tmp" 2>/dev/null | tr '\n' ' ')"
  fi
  kill -TERM "$watcher" 2>/dev/null; wait "$watcher" 2>/dev/null
  rm -f "$tmp" 2>/dev/null
  if [ -n "$who" ]; then
    line="Composio CLI is available and you are signed in. Use it to act on 1000+ apps (search -> execute -> link). See the 'composio:composio-cli' skill."
  else
    line="Composio CLI is available but you may not be signed in. Run 'composio login' to connect apps, then use search -> execute -> link. See the 'composio:composio-cli' skill."
  fi
fi

if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$line" \
    '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
else
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$line"
fi

exit 0

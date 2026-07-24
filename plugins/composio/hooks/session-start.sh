#!/usr/bin/env bash
# Inject Composio guidance and auth status, and refresh the prompt hook's cache.

set -u
cat >/dev/null 2>&1 || true

CACHE="${TMPDIR:-/tmp}/composio-plugin-toolkits.cache"

cache_pid=""
if command -v composio >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  (
    tmp="$(mktemp "${CACHE}.XXXXXX" 2>/dev/null)" || exit 0
    ( composio dev toolkits list --limit 50 2>/dev/null \
        | jq -r '.[] | .slug, .name' \
        | tr '[:upper:]' '[:lower:]' >"$tmp" 2>/dev/null ) &
    fpid=$!
    if wait "$fpid" 2>/dev/null && [ -s "$tmp" ]; then
      mv -f "$tmp" "$CACHE" 2>/dev/null || rm -f "$tmp" 2>/dev/null
    else
      rm -f "$tmp" 2>/dev/null
    fi
  ) &
  cache_pid=$!
fi

if ! command -v composio >/dev/null 2>&1; then
  auth="Install the CLI: curl -fsSL https://composio.dev/install | bash, then composio login."
else
  auth="Run \`composio login\` to connect."
  # CLI 0.2.31 exits 0 with empty output when logged out.
  if whoami_output="$(composio whoami 2>&1)" \
      && [ -n "$(printf '%s' "$whoami_output" | tr -d '[:space:]')" ] \
      && ! printf '%s' "$whoami_output" | grep -Eiq \
        '"authenticated"[[:space:]]*:[[:space:]]*false|not[[:space:]-]+logged[[:space:]-]+in'; then
    auth="You're signed in to Composio."
  fi

  # Upgrade nudge: read the CLI's own 24h-throttled release cache — a local
  # file only, never the network. Nudge only for a plain X.Y.Z install that is
  # strictly older than a plain X.Y.Z latestVersion (the anchored closing quote
  # rejects prereleases instead of truncating them); anything missing or
  # malformed degrades to silence.
  update_cache="${HOME:-}/.composio/update-check.json"
  if [ -f "$update_cache" ]; then
    latest="$(sed -n 's/.*"latestVersion"[[:space:]]*:[[:space:]]*"\([0-9]\{1,\}\.[0-9]\{1,\}\.[0-9]\{1,\}\)".*/\1/p' "$update_cache" 2>/dev/null | head -n 1)"
    installed="$(composio version 2>/dev/null | tail -n 1 | tr -d '[:space:]')"
    if [ -n "$latest" ] && [ "$installed" != "$latest" ] \
        && printf '%s' "$installed" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' \
        && [ "$(printf '%s\n%s\n' "$installed" "$latest" \
              | sort -t. -k1,1n -k2,2n -k3,3n | head -n 1)" = "$installed" ]; then
      auth="${auth} A newer Composio CLI (${latest}) is available — run \`composio upgrade\`."
    fi
  fi
fi

[ -n "$cache_pid" ] && wait "$cache_pid" 2>/dev/null

line="Composio is available in this session. For any task involving an external app or service (email, calendar, GitHub, Slack, CRMs, docs — 1,000+ apps), resolve the tool just-in-time with \`composio search \"<task>\"\`, then run it with \`composio execute\`. Auth is fully managed. ${auth} Run \`composio --help\` for full usage; \`composio login\` also installs the composio-cli skill with detailed guidance."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$line" \
    '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
else
  esc="$(printf '%s' "$line" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')"
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$esc"
fi

exit 0

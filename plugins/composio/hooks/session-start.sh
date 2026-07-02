#!/usr/bin/env bash
# SessionStart hook for the Composio plugin.
#
# Emits ONE concise, brand-aligned standing note as injected context: it points
# the agent at Composio's meta-search model (search -> execute) for any task that
# touches an external app, plus a single auth-status line.
#
# It also warms a top-50 toolkit cache (popularity-ranked, sourced from the CLI)
# that the UserPromptSubmit hook reads on its hot path — so per-prompt matching
# never has to touch the network or shell out to composio.
#
# Fast, bounded, and non-blocking. Tolerates the CLI being missing, offline, or
# not-signed-in. Always exits 0.

set -u
cat >/dev/null 2>&1 || true   # drain stdin payload; we don't need it

# Shared toolkit-cache path (also read by user-prompt-submit.sh). One line per
# lowercased token (slug + display name), popularity-ranked by the CLI.
CACHE="${TMPDIR:-/tmp}/composio-plugin-toolkits.cache"

# --- warm the top-50 toolkit cache (background, bounded, non-fatal) ---------
# Started early so its latency overlaps with the whoami probe below; total added
# session-start latency stays ~max(whoami, fetch), not the sum. Requires both the
# CLI and jq; on any failure/timeout we leave any existing cache untouched.
cache_pid=""
if command -v composio >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  (
    tmp="$(mktemp "${CACHE}.XXXXXX" 2>/dev/null)" || exit 0
    # `dev toolkits list` default order IS popularity. Extract slug + name,
    # lowercased, one token per line.
    ( composio dev toolkits list --limit 50 2>/dev/null \
        | jq -r '.[] | .slug, .name' \
        | tr '[:upper:]' '[:lower:]' >"$tmp" 2>/dev/null ) & fpid=$!
    ( sleep 5; kill -TERM "$fpid" 2>/dev/null ) & fwatch=$!
    if wait "$fpid" 2>/dev/null && [ -s "$tmp" ]; then
      mv -f "$tmp" "$CACHE" 2>/dev/null || rm -f "$tmp" 2>/dev/null
    else
      rm -f "$tmp" 2>/dev/null   # keep any prior cache as-is
    fi
    kill -TERM "$fwatch" 2>/dev/null; wait "$fwatch" 2>/dev/null
  ) & cache_pid=$!
fi

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

# Collect the cache warmer (it is already self-bounded to ~5s).
[ -n "$cache_pid" ] && wait "$cache_pid" 2>/dev/null

# --- standing note (meta search) -------------------------------------------
line="Composio is available in this session. For any task involving an external app or service (email, calendar, GitHub, Slack, CRMs, docs — 1,000+ apps), resolve the tool just-in-time with \`composio search \"<task>\"\`, then run it with \`composio execute\`. Auth is fully managed. ${auth} Run \`composio --help\` for full usage; \`composio login\` also installs the composio-cli skill with detailed guidance."

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

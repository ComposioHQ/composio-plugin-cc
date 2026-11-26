#!/usr/bin/env bash
# Inject Composio guidance and auth status, and refresh the prompt hook's cache.

set -u
hook_input="$(cat 2>/dev/null || true)"

# Read a top-level string field from the hook input. jq is optional.
hook_field() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$hook_input" | jq -r --arg k "$1" '.[$k] | strings' 2>/dev/null
  else
    printf '%s' "$hook_input" | tr -d '\n' \
      | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -n 1
  fi
}

# Agent compaction state, read by the Composio CLI: one file per chat at
# ~/.composio/agent-compactions/<host>/<session id>, created empty when the chat
# starts, with one line appended per compaction. The contract is "Agent
# compaction state" in the CLI README (ComposioHQ/composio, ts/packages/cli).
# Only the host's session ID and a timestamp are stored; nothing leaves the machine.
record_agent_session() {
  local id_pattern='^[A-Za-z0-9_-]{1,128}$'
  local host="claude" session_id source dir file
  session_id="$(hook_field session_id)"
  source="$(hook_field source)"
  # A pair exported by an outer chat's hook wins: the CLI resolves that pair,
  # so this chat's compactions are recorded under it.
  if [ -n "${COMPOSIO_AGENT_HOST:-}" ] && [ -n "${COMPOSIO_AGENT_SESSION_ID:-}" ]; then
    host="$COMPOSIO_AGENT_HOST"
    session_id="$COMPOSIO_AGENT_SESSION_ID"
  fi
  case "$host" in claude | codex) ;; *) return 0 ;; esac
  [[ "$session_id" =~ $id_pattern ]] || return 0
  [ -n "${HOME:-}" ] || return 0

  dir="$HOME/.composio/agent-compactions/$host"
  file="$dir/$session_id"
  (umask 077 && mkdir -p "$dir") || return 0
  [ -L "$file" ] && return 0
  if [ "$source" = "compact" ]; then
    printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$file" || return 0
  else
    # Creates the file without truncating it, and marks the chat as recently used.
    touch "$file" || return 0
  fi
  if [ "$source" = "startup" ]; then
    # Forget chats untouched for 90 days. A resume touches its file first.
    find "$HOME/.composio/agent-compactions" -mindepth 2 -maxdepth 2 -type f -mtime +90 \
      -exec rm -f {} + 2>/dev/null
  fi

  # Later Bash tool commands, and any agent started from them, get the pair.
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    printf 'export COMPOSIO_AGENT_HOST=%s\nexport COMPOSIO_AGENT_SESSION_ID=%s\n' \
      "$host" "$session_id" >>"$CLAUDE_ENV_FILE"
  fi
  return 0
}
record_agent_session >/dev/null 2>&1 </dev/null || true

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

# Plugin self-update: converge a stale install to the latest published version.
# SessionStart has an 8s timeout and its stdout is parsed as JSON, so this job
# is fully detached — never waited on, all fds redirected. `claude plugin ...`
# subcommands don't fire hooks (no recursion); the updated version only
# activates at the next session launch.
SELF_UPDATE_STATE="${HOME:-}/.composio/plugin-cc-self-update.json"
if [ -n "${HOME:-}" ] && command -v claude >/dev/null 2>&1; then
  now="$(date +%s)"
  last="$(sed -n 's/.*"lastAttempt"[[:space:]]*:[[:space:]]*\([0-9]\{1,\}\).*/\1/p' "$SELF_UPDATE_STATE" 2>/dev/null | head -n 1)"
  if [ -z "$last" ] || [ "$((now - last))" -ge 86400 ]; then
    (
      # Stamp before updating: doubles as the throttle lock. Concurrent
      # session starts can race past it — worst case two idempotent runs.
      mkdir -p "${SELF_UPDATE_STATE%/*}" || exit 0
      printf '{"lastAttempt":%s,"lastResult":"running"}\n' "$now" >"$SELF_UPDATE_STATE" || exit 0
      result="error"
      if claude plugin marketplace update composio; then
        case "$(claude plugin update composio@composio 2>&1)" in
          *"already at the latest"*) result="current" ;;
          *[Uu]pdated*) result="updated" ;;
        esac
      fi
      printf '{"lastAttempt":%s,"lastResult":"%s"}\n' "$now" "$result" >"$SELF_UPDATE_STATE"
    ) >/dev/null 2>&1 </dev/null &
  fi
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

  # Upgrade nudge from the CLI's local release cache — never the network.
  # Stable X.Y.Z versions only; anything missing or malformed stays silent.
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

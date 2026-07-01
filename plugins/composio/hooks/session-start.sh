#!/usr/bin/env bash
# SessionStart hook for the Composio plugin.
#
# 1. Emits ONE concise availability + auth-status line as injected context.
# 2. Refreshes a cached list of Composio toolkit names/slugs (background,
#    bounded, non-blocking) so UserPromptSubmit can match app mentions against
#    the live catalog instead of a hardcoded array.
#
# Tolerates the CLI being missing, offline, or not-logged-in. Always exits 0.

set -u
cat >/dev/null 2>&1 || true   # drain stdin payload; we don't need it

cache="${TMPDIR:-/tmp}/composio-plugin-toolkits.cache"
tmp="${TMPDIR:-/tmp}/composio-whoami.$$"

# --- 1. availability + auth-status line ------------------------------------
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

# --- 2. toolkit-name cache -------------------------------------------------
# Seed a small static fallback synchronously so UserPromptSubmit always has
# something to match, even before the (async) live refresh lands.
if [ ! -s "$cache" ]; then
  printf '%s\n' slack github gitlab bitbucket gmail outlook notion linear jira \
    asana trello clickup hubspot salesforce zendesk intercom discord telegram \
    whatsapp stripe shopify airtable dropbox box figma confluence calendly \
    pagerduty datadog sentry vercel supabase quickbooks reddit youtube zoom \
    googlecalendar googledrive googlesheets googledocs composio \
    >"$cache" 2>/dev/null || true
fi

# Live refresh: source the real toolkit catalog from the CLI and atomically
# replace the cache. Fully detached + bounded so it never blocks or hangs the
# session. Tolerates not-installed / offline (leaves the static fallback).
if command -v composio >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  (
    ( composio dev toolkits list --limit 1000 >"$cache.raw.$$" 2>/dev/null ) & cpid=$!
    ( sleep 10; kill -TERM "$cpid" 2>/dev/null ) & cwatch=$!
    if wait "$cpid" 2>/dev/null && [ -s "$cache.raw.$$" ]; then
      # Extract slugs + names, normalize (lowercase, non-alphanumerics -> spaces).
      jq -r '.[] | (.slug, .name) // empty' "$cache.raw.$$" 2>/dev/null \
        | tr '[:upper:]' '[:lower:]' \
        | sed -E 's/[^a-z0-9]+/ /g; s/^ +//; s/ +$//' \
        | awk 'NF' | sort -u >"$cache.new.$$" 2>/dev/null
      [ -s "$cache.new.$$" ] && mv -f "$cache.new.$$" "$cache" 2>/dev/null
    fi
    kill -TERM "$cwatch" 2>/dev/null
    rm -f "$cache.raw.$$" "$cache.new.$$" 2>/dev/null
  ) </dev/null >/dev/null 2>&1 &
fi

# --- emit injected context -------------------------------------------------
if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$line" \
    '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
else
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$line"
fi

exit 0

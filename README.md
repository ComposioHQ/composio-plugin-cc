# Composio for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
&nbsp;[![claude plugin validate](https://img.shields.io/badge/claude%20plugin-validated-blue.svg)](https://code.claude.com/docs/en/plugins)

Your agent decides what to do — Composio handles the rest. Make just-in-time tool calls across
**[1,000+ apps](https://composio.dev/toolkits)** — Slack, GitHub, Gmail, Notion, Linear, Google
Calendar, Jira, HubSpot, and more — directly from Claude Code, powered by the
[Composio CLI](https://composio.dev). Composio manages auth, permissions, and intelligent tool
routing, so the agent can discover, connect, and run tools without you hand-rolling API calls.

Composio's model is **meta search**: instead of pre-loading a fixed toolset, the agent resolves the
right tool just-in-time — `composio search "<task>"` → `composio execute`.

## What you can do

- **Act on any connected app** — "send a Slack message to #eng", "list my open GitHub PRs",
  "add a lunch event to my calendar tomorrow". The agent finds the tool and runs it.
- **Run cross-app workflows** — turn the latest GitHub PR into a Linear issue and announce it in
  Slack; draft a Notion doc from a calendar event.
- **Connect apps on demand** — fully managed OAuth via `/composio-connect <app>`; the agent hands
  you an auth link and waits for it to complete.
- **Script multi-step work** — `composio run '<js>'` fans out several tool calls (reads in parallel,
  then a write) in one pass.

## What's included

This is a **single, CLI-based** plugin: all logic lives in the `composio` binary, and the plugin is
a thin layer over it. No MCP server, no bundled skill.

| Component | Purpose |
|---|---|
| `hooks/session-start.sh` | **SessionStart** hook: injects a standing note pointing the agent at meta search (`composio search "<task>"` → `composio execute`) + an auth-status line. Re-injects on startup, resume, clear, and **compact** (so long sessions don't lose it). Also **warms a top-50 toolkit cache** (popularity-ranked, from `composio dev toolkits list`) for the per-prompt hook. Fast, bounded, non-blocking; tolerates CLI-not-installed / offline / not-signed-in. |
| `hooks/user-prompt-submit.sh` | **UserPromptSubmit** hook: when a prompt **names a known toolkit** (from the SessionStart-warmed top-50 cache, with a small static fallback + common aliases), injects a one-line `composio search` pointer. Matches app names only — not generic verbs — for high precision. Pure-bash, **no network on the hot path**; silent on no match, always exits 0. |
| `commands/composio-connect.md` | `/composio-connect <app>` — connect a toolkit via managed OAuth. |

The `composio-cli` skill (full `search → execute → link` usage) is **not** bundled: the CLI ships it
and auto-installs it on `composio login`, so a copy here would just duplicate the CLI-installed one.

## Install

### Via this marketplace

```
/plugin marketplace add ComposioHQ/composio-plugin-cc
/plugin install composio@composio
```

Then make sure the CLI is present and you are signed in:

```bash
curl -fsSL https://composio.dev/install | bash   # if not already installed
composio login
```

### Team setup

Add this to `.claude/settings.json` in a project to auto-prompt teammates:

```json
{
  "extraKnownMarketplaces": {
    "composio": {
      "source": { "source": "github", "repo": "ComposioHQ/composio-plugin-cc" }
    }
  },
  "enabledPlugins": {
    "composio@composio": true
  }
}
```

## How it works

The plugin keeps the agent reaching for Composio, then gets out of the way — the `composio` CLI does
the work:

1. **SessionStart** injects a standing meta-search note + your auth status, and warms the top-50
   toolkit cache.
2. When a prompt **names an app**, **UserPromptSubmit** nudges the agent toward `composio search`.
3. The agent runs `composio search "<task>"` → `composio execute` (managed auth), and
   `composio link <app>` to connect anything that isn't connected yet.
4. All logic lives in the CLI — `composio upgrade` updates capabilities, no plugin change needed.

See the CLI-installed `composio-cli` skill (`composio --install-skill claude`) for the full
`search → execute → link` reference.

## Examples

Naming the app explicitly keeps tool search scoped and the run reliable.

**Single app:**

```text
What's on my Google Calendar for tomorrow? Add an event for lunch at 12PM.
```

**Connect on demand:**

```text
/composio-connect linear
```

**Cross-app workflow** (reads feed the write):

```text
Take the latest merged PR in acme/app, open a Linear issue summarizing it,
and post the issue link to #eng in Slack.
```

**Parallel reads, then summarize:**

```text
In parallel, fetch my last 10 Gmail emails, my open Linear issues, and today's
Google Calendar events. Redact personal info, then give me a concise summary.
```

## Development

```bash
make test          # static validation + `claude plugin validate`
make test-unit     # pytest only
make validate      # claude plugin validate only
```

## Updating the plugin

Bump `version` only in `plugins/composio/.claude-plugin/plugin.json` (the single source of truth for
the plugin version), push, and users get updates automatically (if auto-update is on) or via:

```
/plugin marketplace update composio
/reload-plugins
```

## Official Anthropic marketplace

This repo is structured to be submittable to the official Claude Code plugin marketplace: it is a
public repo with a valid `.claude-plugin/marketplace.json`, a valid
`plugins/composio/.claude-plugin/plugin.json`, semantic versioning, and CI that runs
`claude plugin validate`. Submission itself is a manual external step.

## License

MIT — see [LICENSE](./LICENSE).

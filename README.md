# Composio for Claude Code

[![CI](https://github.com/ComposioHQ/composio-plugin-cc/actions/workflows/ci.yml/badge.svg)](https://github.com/ComposioHQ/composio-plugin-cc/actions/workflows/ci.yml)
&nbsp;[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

Composio lets you connect and act on **[1,000+ apps](https://composio.dev/toolkits)** like Google
Workspace, Slack, GitHub, Notion, Linear, Jira, HubSpot, and more — directly from Claude Code,
through the [Composio CLI](https://composio.dev).

Composio handles OAuth, permissions, and intelligent tool routing. Its **meta-search** model
resolves the right tool just-in-time (`composio search "<task>"` → `composio execute`) instead of
pre-loading a fixed toolset — so the agent stays fast and picks the right tool the first time.

## What you can do

- **Act on any connected app** — "send a Slack message to #eng", "list my open GitHub PRs",
  "add a lunch event to my calendar tomorrow". The agent finds the tool and runs it.
- **Run cross-app workflows** — turn the latest GitHub PR into a Linear issue and announce it in
  Slack; draft a Notion doc from a calendar event.
- **Connect apps on demand** — fully managed OAuth; the agent hands you an auth link and waits for
  it to complete.
- **Script multi-step work** — `composio run '<js>'` fans out several calls (parallel reads, then a
  write) in one pass.

## What's included

A **thin, CLI-based** plugin: all logic lives in the `composio` binary. No MCP server, no bundled skill.

| Component | Purpose |
|---|---|
| `hooks/session-start.sh` | Injects a meta-search + auth-status note at session start (and on resume/clear/compact); warms a top-50 toolkit cache. |
| `hooks/user-prompt-submit.sh` | When a prompt names a toolkit from the top-50 cache, nudges the agent toward `composio search`. Pure-bash, no network on the hot path. |
| `commands/composio-connect.md` | `/composio-connect <app>` — connect a toolkit via managed OAuth. |

## Install

### Via this marketplace

```
/plugin marketplace add ComposioHQ/composio-plugin-cc
/plugin install composio@composio
```

Then make sure the CLI is present and you're signed in (the CLI also installs the full
`composio-cli` skill on login):

```bash
curl -fsSL https://composio.dev/install | bash   # if not already installed
composio login
```

### Team setup

Add this to `.claude/settings.json` in a project to auto-enable it for teammates:

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
the work. The agent:

1. **Learns Composio is available** — SessionStart injects a meta-search note + your auth status and
   warms the top-50 toolkit cache.
2. **Gets nudged when it matters** — UserPromptSubmit fires only when a prompt names a known app.
3. **Searches and executes** — `composio search "<task>"` → `composio execute` (managed auth),
   `composio link <app>` to connect anything not yet connected.
4. **Stays current for free** — all logic is in the CLI; `composio upgrade` updates capabilities, no
   plugin change needed.

See the CLI-installed `composio-cli` skill (`composio --install-skill claude`) for the full reference.

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

## License

MIT — see [LICENSE](./LICENSE).

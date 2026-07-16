# Composio for Claude Code

[![CI](https://github.com/ComposioHQ/composio-plugin-cc/actions/workflows/ci.yml/badge.svg)](https://github.com/ComposioHQ/composio-plugin-cc/actions/workflows/ci.yml)
&nbsp;[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

Act on **[1,000+ apps](https://composio.dev/toolkits)** — Google Workspace, Slack, GitHub, Notion,
Linear, Jira, HubSpot, and more — directly from Claude Code. Your agent decides what to do;
[Composio](https://composio.dev) handles the rest: OAuth, permissions, and finding the right tool
for each task. No API keys, no config files.

## What you can do

- **Act on any connected app** — "send a Slack message to #eng", "list my open GitHub PRs",
  "add a lunch event to my calendar tomorrow". Claude finds the tool and runs it.
- **Run cross-app workflows** — turn the latest GitHub PR into a Linear issue and announce it in
  Slack; draft a Notion doc from a calendar event.
- **Connect apps in the flow of work** — fully managed OAuth; Claude hands you an auth link and
  picks up where it left off once you approve. Connections persist across sessions.

## Install

In Claude Code:

```
/plugin marketplace add ComposioHQ/composio-plugin-cc
/plugin install composio@composio
```

Then ask Claude to do something — for example, *"Star `composiohq/composio` on GitHub."* On first
use, Claude sets up everything it needs: it offers to install the Composio CLI if it's missing
(behind the normal permission prompt), signs you in with `composio login`, and hands you an OAuth
link to connect the app. Approve it in your browser and Claude runs the action.

Prefer to set things up ahead of time?

```bash
curl -fsSL https://composio.dev/install | bash
composio login
```

Logging in also installs the `composio-cli` skill, which gives Claude detailed usage guidance.

### Team setup

Add this to `.claude/settings.json` in a project to auto-enable the plugin for teammates:

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

## Examples

Naming the app explicitly keeps tool search scoped and the run reliable.

**Single app:**

```text
What's on my Google Calendar for tomorrow? Add an event for lunch at 12PM.
```

**Connect an app ahead of time:**

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

## What's inside

Three small components; all tool logic lives in the `composio` CLI:

| Component | What it does for you |
|---|---|
| SessionStart hook | Lets Claude know Composio is available and whether you're signed in, so first-time setup happens in the flow of work. |
| UserPromptSubmit hook | When your prompt names an app Composio supports, reminds Claude to reach for Composio instead of improvising. |
| `/composio-connect <app>` | Connects an app via managed OAuth. |

Because capabilities ship in the CLI, `composio upgrade` keeps them current — no plugin update
needed.

## License

MIT — see [LICENSE](./LICENSE).

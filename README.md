# Composio for Claude Code

Your agent decides what to do — Composio handles the rest. Make just-in-time tool calls across
**[1,000+ apps](https://composio.dev/toolkits)** — Slack, GitHub, Gmail, Notion, Linear, Google
Calendar, Jira, HubSpot, and more — directly from Claude Code, powered by the
[Composio CLI](https://composio.dev). Composio manages auth, permissions, and intelligent tool
routing, so the agent can discover, connect, and run tools without you hand-rolling API calls.

Composio's model is **meta search**: instead of pre-loading a fixed toolset, the agent resolves the
right tool just-in-time for the task at hand — `composio search "<task>"` → `composio execute`.

This is a **single, CLI-based** plugin: all logic lives in the `composio` binary, and the plugin is a
thin layer — a SessionStart meta-search hook and the `/composio-connect` command — over it. The CLI
itself ships and auto-installs the `composio-cli` skill on `composio login`, so the plugin doesn't
bundle one. Updating the CLI (`composio upgrade`) updates the capabilities.

## Install

### Via this marketplace (self-hosted)

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

## What it ships

| Component | Purpose |
|---|---|
| `hooks/session-start.sh` | **SessionStart** hook: one concise standing note pointing the agent at Composio's meta-search model (`composio search "<task>"` → `composio execute`) plus an auth-status line. Re-injects on startup, resume, clear, and compact. Fast, bounded, non-blocking; tolerates CLI-not-installed / offline / not-signed-in. |
| `commands/composio-connect.md` | `/composio-connect <app>` — connect a toolkit via managed OAuth. |

The `composio-cli` skill (full `search → execute → link` usage) is **not** bundled: the CLI ships it and
auto-installs it on `composio login`, so a copy here would just duplicate the CLI-installed one.

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
public repo with a valid `.claude-plugin/marketplace.json`, a valid `plugins/composio/.claude-plugin/plugin.json`,
semantic versioning, and CI that runs `claude plugin validate`. Submission itself is a manual external step.

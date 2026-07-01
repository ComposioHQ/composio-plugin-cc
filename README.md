# Composio for Claude Code

Your agent decides what to do — Composio handles the rest. Make just-in-time tool calls across
**[1,000+ apps](https://composio.dev/toolkits)** — Slack, GitHub, Gmail, Notion, Linear, Google
Calendar, Jira, HubSpot, and more — directly from Claude Code, powered by the
[Composio CLI](https://composio.dev). Composio manages auth, permissions, and intelligent tool
routing, so the agent can discover, connect, and run tools without you hand-rolling API calls.

Composio's model is **meta search**: instead of pre-loading a fixed toolset, the agent resolves the
right tool just-in-time for the task at hand — `composio search "<task>"` → `composio execute`.

This is a **single, CLI-based** plugin: all logic lives in the `composio` binary, and the plugin is a
thin layer of hooks, slash commands, and the generated skill over it. Updating the CLI (`composio
upgrade`) updates the capabilities.

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
| `skills/composio-cli` | The **real, generated** Composio CLI skill (vendored trimmed from a pinned STABLE CLI release): the full `search → execute → link` workflow, flags, `run`/`proxy`/`listen`, plus `references/composio-dev.md` and `references/troubleshooting.md`. |
| `hooks/session-start.sh` | **SessionStart** hook: one concise standing note pointing the agent at Composio's meta-search model (`composio search "<task>"` → `composio execute`) plus an auth-status line. Fast, bounded, non-blocking; tolerates CLI-not-installed / offline / not-signed-in. |
| `commands/composio-connect.md` | `/composio-connect <app>` — connect a toolkit via managed OAuth. |
| `commands/composio-onboard.md` | `/composio-onboard` — interactive first-time setup. |

## How the skill stays current

The `composio-cli` skill is generated in [`ComposioHQ/composio`](https://github.com/ComposioHQ/composio)
and published as the `composio-skill.zip` asset on `@composio/cli@*` releases. It is vendored here (trimmed
to `SKILL.md` + the two references) from a **pinned STABLE** release (currently `@composio/cli@0.2.31`). CI
regenerates it and fails on drift, so the skill is single-sourced from the CLI, never hand-edited. To refresh:

```bash
./scripts/refresh-skill.sh                       # pinned tag
./scripts/refresh-skill.sh '@composio/cli@X.Y.Z' # a specific tag
```

Update `PINNED_SKILL_RELEASE` in `tests/config.py` (and the tag in `.github/workflows/ci.yml` and
`scripts/refresh-skill.sh`) when you bump it.

## Development

```bash
make test          # static validation + `claude plugin validate`
make test-unit     # pytest only
make validate      # claude plugin validate only
make refresh-skill # re-vendor the CLI skill
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

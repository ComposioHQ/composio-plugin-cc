# Composio for Claude Code

Connect and act on **[1000+ apps](https://composio.dev/toolkits)** — Slack, GitHub, Gmail, Notion,
Linear, Google Calendar, Jira, HubSpot, and more — directly from Claude Code, powered by the
[Composio CLI](https://composio.dev). Composio handles OAuth, permissions, and intelligent tool
routing, so the agent can discover, connect, and run tools without you hand-rolling API calls.

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
| `skills/composio-cli` | The **real, generated** Composio CLI skill (vendored from a pinned CLI release): the full `search → execute → link` workflow, flags, `run`/`proxy`/`listen`, plus references and troubleshooting. |
| `skills/company-activity-summary` | Generates a cross-app activity summary (Slack, GitHub, Notion, Linear, Gmail, ...) for a time period. |
| `hooks/user-prompt-submit.sh` | **UserPromptSubmit** hook: fast, local keyword match for app/toolkit/integration mentions. On a match it injects a reminder that Composio can do it plus the workflow. No network on the non-matching hot path; never blocks. |
| `hooks/session-start.sh` | **SessionStart** hook: one concise availability + auth-status line (tolerates CLI-not-installed / not-signed-in). |
| `commands/composio-connect.md` | `/composio-connect <app>` — connect a toolkit via managed OAuth. |
| `commands/composio-status.md` | `/composio-status` — show CLI auth status and connected accounts. |
| `commands/composio-run.md` | `/composio-run <slug or task>` — run a known tool, or discover one from a description. |
| `commands/composio-onboard.md` | `/composio-onboard` — interactive first-time setup. |

## How the skill stays current

The `composio-cli` skill is generated in [`ComposioHQ/composio`](https://github.com/ComposioHQ/composio)
and published as the `composio-skill.zip` asset on `@composio/cli@*` releases. It is vendored here from a
**pinned** release (currently `@composio/cli@0.2.31`). To refresh:

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

Bump `version` in `plugins/composio/.claude-plugin/plugin.json` and the marketplace entry, push, and
users get updates automatically (if auto-update is on) or via:

```
/plugin marketplace update composio
/reload-plugins
```

## Official Anthropic marketplace

This repo is structured to be submittable to the official Claude Code plugin marketplace: it is a
public repo with a valid `.claude-plugin/marketplace.json`, a valid `plugins/composio/.claude-plugin/plugin.json`,
semantic versioning, and CI that runs `claude plugin validate`. See [`SUBMISSION.md`](SUBMISSION.md) for
the submission checklist. Submission itself is a manual external step.

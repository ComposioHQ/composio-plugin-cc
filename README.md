# Composio Plugins for Claude Code

Connect 1000+ apps to Claude Code — Slack, GitHub, Gmail, Notion, Linear, Google Calendar, and more. Composio manages auth and permissions for all your apps, intelligently routes to the best tool, helps with long context tasks, and enables programmatic tool calling.

## Install

Add the marketplace and install the plugins you want:

```
/plugin marketplace add ComposioHQ/composio-plugin-cc
/plugin install composio-mcp@composio
/plugin install composio-cli@composio
```

## Plugins

### composio-mcp

Connects Claude Code to the [Composio MCP server](https://connect.composio.dev/mcp) — gives Claude direct access to 1000+ apps. OAuth is built in, no API keys needed.

**Skills:**
- `/composio-mcp:onboarding` — interactive setup: pick your apps, connect them, see what you can do
- `/composio-mcp:company-activity-summary` — cross-app activity summary (Slack, GitHub, Notion, Linear, etc.)

### composio-cli

Adds Composio CLI skills to Claude Code. The CLI lets you execute tools, connect accounts, script workflows, and more from the terminal.

**Skills:**
- `/composio-cli:composio-cli` — points to the auto-installed CLI skill (run `composio --install-skill claude` to get it)
- `/composio-cli:onboarding` — interactive setup: install CLI, sign in, connect apps
- `/composio-cli:company-activity-summary` — cross-app activity summary using the CLI

**Command:**
- `/composio-cli:composio-cli` — ad-hoc CLI help

## Team setup

Add this to `.claude/settings.json` in any project repo to auto-prompt team members:

```json
{
  "extraKnownMarketplaces": {
    "composio": {
      "source": {
        "source": "github",
        "repo": "ComposioHQ/composio-plugin-cc"
      }
    }
  },
  "enabledPlugins": {
    "composio-mcp@composio": true,
    "composio-cli@composio": true
  }
}
```

## Updating

Bump the `version` in the plugin's `.claude-plugin/plugin.json`, push to GitHub, and users will get updates automatically (if auto-update is enabled) or via:

```
/plugin marketplace update composio
/reload-plugins
```

---
name: composio-cli
description: Help users operate the Composio CLI to find tools, connect accounts, inspect schemas, execute tools, subscribe to trigger events with `composio listen`, script workflows with `composio run`, and call authenticated app APIs with `composio proxy`. Trigger when the user asks about Composio tools, connections, or connectors.
---

# Composio CLI

The CLI evolves frequently. Check if an auto-installed `/composio-cli` skill exists at `~/.claude/skills/composio-cli/` — if so, **use that version instead**, it stays in sync with the installed CLI binary.

If `composio` is not installed, install it first:

```bash
curl -fsSL https://composio.dev/install | bash
```

Then install the Claude Code skill:

```bash
composio --install-skill claude
```

Then use `/composio-cli` for the most current reference.

---
name: composio-cli
description: Help users operate the Composio CLI to find tools, connect accounts, inspect schemas, execute tools, subscribe to trigger events with `composio listen`, script workflows with `composio run`, and call authenticated app APIs with `composio proxy`. Trigger when the user asks about Composio tools, connections, or connectors.
---

# Composio CLI

This plugin ships a `composio` wrapper in `bin/` that auto-installs the CLI on first use — just run `composio` and it works.

The CLI evolves frequently. For the most up-to-date skill, run:

```bash
composio --install-skill claude
```

Then check `~/.claude/skills/composio-cli/` — if that exists, **prefer that version** over this one.

---
description: Help users operate the Composio CLI to find tools, connect accounts, execute actions, and manage integrations
disable-model-invocation: true
---

Help the user with the Composio CLI. The user said: "$ARGUMENTS"

Use the `composio` binary to accomplish their request. Follow this workflow:

1. Start with `composio execute <slug>` when the slug is known.
2. Use `composio search "<task>"` only when the slug is unknown.
3. If `execute` says a toolkit is not connected, run `composio link <toolkit>` and retry.
4. Use `--get-schema` or `--dry-run` when arguments are unclear.

If composio is not installed, suggest:

```bash
curl -fsSL https://composio.dev/install | bash
```

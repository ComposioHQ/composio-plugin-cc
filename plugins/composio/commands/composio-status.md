---
description: Show Composio CLI auth status and connected accounts.
---

# Composio status

Report the user's Composio setup.

1. Check install + auth:
   ```bash
   composio whoami
   ```
   - CLI missing → tell the user: `curl -fsSL https://composio.dev/install | bash`
   - Not signed in → tell the user: `composio login`

2. List connected accounts / toolkits:
   ```bash
   composio connections list
   ```

Summarize concisely: whether the CLI is installed, whether the user is signed in, and which apps are currently connected. If nothing is connected, suggest `/composio-connect <app>` or `/composio-onboard`.

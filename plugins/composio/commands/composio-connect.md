---
description: Connect an app/toolkit to Composio via managed OAuth (e.g. Slack, GitHub, Gmail).
argument-hint: <app> (e.g. slack, github, gmail, notion, linear)
---

# Connect a Composio toolkit

Connect the app the user named: **$ARGUMENTS**

Steps:

1. Make sure the CLI is available and the user is signed in:
   ```bash
   composio whoami
   ```
   - If the CLI is missing: `curl -fsSL https://composio.dev/install | bash`
   - If not signed in: `composio login`

2. Start the managed OAuth flow for the toolkit:
   ```bash
   composio link $ARGUMENTS
   ```
   If you are in a non-interactive context, use `composio link $ARGUMENTS --no-browser` and hand the returned URL to the user, then wait for them to confirm completion.

3. Verify the connection with a lightweight read, for example:
   - GitHub: `composio execute GITHUB_GET_THE_AUTHENTICATED_USER -d '{}'`
   - Slack: `composio execute SLACK_LIST_CHANNELS -d '{}'`
   - Gmail: `composio execute GMAIL_FETCH_EMAILS -d '{ max_results: 1 }'`

If `$ARGUMENTS` is empty, ask the user which app they want to connect. Composio supports 1000+ apps, so try `composio link <app>` for any name.

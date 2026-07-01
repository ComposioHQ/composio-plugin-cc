---
description: Connect an app/toolkit to Composio via managed OAuth (e.g. Slack, GitHub, Gmail).
argument-hint: <app> (e.g. slack, github, gmail, notion, linear)
---

# Connect a Composio toolkit

Connect the app the user named: **$ARGUMENTS**

Assume the `composio` CLI is installed and authenticated (SessionStart surfaces its status). If a step reports you are not signed in, run `composio login` and retry.

Steps:

1. Start the managed OAuth flow for the toolkit:
   ```bash
   composio link $ARGUMENTS
   ```
   If you are in a non-interactive context, use `composio link $ARGUMENTS --no-browser` and hand the returned URL to the user, then wait for them to confirm completion.

2. Verify the connection with a lightweight read, for example:
   - GitHub: `composio execute GITHUB_GET_THE_AUTHENTICATED_USER -d '{}'`
   - Slack: `composio execute SLACK_LIST_CHANNELS -d '{}'`
   - Gmail: `composio execute GMAIL_FETCH_EMAILS -d '{ max_results: 1 }'`

If `$ARGUMENTS` is empty, ask the user which app they want to connect. Composio supports 1000+ apps, so try `composio link <app>` for any name.

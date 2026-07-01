---
description: Interactive Composio onboarding — install, sign in, and connect your first apps.
---

# Composio onboarding

Guide a new user through setup. Use AskUserQuestion at each decision point; keep it conversational.

## Step 1: Auth

Assume the `composio` CLI is installed (SessionStart surfaces its status). Confirm sign-in:

```bash
composio whoami
```

- **Not signed in** → run `composio login` and wait for completion.
- **Signed in** → continue.

## Step 2: Understand the goal

Ask what they want to automate. Examples: team updates (Slack, Gmail), task tracking (Linear, Notion), email triage (Gmail), daily briefing (Slack + Gmail + Calendar + Linear), scheduling (Google Calendar).

## Step 3: Recommend + connect

Recommend 2-4 apps for their goal and confirm. For each, run:

```bash
composio link <app> --no-browser
```

Share the OAuth URL and wait for confirmation. Verify each with a lightweight read (e.g. `composio execute SLACK_LIST_CHANNELS -d '{}'`). Composio supports 1000+ apps, so try `composio link <app>` for any name.

## Step 4: Show what they can do

Present 3-4 personalized example actions based on what they connected, then ask what they want to try first.

Guidelines: ask before assuming, keep it short, and after onboarding let the user drive.

---
name: onboarding
description: Interactive onboarding — checks CLI install and auth, learns what the user wants to automate across their apps, and connects the right ones. Use when the user is new to Composio, says "get started", or asks what apps they can connect.
disable-model-invocation: true
---

# Onboarding (CLI)

Interactive flow to get the user set up. Use AskUserQuestion at every decision point.

## Step 1: Check CLI and auth

Run `composio whoami` to check if the CLI is installed and the user is signed in.

- **Not installed**: tell the user to run `curl -fsSL https://composio.dev/install | bash` and then `composio login`.
- **Not signed in**: run `composio login` to start the auth flow.
- **Signed in**: move on.

## Step 2: Understand what they want to do

Use AskUserQuestion:

> What would you like to automate or speed up with your apps? For example:
>
> - **Team updates** — post summaries to Slack, send status emails, notify channels
> - **Task tracking** — create and update issues in Linear, Jira, or Asana from conversations
> - **Email management** — draft replies, triage inbox, send follow-ups
> - **Knowledge & docs** — save notes to Notion, search across docs, update wikis
> - **Daily briefing** — get a summary of what's happening across Slack, email, calendar, and tasks
> - **Scheduling** — check availability, create calendar events, send invites
> - **Something else** — just describe it and I'll figure out the right apps

## Step 3: Recommend and connect apps

Based on their answer, recommend 2-4 apps that would help. Map use cases to apps:

| Use case | Recommended apps |
|----------|-----------------|
| Team updates | Slack, Gmail |
| Task tracking | Linear, Notion |
| Email management | Gmail |
| Knowledge & docs | Notion, Google Drive |
| Daily briefing | Slack, Gmail, Google Calendar, Linear |
| Scheduling | Google Calendar, Gmail |

Use AskUserQuestion to confirm:

> Based on what you described, I'd recommend connecting **[apps]**. Sound good, or would you like to add/change any?

Then for each app, run:

```bash
composio link <app> --no-browser
```

Share the OAuth URL with the user and wait for confirmation. After linking, verify with a quick execute:

- **GitHub**: `composio execute GITHUB_GET_THE_AUTHENTICATED_USER -d '{}'`
- **Gmail**: `composio execute GMAIL_FETCH_EMAILS -d '{ max_results: 1 }'`
- **Slack**: `composio execute SLACK_LIST_CHANNELS -d '{}'`
- **Notion**: `composio execute NOTION_SEARCH_NOTION_PAGE -d '{ query: "" }'`
- **Linear**: `composio execute LINEAR_LIST_LINEAR_TEAMS -d '{}'`
- **Google Calendar**: `composio execute GOOGLECALENDAR_LIST_EVENTS -d '{}'`

## Step 4: Show what they can do

After connecting, use AskUserQuestion to present personalized examples based on their use case and connected apps. Tailor the examples to what they said they wanted to do in Step 2 — don't just list generic capabilities.

End with: "What would you like to try first?"

## Guidelines

- Use AskUserQuestion at every step — never assume
- Keep it conversational, not a wall of text
- If the user names an app not listed above, still try `composio link <app>` — Composio supports 1000+ apps
- After onboarding, let the user drive

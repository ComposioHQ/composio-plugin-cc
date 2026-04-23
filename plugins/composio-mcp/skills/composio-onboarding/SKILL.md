---
name: onboarding
description: Interactive onboarding — checks auth, learns what the user wants to automate across their apps, and connects the right ones. Use when the user is new to Composio, says "get started", or asks what apps they can connect.
---

# Onboarding (MCP)

Interactive flow to get the user set up. Use AskUserQuestion at every decision point.

## Step 1: Check auth

Try a lightweight MCP tool call to verify the MCP server is connected and the user is signed in.

- If the server is not responding or the user isn't authenticated, ask them to sign up / sign in at https://app.composio.dev and complete the OAuth flow when prompted by the MCP server.
- Once auth is confirmed, move on.

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

Then for each app, try a read-only tool call to check if it's already connected:

- **GitHub**: `GITHUB_GET_THE_AUTHENTICATED_USER`
- **Gmail**: `GMAIL_FETCH_EMAILS` with `{ max_results: 1 }`
- **Slack**: `SLACK_LIST_CHANNELS`
- **Notion**: `NOTION_SEARCH_NOTION_PAGE` with `{ query: "" }`
- **Linear**: `LINEAR_LIST_LINEAR_TEAMS`
- **Google Calendar**: `GOOGLECALENDAR_LIST_EVENTS`

If connected, confirm it. If not, the MCP server will provide an OAuth link — share it with the user and retry after they complete the flow.

## Step 4: Show what they can do

After connecting, use AskUserQuestion to present personalized examples based on their use case and connected apps. Tailor the examples to what they said they wanted to do in Step 2 — don't just list generic capabilities.

End with: "What would you like to try first?"

## Guidelines

- Use AskUserQuestion at every step — never assume
- Keep it conversational, not a wall of text
- If the user names an app not listed above, still try to connect it — Composio supports 1000+ apps
- After onboarding, let the user drive

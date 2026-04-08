---
name: company-activity-summary
description: Generates comprehensive company activity summary across connected apps — Slack, GitHub, Notion, Linear, Gmail, and more. Uses the composio CLI to fetch data. Use when user asks for company updates, daily summary, or what's happening across the org.
disable-model-invocation: true
---

# Company Activity Summary (CLI)

Generate a comprehensive summary of company activity over the last 24 hours (or specified time period) using the `composio` CLI.

## Arguments

- `$ARGUMENTS` - Time period to analyze (default: "last 24 hours"). Examples: "last 24 hours", "last 7 days", "since Monday"

## Step 1: Discover Connected Apps

Check which apps the user has connected. Use AskUserQuestion if you're unsure which apps they use. Otherwise, try lightweight calls and skip apps that aren't connected:

```bash
# Try each — skip silently if it fails with a connection error
composio execute SLACK_LIST_CHANNELS -d '{}'
composio execute GITHUB_GET_THE_AUTHENTICATED_USER -d '{}'
composio execute NOTION_SEARCH_NOTION_PAGE -d '{ query: "" }'
composio execute LINEAR_LIST_LINEAR_TEAMS -d '{}'
composio execute GMAIL_FETCH_EMAILS -d '{ max_results: 1 }'
composio execute GOOGLECALENDAR_LIST_EVENTS -d '{}'
```

Note which apps are connected and skip the rest.

## Step 2: Launch Parallel Agents Per Connected App

For each connected app, launch a background Agent to gather and summarize activity. Each agent uses `composio execute` and `composio run` to fetch data, and writes its summary to a markdown file in the current working directory.

### Slack Agent
Prompt: Fetch Slack activity for "$ARGUMENTS" (default: last 24 hours).
1. List channels:
   ```bash
   composio execute SLACK_LIST_CHANNELS -d '{}'
   ```
2. For active channels, fetch messages:
   ```bash
   composio execute SLACK_GET_CHANNEL_MESSAGES_AND_THREAD_REPLIES -d '{ channel: "<id>", limit: 50 }'
   ```
3. Focus on: key discussions, decisions, announcements, questions
4. Write summary to `slack-activity-summary.md`

### GitHub Agent
Prompt: Fetch GitHub activity for "$ARGUMENTS" (default: last 24 hours).
1. List repos:
   ```bash
   composio execute GITHUB_LIST_REPOSITORIES_FOR_THE_AUTHENTICATED_USER -d '{ sort: "updated", per_page: 10 }'
   ```
2. For each active repo, fetch PRs:
   ```bash
   composio execute GITHUB_LIST_PULL_REQUESTS_IN_A_REPOSITORY -d '{ owner: "<owner>", repo: "<repo>", state: "all", sort: "updated" }'
   ```
3. For significant PRs, get details and diff via `gh` CLI
4. Focus on: PRs opened/merged/reviewed, issues created/closed
5. Write summary to `github-activity-summary.md`

### Notion Agent
Prompt: Fetch Notion activity for "$ARGUMENTS" (default: last 24 hours).
1. Search recent pages:
   ```bash
   composio execute NOTION_SEARCH_NOTION_PAGE -d '{ query: "", sort_direction: "descending", sort_timestamp: "last_edited_time", page_size: 50 }'
   ```
2. For important pages, fetch content:
   ```bash
   composio execute NOTION_FETCH_ALL_BLOCK_CONTENTS -d '{ page_url: "<url>", recursive: true, max_blocks: 200 }'
   ```
3. Focus on: doc updates, meeting notes, project tracking changes
4. Write summary to `notion-activity-summary.md`

### Linear Agent
Prompt: Fetch Linear activity for "$ARGUMENTS" (default: last 24 hours).
1. Fetch updated issues:
   ```bash
   composio execute LINEAR_LIST_LINEAR_ISSUES -d '{}'
   ```
   Or use GraphQL for richer data:
   ```bash
   composio execute LINEAR_RUN_QUERY_OR_MUTATION -d '{ query_or_mutation: "query { issues(filter: { updatedAt: { gte: \"<cutoff_iso>\" } }, first: 50) { nodes { id identifier title state { name } assignee { name } team { name } updatedAt } } }" }'
   ```
2. Group by team and status changes
3. Focus on: issues completed, created, blockers, project progress
4. Write summary to `linear-activity-summary.md`

### Gmail Agent (if connected)
Prompt: Fetch Gmail activity for "$ARGUMENTS" (default: last 24 hours).
```bash
composio execute GMAIL_FETCH_EMAILS -d '{ max_results: 20 }'
```
Focus on: important threads, action items, external communications
Write summary to `gmail-activity-summary.md`

### Calendar Agent (if connected)
Prompt: Fetch Google Calendar activity for "$ARGUMENTS" (default: last 24 hours).
```bash
composio execute GOOGLECALENDAR_LIST_EVENTS -d '{ timeMin: "<start_iso>", timeMax: "<end_iso>" }'
```
Focus on: meetings that happened, key attendees, upcoming schedule
Write summary to `calendar-activity-summary.md`

### Scripted Alternative (composio run)

For more complex data gathering, agents can use `composio run` to script multi-step fetches:

```bash
composio run '
  const [channels, repos] = await Promise.all([
    execute("SLACK_LIST_CHANNELS"),
    execute("GITHUB_LIST_REPOSITORIES_FOR_THE_AUTHENTICATED_USER", { sort: "updated", per_page: 10 }),
  ]);
  // Process and output results
  console.log(JSON.stringify({ channels: channels.data, repos: repos.data }, null, 2));
'
```

## Step 3: Compile Overview

After all agents complete, read each summary file and present:

```markdown
# Company Activity Summary - [Date Range]

## Connected Apps Analyzed
- [list of apps that were successfully queried]

## Key Highlights
[3-5 bullet points of the most important things across all apps]

## Detailed Summaries
| Platform | File | Highlights |
|----------|------|------------|
| Slack | [slack-activity-summary.md](./slack-activity-summary.md) | [1-line summary] |
| GitHub | [github-activity-summary.md](./github-activity-summary.md) | [1-line summary] |
| ... | ... | ... |
```

Read each file and provide a brief overview of key highlights, then let the user know they can open individual files for full details.

## Guidelines

- Only summarize apps that are actually connected — don't fail or warn about missing apps
- Use AskUserQuestion if the time period is ambiguous
- Prefer `composio execute` for single tool calls, `composio run` for multi-step scripts
- If any agent fails, note which summaries are missing but still present the rest
- Focus on actionable insights, not just lists of items

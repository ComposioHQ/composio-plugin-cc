---
name: composio-mcp
description: Use Composio MCP tools to interact with 1000+ apps — GitHub, Slack, Notion, Gmail, Linear, Jira, and more. Trigger when the user asks to connect an app, execute an action on an external service, or work with connectors.
---

# Composio MCP

You have access to Composio tools via the MCP server at connect.composio.dev. These tools let you interact with 1000+ apps and services the user has connected through Composio. OAuth authentication is handled automatically.

## When to use

- The user asks to perform actions on external apps (e.g., "create a GitHub issue", "send a Slack message", "add a Notion page")
- The user asks to check or fetch data from connected services
- The user wants to trigger workflows across multiple apps

## How to use

1. Use the available Composio MCP tools directly — they appear as standard tools in your toolkit
2. If a tool call fails with an auth error, the user needs to connect the app through Composio
3. Tools are namespaced by app (e.g., `GITHUB_CREATE_ISSUE`, `SLACK_SEND_MESSAGE`)

## Tips

- Check which tools are available before suggesting actions
- OAuth is handled by the Composio server — no API keys needed from the user
- You can chain multiple tool calls across different apps to build workflows

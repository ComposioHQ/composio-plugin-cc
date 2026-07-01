---
description: Run a Composio tool by slug, or discover one from a task description.
argument-hint: <SLUG or plain-English task> (e.g. GITHUB_CREATE_AN_ISSUE, or "star a repo")
---

# Run a Composio tool

Request: **$ARGUMENTS**

Decide the path:

- **Looks like a tool slug** (UPPER_SNAKE_CASE, e.g. `GITHUB_CREATE_AN_ISSUE`): use it directly.
  1. Inspect inputs first if unsure:
     ```bash
     composio execute $ARGUMENTS --get-schema
     ```
  2. Execute:
     ```bash
     composio execute $ARGUMENTS -d '{ ... }'
     ```

- **Looks like a task description**: discover the slug first, then execute.
  ```bash
  composio search "$ARGUMENTS"
  ```
  Pick the best slug, inspect with `--get-schema`, then `composio execute <SLUG> -d '{ ... }'`.

Guidelines:
- Preview risky/writing actions with `--dry-run` before running for real.
- If execution reports the toolkit is not connected, run `composio link <toolkit>` and retry.
- For multi-step scripted workflows, use `composio run '<js>'`.

Refer to the `composio:composio-cli` skill for full flag reference.

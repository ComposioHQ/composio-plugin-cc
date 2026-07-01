# Greenfield Claude Code plugin — composio-plugin-cc slice

**Goal:** Rebuild `ComposioHQ/composio-plugin-cc` as a single, thin, high-quality **CLI-based** Claude Code plugin (all logic in the `composio` binary) that ships real hooks + the real generated skill + slash commands, is CI-validated, and is publishable to BOTH our self-hosted marketplace and the official Anthropic marketplace.

**Branch:** kj/greenfield-cc-plugin   **PR:** <link once open>

## Decisions (locked)
- **CLI-only.** Remove the `composio-mcp` plugin from this repo (MCP is for non-terminal clients elsewhere). Call this out explicitly in the PR.
- **Thin plugin:** no business logic in the plugin; hooks/commands shell out to `composio`. Update story = `composio upgrade`.
- **Dual marketplace:** keep our `.claude-plugin/marketplace.json` (self-hosted: `/plugin marketplace add ComposioHQ/composio-plugin-cc`) AND make the plugin submission-ready for the official Anthropic marketplace.
- **Skill single-sourcing:** bundle the REAL generated `composio-cli` skill (not the current stub), sourced by pulling the pinned `composio-skill.zip` from a Composio CLI GitHub release in CI; vendor it into the plugin for the initial PR.

## IMPORTANT — verify schemas against LIVE docs first
The current repo's `.claude-plugin/marketplace.json` uses a top-level `plugins` array with `source` (NOT the `entries` shape some docs summaries show). Before writing, fetch the official Claude Code docs (code.claude.com/docs) and confirm the CURRENT required schema for: `plugin.json`, `hooks/hooks.json` (esp. `UserPromptSubmit` input field for the raw prompt + the `additionalContext` output field + exit codes), and `marketplace.json`. Prefer the format the existing working file uses when in doubt, and validate with `claude plugin validate` if available.

## Files to change
- `.claude-plugin/marketplace.json` — collapse to a single plugin entry (`composio`), bump version, polish description/metadata. (Remove the `composio-mcp` entry.)
- `plugins/composio-mcp/**` — **delete** (CLI-only decision).
- `plugins/composio-cli/` → rename/rework to `plugins/composio/` (or keep name; pick one, keep marketplace `source` in sync):
  - `.claude-plugin/plugin.json` — full manifest: name, version, description, author, homepage, repository, license, keywords, logo if available. Anthropic-submission-ready.
  - `hooks/hooks.json` + `hooks/*.sh` — **the core new value:**
    - `UserPromptSubmit`: fast local keyword match for toolkit/app/integration mentions; on match, return `additionalContext` reminding the agent Composio can do it + the search→execute→link workflow (optionally enrich by shelling out to `composio` only when matched + logged in). Must be cheap (timeout ~5s, non-blocking, no network on the hot path unless matched). Reference pattern: openclaw's prompt-injection.
    - `SessionStart`: one-line availability + auth-status nudge (`composio whoami`, cached).
  - `skills/composio-cli/` — bundle the REAL generated skill (vendor the current `composio-cli` skill from the latest Composio CLI release's `composio-skill.zip`), replacing the stub SKILL.md.
  - `commands/*.md` — real slash commands: `/composio-connect <app>`, `/composio-status`, `/composio-run`, `/composio-onboard` (thin — each shells out to `composio`).
  - CLI presence: replace/repair the fragile `bin/composio` PATH-shim (silent `curl|bash`) with a safer path — prefer the supported `composio --install-skill claude` flow and an explicit "not installed → guided install" rather than a silent shadowing shim. Keep it thin.
- `.github/workflows/ci.yml` — validate frontmatter/manifest/skill discovery/cross-references (mirror `ComposioHQ/composio-mcp-plugin`'s test approach); run `claude plugin validate` if available; a step (or documented script) to pull/refresh the pinned `composio-skill.zip`.
- `README.md` — install (both marketplaces), what it ships, dual-marketplace + Anthropic submission note.
- (Optional) `SUBMISSION.md` — checklist/notes for Anthropic official-marketplace submission (public repo ✓, valid structure, versioning, safety screening). Actual submission is a manual external step (platform.claude.com/plugins/submit).

## Cross-repo deps
- The real skill originates in `ComposioHQ/composio` (`ts/packages/cli/skills-src/composio-cli/`), shipped as `composio-skill.zip` on CLI releases. The plugin depends on that release asset (pin a version).
- Landing/dashboard/apollo phases are independent; no lockstep needed for this PR.

## Verification
- `claude plugin validate <plugin dir>` passes (or `claude --plugin-dir` loads it cleanly).
- Hooks: manually trigger `UserPromptSubmit` locally (simulate stdin JSON) and confirm `additionalContext` is emitted on a toolkit mention and NOT on unrelated prompts; confirm fast + non-blocking.
- `marketplace.json` parses and lists exactly one plugin with a correct `source`.
- The bundled skill is the real generated content (not the stub) and its references resolve.
- CI is green.

## Done when
A reviewer can `/plugin marketplace add ComposioHQ/composio-plugin-cc` + install the single `composio` plugin; it prompt-injects on toolkit mentions, ships the real skill + working slash commands, delegates all logic to the CLI, passes `claude plugin validate` + CI, and is structured/versioned so it can be submitted to the official Anthropic marketplace. PR open with a clear description (incl. the composio-mcp removal).

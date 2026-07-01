# Official Anthropic marketplace — submission checklist

This plugin is structured to be submittable to the official Claude Code plugin marketplace. The
submission itself is a manual, external step (see Claude Code plugin docs / the official marketplace
submission flow). Use this checklist before submitting.

## Readiness checklist

- [x] **Public repository** — `ComposioHQ/composio-plugin-cc`.
- [x] **Valid marketplace manifest** — `.claude-plugin/marketplace.json` lists exactly one plugin with
      a relative `source`, an `owner`, and metadata.
- [x] **Valid plugin manifest** — `plugins/composio/.claude-plugin/plugin.json` has `name` (kebab-case),
      `version` (semver), `description`, `author`, `homepage`, `repository`, `license`, `keywords`.
- [x] **Passes validation** — `claude plugin validate ./plugins/composio` and
      `claude plugin validate ./.claude-plugin/marketplace.json` succeed.
- [x] **Discoverable components** — `skills/`, `commands/`, and `hooks/hooks.json` present; hook
      commands reference `${CLAUDE_PLUGIN_ROOT}` and the scripts are executable.
- [x] **Semantic versioning** — bump `version` in both `plugin.json` and the marketplace entry together.
- [x] **CI** — `.github/workflows/ci.yml` runs static validation + `claude plugin validate`.
- [x] **No secrets / no silent network side effects** — hooks never block, do no network on the
      non-matching hot path, and shell out to the CLI only with bounded timeouts.

## Before each submission / release

1. `make test` is green.
2. `version` bumped in `plugins/composio/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
3. Vendored skill is current for the intended CLI release (`scripts/refresh-skill.sh`), and
   `PINNED_SKILL_RELEASE` / CI tag match.
4. `README.md` install instructions accurate.
5. Optionally tag a release: `claude plugin tag ./plugins/composio`.

## Notes

- The plugin is intentionally **thin**: all capability lives in the `composio` CLI. The plugin ships
  hooks, slash commands, and the generated skill, and delegates execution to the CLI.
- MCP support was intentionally removed from this repo (CLI-only). MCP for non-terminal clients lives
  elsewhere (e.g. the Cursor plugin at `ComposioHQ/composio-mcp-plugin`).

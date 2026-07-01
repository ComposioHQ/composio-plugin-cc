"""Paths and expected values shared across the test suite."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "composio"

SKILLS_ROOT = PLUGIN_ROOT / "skills"
COMMANDS_ROOT = PLUGIN_ROOT / "commands"
HOOKS_ROOT = PLUGIN_ROOT / "hooks"
HOOKS_CONFIG = HOOKS_ROOT / "hooks.json"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = REPO_ROOT / ".claude-plugin" / "marketplace.json"

# Read from the manifest so a rename only needs to change one file.
PLUGIN_NAME = json.loads(PLUGIN_MANIFEST.read_text())["name"]

EXPECTED_SKILLS = ("composio-cli", "company-activity-summary")
EXPECTED_COMMANDS = (
    "composio-connect",
    "composio-status",
    "composio-run",
    "composio-onboard",
)
EXPECTED_HOOK_EVENTS = ("UserPromptSubmit", "SessionStart")

# The composio CLI release whose composio-skill.zip is vendored under
# skills/composio-cli. Keep in sync with scripts/refresh-skill.sh.
PINNED_SKILL_RELEASE = "@composio/cli@0.2.31"

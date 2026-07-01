"""Check the plugin manifest and marketplace manifest are valid and consistent."""
import json
import re

from tests.config import (
    MARKETPLACE_MANIFEST,
    PLUGIN_MANIFEST,
    PLUGIN_NAME,
    PLUGIN_ROOT,
)

KEBAB = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+")


def _load(path):
    return json.loads(path.read_text())


class TestPluginManifest:
    def setup_method(self):
        self.manifest = _load(PLUGIN_MANIFEST)

    def test_name_is_kebab_case(self):
        assert KEBAB.match(self.manifest["name"]), f"plugin name '{self.manifest['name']}' not kebab-case"

    def test_has_version(self):
        assert SEMVER.match(self.manifest.get("version", "")), "plugin.json needs a semver `version`"

    def test_has_description(self):
        assert len(self.manifest.get("description", "")) > 20, "plugin.json needs a real description"

    def test_skills_dir_is_discoverable(self):
        assert (PLUGIN_ROOT / "skills").is_dir(), "skills/ directory must exist for auto-discovery"

    def test_hooks_and_commands_present(self):
        assert (PLUGIN_ROOT / "hooks" / "hooks.json").exists(), "hooks/hooks.json must exist"
        assert (PLUGIN_ROOT / "commands").is_dir(), "commands/ directory must exist"


class TestMarketplaceManifest:
    def setup_method(self):
        self.market = _load(MARKETPLACE_MANIFEST)

    def test_lists_exactly_one_plugin(self):
        plugins = self.market.get("plugins", [])
        assert len(plugins) == 1, f"marketplace should list exactly one plugin, found {len(plugins)}"

    def test_plugin_entry_matches(self):
        entry = self.market["plugins"][0]
        assert entry["name"] == PLUGIN_NAME, (
            f"marketplace plugin name '{entry['name']}' != plugin.json name '{PLUGIN_NAME}'"
        )

    def test_source_points_at_plugin_dir(self):
        entry = self.market["plugins"][0]
        assert entry["source"] == f"./plugins/{PLUGIN_NAME}", (
            f"marketplace source '{entry.get('source')}' does not point at ./plugins/{PLUGIN_NAME}"
        )
        assert PLUGIN_ROOT.is_dir(), "source directory must exist on disk"

    def test_no_mcp_plugin_remains(self):
        names = [p["name"] for p in self.market.get("plugins", [])]
        assert "composio-mcp" not in names, "composio-mcp must be removed (CLI-only)"

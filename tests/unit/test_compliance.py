"""Marketplace/repo compliance guards (ComposioHQ plugin policy)."""
import json

from tests.config import MARKETPLACE_MANIFEST, REPO_ROOT


def _market():
    return json.loads(MARKETPLACE_MANIFEST.read_text())


def test_marketplace_has_owner_name():
    owner = _market().get("owner", {})
    assert owner.get("name"), "marketplace.json must declare owner.name"


def test_plugin_entry_has_no_version_key():
    # Single-source the plugin version in plugin.json; the marketplace entry
    # must NOT carry its own `version` (guards against the dual-version regression).
    entry = _market()["plugins"][0]
    assert "version" not in entry, (
        "marketplace plugins[0] must not have a `version` key — "
        "the plugin version lives only in plugin.json"
    )


def test_license_file_exists():
    assert (REPO_ROOT / "LICENSE").is_file(), "a top-level LICENSE file must exist"

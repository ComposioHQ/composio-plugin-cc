"""Validate the hooks manifest and hook scripts."""
import json
import os
import stat
import subprocess

from tests.config import EXPECTED_HOOK_EVENTS, HOOKS_CONFIG, HOOKS_ROOT, PLUGIN_ROOT


def _load():
    return json.loads(HOOKS_CONFIG.read_text())


class TestHooksManifest:
    def setup_method(self):
        self.hooks = _load().get("hooks", {})

    def test_manifest_parses(self):
        assert self.hooks, "hooks.json must define a top-level `hooks` object"

    def test_expected_events_present(self):
        for event in EXPECTED_HOOK_EVENTS:
            assert event in self.hooks, f"hooks.json missing `{event}` event"

    def test_commands_use_plugin_root_and_exist(self):
        for event, groups in self.hooks.items():
            for group in groups:
                for hook in group.get("hooks", []):
                    cmd = hook.get("command", "")
                    assert "${CLAUDE_PLUGIN_ROOT}" in cmd, (
                        f"{event} hook command must reference ${{CLAUDE_PLUGIN_ROOT}}: {cmd}"
                    )
                    # Resolve the referenced script path and confirm it exists + is executable.
                    rel = cmd.replace('"', "").replace("${CLAUDE_PLUGIN_ROOT}/", "").strip()
                    script = PLUGIN_ROOT / rel
                    assert script.exists(), f"{event} hook script not found: {script}"
                    mode = script.stat().st_mode
                    assert mode & stat.S_IXUSR, f"{event} hook script not executable: {script}"


class TestHookBehavior:
    """Run the UserPromptSubmit hook to confirm match / no-match behavior.

    The hook matches app mentions against a CLI-sourced cache that SessionStart
    maintains at ${TMPDIR}/composio-plugin-toolkits.cache. Each test controls
    that cache by pointing TMPDIR at an isolated tmp dir.
    """

    SCRIPT = HOOKS_ROOT / "user-prompt-submit.sh"

    def _run(self, prompt: str, tmpdir, cache_entries=None):
        env = dict(os.environ, TMPDIR=str(tmpdir))
        cache = os.path.join(str(tmpdir), "composio-plugin-toolkits.cache")
        if cache_entries is not None:
            with open(cache, "w") as fh:
                fh.write("\n".join(cache_entries) + "\n")
        payload = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        return subprocess.run(
            ["bash", str(self.SCRIPT)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )

    def test_injects_on_toolkit_mention_from_cache(self, tmp_path):
        proc = self._run(
            "Please open a GitHub issue for this bug",
            tmp_path,
            cache_entries=["github", "slack", "gmail"],
        )
        assert proc.returncode == 0
        assert proc.stdout.strip(), "expected additionalContext on a toolkit mention"
        data = json.loads(proc.stdout)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        assert data["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert "composio" in ctx.lower()
        assert "composio:composio-cli" in ctx

    def test_no_injection_on_unrelated_prompt(self, tmp_path):
        proc = self._run(
            "Refactor this quicksort to be iterative",
            tmp_path,
            cache_entries=["github", "slack", "gmail"],
        )
        assert proc.returncode == 0
        assert proc.stdout.strip() == "", "must not inject on unrelated prompts"

    def test_fallback_intent_match_when_cache_absent(self, tmp_path):
        # No cache written: hook falls back to the minimal generic intent set.
        proc = self._run("Help me connect my account", tmp_path)
        assert proc.returncode == 0
        assert proc.stdout.strip(), "expected fallback intent match without a cache"

    def test_no_fallback_match_for_app_name_without_cache(self, tmp_path):
        # Without a cache, a bare app name must NOT match (only generic intent does).
        proc = self._run("Summarize my github activity", tmp_path)
        assert proc.returncode == 0
        assert proc.stdout.strip() == "", "app names require the CLI-sourced cache"

    def test_empty_prompt_is_safe(self, tmp_path):
        proc = self._run("", tmp_path, cache_entries=["github"])
        assert proc.returncode == 0


class TestSessionStartHook:
    """SessionStart must always emit valid JSON and exit 0, CLI present or not."""

    SCRIPT = HOOKS_ROOT / "session-start.sh"

    def test_emits_valid_json(self, tmp_path):
        env = dict(os.environ, TMPDIR=str(tmp_path))
        proc = subprocess.run(
            ["bash", str(self.SCRIPT)],
            input=json.dumps({"hook_event_name": "SessionStart"}),
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
        )
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert data["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert data["hookSpecificOutput"]["additionalContext"]
        # A static toolkit cache is seeded synchronously for UserPromptSubmit.
        cache = tmp_path / "composio-plugin-toolkits.cache"
        assert cache.exists(), "session-start should seed the toolkit cache"

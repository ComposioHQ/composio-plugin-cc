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
    """Run the UserPromptSubmit hook to confirm match / no-match behavior."""

    SCRIPT = HOOKS_ROOT / "user-prompt-submit.sh"

    def _run(self, prompt: str):
        payload = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        proc = subprocess.run(
            ["bash", str(self.SCRIPT)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc

    def test_injects_on_toolkit_mention(self):
        proc = self._run("Please open a GitHub issue for this bug")
        assert proc.returncode == 0
        assert proc.stdout.strip(), "expected additionalContext on a toolkit mention"
        data = json.loads(proc.stdout)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        assert data["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert "composio" in ctx.lower()

    def test_no_injection_on_unrelated_prompt(self):
        proc = self._run("Refactor this quicksort to be iterative")
        assert proc.returncode == 0
        assert proc.stdout.strip() == "", "must not inject on unrelated prompts"

    def test_empty_prompt_is_safe(self):
        proc = self._run("")
        assert proc.returncode == 0

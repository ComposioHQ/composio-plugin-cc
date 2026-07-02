"""Validate the hooks manifest and the SessionStart hook script."""
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

    def test_only_session_start_event(self):
        # Meta-search redesign: SessionStart is the only hook. In particular the
        # per-prompt UserPromptSubmit hook must be gone.
        assert set(self.hooks.keys()) == {"SessionStart"}, (
            f"hooks.json should define only SessionStart, found {sorted(self.hooks)}"
        )

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


class TestSessionStartHook:
    """SessionStart must always emit valid JSON with the meta-search guidance and
    the correct auth line, exit 0, and never seed a toolkit cache — CLI present,
    absent, signed-in, or not."""

    SCRIPT = HOOKS_ROOT / "session-start.sh"

    def _run(self, tmp_path, path=None):
        env = dict(os.environ, TMPDIR=str(tmp_path))
        if path is not None:
            env["PATH"] = path
        proc = subprocess.run(
            ["bash", str(self.SCRIPT)],
            input=json.dumps({"hook_event_name": "SessionStart"}),
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
        )
        assert proc.returncode == 0, proc.stderr
        data = json.loads(proc.stdout)
        assert data["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        return data["hookSpecificOutput"]["additionalContext"]

    def _fake_composio(self, tmp_path, exit_code: int, stdout: str = ""):
        """Create a throwaway PATH containing a fake `composio` whose `whoami`
        prints `stdout` and exits with `exit_code`. Sign-in must be decided by
        the exit code alone, independent of stdout."""
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        script = bindir / "composio"
        body = "#!/usr/bin/env bash\n"
        if stdout:
            body += f"echo {json.dumps(stdout)}\n"
        body += f"exit {exit_code}\n"
        script.write_text(body)
        script.chmod(0o755)
        # Keep the real toolchain (jq, bash, coreutils) available too.
        return f"{bindir}:{os.environ.get('PATH', '')}"

    def _assert_meta_search(self, ctx):
        low = ctx.lower()
        assert "composio search" in low, "must point at meta search (composio search)"
        assert "composio execute" in low, "must mention composio execute"
        assert "composio login" in low, "must reference the CLI (composio login installs the skill)"
        assert "no api key" not in low, "must not say 'no API keys'"

    def test_cli_present_signed_in(self, tmp_path):
        # Exit 0 => signed in.
        path = self._fake_composio(tmp_path, exit_code=0, stdout="user@example.com")
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        assert "You're signed in to Composio." in ctx

    def test_signed_in_is_exit_code_not_stdout(self, tmp_path):
        # Exit 0 with EMPTY stdout must still count as signed in — sign-in is
        # gated on the whoami exit code, never on stdout contents.
        path = self._fake_composio(tmp_path, exit_code=0, stdout="")
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        assert "You're signed in to Composio." in ctx

    def test_cli_present_not_signed_in(self, tmp_path):
        # Non-zero exit => not signed in.
        path = self._fake_composio(tmp_path, exit_code=1)
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        assert "composio login" in ctx

    def test_not_signed_in_even_with_stdout(self, tmp_path):
        # Non-zero exit must count as NOT signed in even if the CLI printed
        # something to stdout (e.g. an error banner).
        path = self._fake_composio(tmp_path, exit_code=1, stdout="Not logged in")
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        assert "composio login" in ctx

    def test_cli_absent(self, tmp_path):
        # Minimal PATH with the standard toolchain but no `composio` on it.
        bindir = tmp_path / "emptybin"
        bindir.mkdir()
        path = f"{bindir}:/usr/bin:/bin"
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        assert "composio.dev/install" in ctx, "CLI-absent line must give install instructions"

    def test_does_not_seed_toolkit_cache(self, tmp_path):
        # The old toolkit-name cache must no longer be created.
        self._run(tmp_path)
        cache = tmp_path / "composio-plugin-toolkits.cache"
        assert not cache.exists(), "session-start must not seed a toolkit cache anymore"

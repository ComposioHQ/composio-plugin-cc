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

    def test_exactly_session_start_and_user_prompt_submit(self):
        # The plugin ships exactly two hooks: SessionStart (standing note + cache
        # warm) and UserPromptSubmit (per-prompt nudge).
        assert set(self.hooks.keys()) == {"SessionStart", "UserPromptSubmit"}, (
            f"hooks.json should define SessionStart + UserPromptSubmit, found {sorted(self.hooks)}"
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
    the correct auth line, exit 0 — CLI present, absent, signed-in, or not — and
    warm the top-50 toolkit cache when the CLI is available."""

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

    def _fake_composio_with_toolkits(self, tmp_path):
        """Fake `composio` that answers `whoami` (exit 0) and emits a small
        popularity-ordered toolkit JSON array for `dev toolkits list`."""
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        script = bindir / "composio"
        toolkits = [
            {"slug": "gmail", "name": "Gmail"},
            {"slug": "github", "name": "GitHub"},
            {"slug": "googlecalendar", "name": "Google Calendar"},
        ]
        body = (
            "#!/usr/bin/env bash\n"
            'if [ "$1" = "dev" ] && [ "$2" = "toolkits" ]; then\n'
            f"  cat <<'EOF'\n{json.dumps(toolkits)}\nEOF\n"
            "  exit 0\n"
            "fi\n"
            "exit 0\n"  # whoami and anything else: signed in
        )
        script.write_text(body)
        script.chmod(0o755)
        return f"{bindir}:{os.environ.get('PATH', '')}"

    def test_warms_toolkit_cache_when_cli_present(self, tmp_path):
        # With a working CLI, session-start must write a non-empty cache of
        # lowercased slugs + names for UserPromptSubmit to read.
        path = self._fake_composio_with_toolkits(tmp_path)
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        cache = tmp_path / "composio-plugin-toolkits.cache"
        assert cache.exists(), "session-start must warm the toolkit cache"
        tokens = cache.read_text().splitlines()
        assert "gmail" in tokens and "github" in tokens, (
            f"cache should hold lowercased slugs, got {tokens}"
        )
        assert "google calendar" in tokens, "multi-word display names should be cached lowercased"

    def test_cli_absent_does_not_write_cache(self, tmp_path):
        # No CLI -> nothing to source; leave the cache untouched, never crash.
        bindir = tmp_path / "emptybin"
        bindir.mkdir()
        path = f"{bindir}:/usr/bin:/bin"
        self._run(tmp_path, path=path)
        cache = tmp_path / "composio-plugin-toolkits.cache"
        assert not cache.exists(), "no cache should be written when the CLI is absent"


class TestUserPromptSubmitHook:
    """UserPromptSubmit nudges (single-line, via additionalContext) when a prompt
    mentions a toolkit or an action-intent verb; is silent otherwise; reads the
    SessionStart-warmed cache; never touches the network; always exits 0."""

    SCRIPT = HOOKS_ROOT / "user-prompt-submit.sh"

    def _run(self, tmp_path, prompt, cache=None):
        env = dict(os.environ, TMPDIR=str(tmp_path))
        if cache is not None:
            (tmp_path / "composio-plugin-toolkits.cache").write_text(cache)
        proc = subprocess.run(
            ["bash", str(self.SCRIPT)],
            input=json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": prompt}),
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
        )
        assert proc.returncode == 0, proc.stderr
        return proc.stdout

    def _ctx(self, out):
        data = json.loads(out)
        assert data["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        ctx = data["hookSpecificOutput"]["additionalContext"]
        # The nudge must be a single line and must never leak an auth error.
        assert "\n" not in ctx.strip(), f"nudge must be one line: {ctx!r}"
        assert "no api key" not in ctx.lower()
        assert "composio search" in ctx.lower()
        return ctx

    def test_toolkit_token_matches(self, tmp_path):
        # No cache -> static fallback contains github.
        out = self._run(tmp_path, "open a github issue")
        self._ctx(out)

    def test_action_verb_matches(self, tmp_path):
        out = self._run(tmp_path, "connect my account")
        self._ctx(out)

    def test_unrelated_prompt_is_silent(self, tmp_path):
        out = self._run(tmp_path, "refactor this python function")
        assert out.strip() == "", f"unrelated prompt must produce no output, got {out!r}"

    def test_reads_cache_not_just_fallback(self, tmp_path):
        # A made-up token present only in the cache must trigger a match, proving
        # the hook reads the cache rather than only the static fallback.
        token = "zzzcustomtoolkit"
        out = self._run(tmp_path, f"please use {token} for this", cache=f"{token}\n")
        self._ctx(out)

    def test_cache_token_absent_from_fallback_is_silent_without_cache(self, tmp_path):
        # Same made-up token, but no cache present -> not in the static fallback -> silent.
        out = self._run(tmp_path, "please use zzzcustomtoolkit for this")
        assert out.strip() == "", f"expected silence without cache, got {out!r}"

"""Validate the hooks manifest and the SessionStart hook script."""
import json
import os
import shlex
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

    def _run(self, tmp_path, path=None, timeout=20):
        env = dict(os.environ, TMPDIR=str(tmp_path))
        if path is not None:
            env["PATH"] = path
        proc = subprocess.run(
            ["bash", str(self.SCRIPT)],
            input=json.dumps({"hook_event_name": "SessionStart"}),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        assert proc.returncode == 0, proc.stderr
        data = json.loads(proc.stdout)
        assert data["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        return data["hookSpecificOutput"]["additionalContext"]

    def _fake_composio(
        self,
        tmp_path,
        exit_code: int,
        stdout: str = "",
        stderr: str = "",
        hang_whoami: bool = False,
    ):
        """Create a fake `composio` with configurable `whoami` behavior."""
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        script = bindir / "composio"
        body = "#!/usr/bin/env bash\n"
        if hang_whoami:
            body += 'if [ "${1:-}" = "whoami" ]; then exec sleep 30; fi\n'
        if stdout:
            body += f"printf '%s\\n' {shlex.quote(stdout)}\n"
        if stderr:
            body += f"printf '%s\\n' {shlex.quote(stderr)} >&2\n"
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

    def _assert_signed_in(self, ctx):
        assert "You're signed in to Composio." in ctx
        assert "Run `composio login` to connect." not in ctx

    def _assert_signed_out(self, ctx):
        assert "Run `composio login` to connect." in ctx
        assert "You're signed in to Composio." not in ctx

    def test_old_human_readable_output_is_signed_in(self, tmp_path):
        # Older CLIs emitted account data without an explicit auth boolean.
        path = self._fake_composio(tmp_path, exit_code=0, stdout="user@example.com")
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        self._assert_signed_in(ctx)

    def test_fast_cli_does_not_wait_for_timeout_watchdogs(self, tmp_path):
        path = self._fake_composio(tmp_path, exit_code=0, stdout="user@example.com")
        ctx = self._run(tmp_path, path=path, timeout=2)
        self._assert_signed_in(ctx)

    def test_slow_whoami_is_bounded(self, tmp_path):
        path = self._fake_composio(tmp_path, exit_code=0, hang_whoami=True)
        ctx = self._run(tmp_path, path=path, timeout=5)
        self._assert_signed_out(ctx)

    def test_exit_zero_with_empty_output_is_not_signed_in(self, tmp_path):
        # Published CLI 0.2.31 exits 0 with empty output when unauthenticated.
        path = self._fake_composio(tmp_path, exit_code=0, stdout="")
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        self._assert_signed_out(ctx)

    def test_exit_zero_with_whitespace_only_output_is_not_signed_in(self, tmp_path):
        path = self._fake_composio(tmp_path, exit_code=0, stdout=" \t")
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        self._assert_signed_out(ctx)

    def test_exit_zero_with_logged_out_warning_is_not_signed_in(self, tmp_path):
        path = self._fake_composio(
            tmp_path,
            exit_code=0,
            stderr="You are not logged in yet. Please run `composio login`.",
        )
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        self._assert_signed_out(ctx)

    def test_exit_zero_with_unauthenticated_json_is_not_signed_in(self, tmp_path):
        path = self._fake_composio(
            tmp_path,
            exit_code=0,
            stdout=json.dumps({"authenticated": False, "email": None}),
        )
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        self._assert_signed_out(ctx)

    def test_new_authenticated_json_is_signed_in(self, tmp_path):
        path = self._fake_composio(
            tmp_path,
            exit_code=0,
            stdout=json.dumps(
                {"authenticated": True, "account_type": "human", "email": "user@example.com"}
            ),
        )
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        self._assert_signed_in(ctx)

    def test_old_authenticated_json_is_signed_in(self, tmp_path):
        path = self._fake_composio(
            tmp_path,
            exit_code=0,
            stdout=json.dumps({"account_type": "agent", "email": "agent@example.com"}),
        )
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        self._assert_signed_in(ctx)

    def test_cli_present_not_signed_in(self, tmp_path):
        # Non-zero exit => not signed in.
        path = self._fake_composio(tmp_path, exit_code=1)
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        self._assert_signed_out(ctx)

    def test_not_signed_in_even_with_stdout(self, tmp_path):
        # Non-zero exit must count as NOT signed in even if the CLI printed
        # something to stdout (e.g. an error banner).
        path = self._fake_composio(tmp_path, exit_code=1, stdout="Not logged in")
        ctx = self._run(tmp_path, path=path)
        self._assert_meta_search(ctx)
        self._assert_signed_out(ctx)

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
            "printf '%s\\n' '{\"account_type\":\"agent\",\"email\":\"agent@example.com\"}'\n"
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
    NAMES a toolkit from the SessionStart-warmed top-50 cache — and ONLY then. No
    generic verbs, no static fallback: a cold cache means silence. Never touches
    the network; always exits 0."""

    # A representative warmed cache (what SessionStart writes: one lowercased
    # slug/name per line).
    CACHE = "gmail\ngithub\nslack\nnotion\nlinear\ngooglecalendar\ngoogle calendar\n"

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

    def test_cached_toolkit_matches(self, tmp_path):
        # Prompt names a toolkit present in the warmed cache -> fires.
        out = self._run(tmp_path, "open a github issue", cache=self.CACHE)
        self._ctx(out)

    def test_cached_multiword_toolkit_matches(self, tmp_path):
        out = self._run(tmp_path, "add an event to my google calendar", cache=self.CACHE)
        self._ctx(out)

    def test_prompt_naming_nothing_cached_is_silent(self, tmp_path):
        # Cache is warm but the prompt names no cached toolkit -> silent.
        out = self._run(tmp_path, "refactor this python function", cache=self.CACHE)
        assert out.strip() == "", f"non-toolkit prompt must be silent, got {out!r}"

    def test_bare_action_verb_is_silent(self, tmp_path):
        # Generic verbs must NOT fire (they collide with coding vocab and over-inject);
        # they are not toolkit names, so even with a warm cache they stay silent.
        for prompt in (
            "connect to the local postgres database",
            "the issue is on line 42",
            "post the results to the console",
            "write an email validation regex",
        ):
            out = self._run(tmp_path, prompt, cache=self.CACHE)
            assert out.strip() == "", f"bare verb must be silent, but fired on: {prompt!r}"

    def test_cold_cache_is_always_silent(self, tmp_path):
        # No cache present -> nothing to match against -> silent even for a real app name.
        out = self._run(tmp_path, "open a github issue")
        assert out.strip() == "", f"cold cache must be silent, got {out!r}"

    def test_reads_the_cache(self, tmp_path):
        # A made-up token present only in the cache must fire, proving the hook
        # matches against the cache contents (not a hardcoded list).
        token = "zzzcustomtoolkit"
        out = self._run(tmp_path, f"please use {token} for this", cache=f"{token}\n")
        self._ctx(out)

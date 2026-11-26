"""The SessionStart hook records agent compactions for the Composio CLI.

The file contract is "Agent compaction state" in the CLI README
(ComposioHQ/composio, ts/packages/cli/README.md).
"""
import json
import os
import pathlib
import shutil
import stat
import subprocess
import time

import pytest

from tests.config import HOOKS_ROOT

SCRIPT = HOOKS_ROOT / "session-start.sh"

SESSION_ID = "113a59a3-036e-453b-91c0-7462d7e1019e"
OUTER_ID = "0b6c0ad6-5a51-4a1e-9b0e-1f0f6c0e2d11"
TOOLS = ("bash", "cat", "tr", "sed", "head", "date", "mkdir", "touch", "find", "rm", "dirname", "grep", "sort", "tail")


def _env(home, path, extra=None):
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("COMPOSIO_AGENT_", "CLAUDE_", "CODEX_"))
    }
    env.update(HOME=str(home), TMPDIR=str(home), PATH=path)
    env.update(extra or {})
    return env


def _bin_without(home, excluded=()):
    """A PATH with only the tools the hook needs, so neither composio nor the
    host CLI runs, and jq only when asked."""
    bindir = pathlib.Path(home) / "toolbin"
    bindir.mkdir(exist_ok=True)
    for tool in TOOLS + ("jq",):
        target = shutil.which(tool)
        if tool in excluded or target is None or (bindir / tool).exists():
            continue
        (bindir / tool).symlink_to(target)
    return str(bindir)


def _compaction_file(home, session_id=SESSION_ID, host="claude"):
    return pathlib.Path(home) / ".composio" / "agent-compactions" / host / session_id


def _run(home, source, session_id=SESSION_ID, extra_env=None, excluded=()):
    env_file = pathlib.Path(home) / "claude-env"
    env = _env(home, _bin_without(home, excluded), {"CLAUDE_ENV_FILE": str(env_file), **(extra_env or {})})
    payload = {"hook_event_name": "SessionStart", "source": source, "session_id": session_id}
    proc = subprocess.run(
        ["bash", str(SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=20,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    # stdout stays the hook's JSON and nothing else.
    assert json.loads(proc.stdout)["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    return env_file.read_text() if env_file.exists() else ""


@pytest.mark.parametrize("excluded", [(), ("jq",)], ids=["with-jq", "without-jq"])
def test_startup_creates_an_empty_file_and_exports_the_pair(tmp_path, excluded):
    exported = _run(tmp_path, "startup", excluded=excluded)
    file = _compaction_file(tmp_path)
    assert file.read_text() == ""
    assert stat.S_IMODE(file.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(file.parent.parent.stat().st_mode) == 0o700
    assert exported == (
        "export COMPOSIO_AGENT_HOST=claude\n"
        f"export COMPOSIO_AGENT_SESSION_ID={SESSION_ID}\n"
    )


@pytest.mark.parametrize("excluded", [(), ("jq",)], ids=["with-jq", "without-jq"])
def test_each_compaction_appends_one_line_and_resume_keeps_them(tmp_path, excluded):
    _run(tmp_path, "startup", excluded=excluded)
    _run(tmp_path, "compact", excluded=excluded)
    _run(tmp_path, "resume", excluded=excluded)
    _run(tmp_path, "compact", excluded=excluded)
    lines = _compaction_file(tmp_path).read_text().splitlines()
    assert len(lines) == 2
    assert all(line.strip() for line in lines)


def test_a_fork_gets_its_own_empty_file(tmp_path):
    _run(tmp_path, "startup")
    _run(tmp_path, "compact")
    fork_id = "921d83f2-8b42-40ad-a2aa-588bd8a4931a"
    exported = _run(tmp_path, "fork", session_id=fork_id)
    assert _compaction_file(tmp_path, fork_id).read_text() == ""
    assert exported.endswith(f"export COMPOSIO_AGENT_SESSION_ID={fork_id}\n")


def test_an_inherited_pair_wins(tmp_path):
    exported = _run(
        tmp_path,
        "compact",
        extra_env={"COMPOSIO_AGENT_HOST": "claude", "COMPOSIO_AGENT_SESSION_ID": OUTER_ID},
    )
    assert len(_compaction_file(tmp_path, OUTER_ID).read_text().splitlines()) == 1
    assert not _compaction_file(tmp_path).exists()
    assert f"export COMPOSIO_AGENT_SESSION_ID={OUTER_ID}\n" in exported


@pytest.mark.parametrize(
    "session_id",
    ["", "../escape", "a/b", "id with space", "x" * 129, "abc\nexport EVIL=1"],
    ids=["empty", "dotdot", "slash", "space", "too-long", "newline"],
)
def test_an_unsafe_session_id_records_and_exports_nothing(tmp_path, session_id):
    exported = _run(tmp_path, "startup", session_id=session_id)
    assert exported == ""
    root = tmp_path / ".composio" / "agent-compactions"
    assert not root.exists() or not any(p.is_file() for p in root.rglob("*"))


def test_an_unknown_inherited_host_records_nothing(tmp_path):
    exported = _run(
        tmp_path,
        "startup",
        extra_env={"COMPOSIO_AGENT_HOST": "../x", "COMPOSIO_AGENT_SESSION_ID": OUTER_ID},
    )
    assert exported == ""
    assert not (tmp_path / ".composio" / "agent-compactions").exists()


def test_a_symlink_at_the_file_name_is_not_followed(tmp_path):
    target = tmp_path / "target"
    target.write_text("keep\n")
    file = _compaction_file(tmp_path)
    file.parent.mkdir(parents=True)
    file.symlink_to(target)
    _run(tmp_path, "compact")
    assert target.read_text() == "keep\n"


def test_startup_forgets_chats_untouched_for_90_days(tmp_path):
    old = _compaction_file(tmp_path, "old-chat")
    recent = _compaction_file(tmp_path, "recent-chat")
    old.parent.mkdir(parents=True)
    old.write_text("")
    recent.write_text("")
    long_ago = time.time() - 100 * 86400
    os.utime(old, (long_ago, long_ago))
    _run(tmp_path, "startup")
    assert not old.exists()
    assert recent.exists()
    assert _compaction_file(tmp_path).exists()

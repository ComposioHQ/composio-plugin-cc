"""Validate slash-command files."""
import re

from tests.config import EXPECTED_COMMANDS
from tests.skill import discover_commands


class TestCommands:
    def setup_method(self):
        self.commands = discover_commands()
        self.by_name = {c.metadata.name: c for c in self.commands}

    def test_expected_commands_exist(self):
        for expected in EXPECTED_COMMANDS:
            assert expected in self.by_name, (
                f"missing command '{expected}'; have {sorted(self.by_name)}"
            )

    def test_each_command_has_description(self):
        for cmd in self.commands:
            assert len(cmd.metadata.description) > 10, f"{cmd.path}: needs a description"

    def test_each_command_shells_to_composio(self):
        for cmd in self.commands:
            assert re.search(r"\bcomposio\b", cmd.body), (
                f"{cmd.path}: thin command should reference the composio CLI"
            )

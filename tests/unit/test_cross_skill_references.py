import re

from tests.config import COMMANDS_ROOT, PLUGIN_NAME, SKILLS_ROOT
from tests.skill import discover_commands, discover_skills


class TestCrossSkillReferences:
    """Validate `plugin:skill` references across skills and commands resolve."""

    def setup_method(self):
        self.skills = discover_skills()
        self.commands = discover_commands()
        self.skill_names = {skill.metadata.name for skill in self.skills}

    def test_references_target_real_skills(self):
        pattern = re.compile(rf"`{re.escape(PLUGIN_NAME)}:([a-z0-9-]+)`")
        for doc in (*self.skills, *self.commands):
            for target in pattern.findall(doc.body):
                assert target in self.skill_names, (
                    f"{doc.path} references unknown skill `{PLUGIN_NAME}:{target}`; "
                    f"have {sorted(self.skill_names)}"
                )

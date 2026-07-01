"""Discover and parse plugin skill / command files with YAML frontmatter."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import yaml

from tests.config import COMMANDS_ROOT, SKILLS_ROOT


@dataclasses.dataclass
class Metadata:
    name: str
    description: str
    argument_hint: str | None = None


@dataclasses.dataclass
class Doc:
    metadata: Metadata
    body: str
    path: Path
    content: str

    @classmethod
    def from_path(cls, path: Path, name_fallback: str = "") -> "Doc":
        content = path.read_text()
        frontmatter: dict = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
        return cls(
            metadata=Metadata(
                name=frontmatter.get("name", name_fallback),
                description=frontmatter.get("description", ""),
                argument_hint=frontmatter.get("argument-hint"),
            ),
            body=body,
            path=path,
            content=content,
        )


# Skills use `metadata.name` == directory name convention, so no fallback.
Skill = Doc


def discover_skills() -> tuple[Doc, ...]:
    skills = []
    if not SKILLS_ROOT.is_dir():
        return ()
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            skills.append(Doc.from_path(skill_file))
    return tuple(skills)


def discover_commands() -> tuple[Doc, ...]:
    commands = []
    if not COMMANDS_ROOT.is_dir():
        return ()
    for cmd_file in sorted(COMMANDS_ROOT.glob("*.md")):
        commands.append(Doc.from_path(cmd_file, name_fallback=cmd_file.stem))
    return tuple(commands)

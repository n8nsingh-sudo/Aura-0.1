"""Aura Skills System - Plugin-based capabilities extension."""

from typing import Any, Callable
from pathlib import Path
import importlib
import json


class Skill:
    """Base class for Aura skills."""

    name: str = "base"
    description: str = "Base skill"
    commands: list[str] = []

    def run(self, command: str, args: dict = None) -> str:
        """Run a skill command."""
        raise NotImplementedError

    def help(self) -> str:
        """Return help text."""
        return f"{self.name}: {self.description}"


class SkillsRegistry:
    """Registry for managing skills."""

    def __init__(self, skills_dir: Path = None):
        self.skills: dict[str, Skill] = {}
        self._commands: dict[str, tuple[str, Callable]] = {}

        if skills_dir is None:
            skills_dir = Path(__file__).parent / "builtin"

        self.skills_dir = skills_dir
        self._load_builtin_skills()

    def _load_builtin_skills(self):
        """Load all built-in skills."""
        # Direct import - works better than dynamic
        try:
            from aura.skills.builtin import weather, github, system, files

            self.register_skill(weather)
            self.register_skill(github)
            self.register_skill(system)
            self.register_skill(files)
            print(f"✅ Loaded {len(self.skills)} skills")
        except Exception as e:
            print(f"Error loading skills: {e}")

    def register_skill(self, skill: Skill):
        """Register a skill."""
        self.skills[skill.name] = skill
        for cmd in skill.commands:
            self._commands[cmd] = (skill.name, skill.run)

    def get(self, name: str) -> Skill:
        """Get a skill by name."""
        return self.skills.get(name)

    def list(self) -> list[dict]:
        """List all available skills."""
        return [
            {"name": s.name, "description": s.description, "commands": s.commands}
            for s in self.skills.values()
        ]

    def execute(self, command: str, args: dict = None) -> str:
        """Execute a command across all skills."""
        if command in self._commands:
            skill_name, handler = self._commands[command]
            return handler(command, args or {})

        # Try each skill's match
        for skill in self.skills.values():
            if command in skill.commands:
                return skill.run(command, args or {})

        return f"Unknown command: {command}"


def create_skills_registry() -> SkillsRegistry:
    """Create and initialize the skills registry."""
    return SkillsRegistry()

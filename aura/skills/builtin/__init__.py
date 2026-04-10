"""Built-in skills for Aura."""

from aura.skills.builtin.weather import skill as weather
from aura.skills.builtin.github import skill as github
from aura.skills.builtin.system import skill as system
from aura.skills.builtin.files import skill as files

__all__ = ["weather", "github", "system", "files"]

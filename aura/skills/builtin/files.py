"""Files skill - File operations and search."""

import os
import subprocess
from pathlib import Path
from aura.skills import Skill


class FilesSkill(Skill):
    """File operations, search, and management."""

    name = "files"
    description = "File search, operations, and management"
    commands = ["files", "find", "search", "grep", "cat", "tree"]

    def run(self, command: str, args: dict = None) -> str:
        args = args or {}
        path = args.get("path", "")
        pattern = args.get("pattern", "")

        if command == "find":
            return self._find_files(path, pattern)
        elif command == "grep":
            return self._grep(path, pattern, args.get("query", ""))
        elif command == "cat":
            return self._cat(path)
        elif command == "tree":
            return self._tree(path, args.get("depth", 2))

        return self.help_text()

    def _find_files(self, path: str, pattern: str) -> str:
        """Find files by name pattern."""
        if not path:
            path = str(Path.home())
        if not pattern:
            return "Usage: files find <path> <pattern>"

        try:
            result = subprocess.run(
                ["find", path, "-name", f"*{pattern}*", "-type", "f"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            files = result.stdout.strip().split("\n")[:20]
            if files and files[0]:
                return f"Found {len(files)} files:\n" + "\n".join(files[:10])
            return "No files found"
        except Exception as e:
            return f"Error: {e}"

    def _grep(self, path: str, pattern: str, query: str) -> str:
        """Search file contents."""
        if not path or not query:
            return "Usage: files grep <path> <pattern> <query>"

        try:
            result = subprocess.run(
                ["grep", "-r", "--include=" + pattern, query, path, "-l"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            files = result.stdout.strip().split("\n")[:10]
            if files and files[0]:
                return f"Found in {len(files)} files:\n" + "\n".join(files)
            return "No matches found"
        except Exception as e:
            return f"Error: {e}"

    def _cat(self, path: str) -> str:
        """Read file contents."""
        if not path:
            return "Usage: files cat <path>"

        try:
            with open(path, "r") as f:
                content = f.read(2000)
            return content
        except Exception as e:
            return f"Error: {e}"

    def _tree(self, path: str, depth: int = 2) -> str:
        """Show directory tree."""
        if not path:
            path = str(Path.home())

        try:
            result = subprocess.run(
                ["tree", "-L", str(depth), path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout[:2000]
            return f"Found in {path}:"
        except FileNotFoundError:
            # Fallback to ls
            try:
                p = Path(path)
                items = list(p.iterdir())[:20]
                lines = [f"Contents of {path}:"]
                for item in items:
                    suffix = "/" if item.is_dir() else ""
                    lines.append(f"  {item.name}{suffix}")
                return "\n".join(lines)
            except Exception as e:
                return f"Error: {e}"

    def help_text(self) -> str:
        return """Files Skill:
  files find <path> <pattern> - Find files
  files grep <path> <ext> <query> - Search contents
  files cat <path> - Read file
  files tree <path> - Show directory"""


skill = FilesSkill()

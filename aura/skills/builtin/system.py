"""System skill - System information and control."""

import platform
import subprocess
import os
from aura.skills import Skill


class SystemSkill(Skill):
    """Get system information and perform system actions."""

    name = "system"
    description = "System info, processes, notifications"
    commands = ["system", "sysinfo", "process", "kill", "notify"]

    def run(self, command: str, args: dict = None) -> str:
        args = args or {}

        if command in ["system", "sysinfo"]:
            return self._get_sysinfo()
        elif command == "notify":
            return self._notify(args.get("message", ""))

        return self.help_text()

    def _get_sysinfo(self) -> str:
        """Get system information."""
        try:
            return (
                f"System Info:\n"
                f"OS: {platform.system()} {platform.release()}\n"
                f"Machine: {platform.machine()}\n"
                f"Processor: {platform.processor()}\n"
                f"Python: {platform.python_version()}\n"
                f"Home: {os.path.expanduser('~')}"
            )
        except Exception as e:
            return f"Error: {e}"

    def _notify(self, message: str) -> str:
        """Send notification."""
        if not message:
            return "Usage: system notify <message>"

        try:
            if platform.system() == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'display notification "{message}" with title "Aura"',
                    ]
                )
            elif platform.system() == "Linux":
                subprocess.run(["notify-send", "Aura", message])
            return "Notification sent"
        except Exception as e:
            return f"Error: {e}"

    def help_text(self) -> str:
        return """System Skill:
  system sysinfo - System information
  system notify <message> - Send notification"""


skill = SystemSkill()

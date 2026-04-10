"""GitHub skill - GitHub operations via gh CLI."""

import subprocess
import json
from aura.skills import Skill


class GitHubSkill(Skill):
    """GitHub operations using gh CLI."""

    name = "github"
    description = "GitHub issues, PRs, CI runs, code review"
    commands = ["github", "gh", "issue", "pr"]

    def run(self, command: str, args: dict = None) -> str:
        args = args or {}
        action = args.get("action", "")
        repo = args.get("repo", "")
        number = args.get("number", "")

        if action in ["issue", "issues"]:
            return self._handle_issues(action, repo, number)
        elif action in ["pr", "prs"]:
            return self._handle_prs(action, repo, number)
        elif action == "status":
            return self._gh_status()

        return self.help_text()

    def _gh_status(self) -> str:
        """Check gh CLI and auth status."""
        try:
            result = subprocess.run(
                ["gh", "status", "-f", "{{.Username}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return "Logged in as: " + result.stdout.strip()
            return "Not logged in to GitHub"
        except FileNotFoundError:
            return "gh CLI not installed"
        except Exception as e:
            return "Error: " + str(e)

    def _handle_issues(self, action: str, repo: str, number: str) -> str:
        """Handle issue commands."""
        if not repo:
            return "Usage: github issue <owner/repo> <number>"

        if action == "issue" and number:
            try:
                result = subprocess.run(
                    [
                        "gh",
                        "issue",
                        "view",
                        number,
                        "--repo",
                        repo,
                        "--json",
                        "title,state,url",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return f"Issue #{number}: {data.get('title')}, {data.get('state')}"
                return f"Issue #{number} not found"
            except Exception as e:
                return f"Error: {e}"

        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--repo",
                    repo,
                    "--limit",
                    "5",
                    "--json",
                    "number,title,state",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                lines = [f"Issues in {repo}:"]
                for issue in data:
                    lines.append(
                        f"  #{issue['number']} [{issue['state']}] {issue['title']}"
                    )
                return "\n".join(lines)
            return "No issues found"
        except Exception as e:
            return f"Error: {e}"

    def _handle_prs(self, action: str, repo: str, number: str) -> str:
        """Handle PR commands."""
        if not repo:
            return "Usage: github pr <owner/repo> <number>"

        if action == "pr" and number:
            try:
                result = subprocess.run(
                    [
                        "gh",
                        "pr",
                        "view",
                        number,
                        "--repo",
                        repo,
                        "--json",
                        "title,state,url",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return f"PR #{number}: {data.get('title')}, {data.get('state')}"
                return f"PR #{number} not found"
            except Exception as e:
                return f"Error: {e}"

        try:
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--repo",
                    repo,
                    "--limit",
                    "5",
                    "--json",
                    "number,title,state",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                lines = [f"PRs in {repo}:"]
                for pr in data:
                    lines.append(f"  #{pr['number']} [{pr['state']}] {pr['title']}")
                return "\n".join(lines)
            return "No PRs found"
        except Exception as e:
            return f"Error: {e}"

    def help_text(self) -> str:
        return """GitHub Skill:
  github status - Check gh auth status
  github issue <repo> - List issues
  github pr <repo> - List PRs"""


skill = GitHubSkill()

import subprocess
import tempfile
import os
import sys
from pathlib import Path
from aura import config


class DockerSandbox:
    def __init__(self):
        self.docker_available = self._check_docker()
        if self.docker_available:
            print("Docker sandbox ready (secure mode)")
        else:
            print("⚠️ Docker not available - using fallback execution (less secure)")

    def _check_docker(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def run_python(self, code: str) -> dict:
        if self.docker_available:
            return self._run_docker(code)
        else:
            return self._run_fallback(code)

    def _run_docker(self, code: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp_dir:
            code_file = Path(tmp_dir) / "script.py"
            code_file.write_text(code)

            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network=none",
                    "--memory=256m",
                    "--cpus=0.5",
                    f"--volume={tmp_dir}:/code:ro",
                    "python:3.11-slim",
                    "python",
                    "/code/script.py",
                ],
                capture_output=True,
                text=True,
                timeout=config.MAX_EXECUTION_TIME_SECONDS,
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "mode": "docker",
            }

    def _run_fallback(self, code: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp_dir:
            code_file = Path(tmp_dir) / "script.py"
            code_file.write_text(code)

            result = subprocess.run(
                [sys.executable, str(code_file)],
                capture_output=True,
                text=True,
                timeout=config.MAX_EXECUTION_TIME_SECONDS,
                cwd=tmp_dir,
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "mode": "fallback",
            }


def run_code_safely(code: str) -> dict:
    sandbox = DockerSandbox()
    return sandbox.run_python(code)


if __name__ == "__main__":
    result = run_code_safely("print('Hello from AURA!'); print(2 + 2)")
    print(f"Success: {result['success']}")
    print(f"Output: {result['stdout']}")
    print(f"Mode: {result.get('mode', 'unknown')}")

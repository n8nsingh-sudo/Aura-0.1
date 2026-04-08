from aura.action.sandbox import DockerSandbox
from aura.core.model_router import ModelRouter


class CodeExecutor:
    def __init__(self, router: ModelRouter):
        self.sandbox = DockerSandbox()
        self.router = router
        self.max_retries = 5

    def execute_task(self, task_description: str) -> dict:
        print(f"Code executor starting: {task_description[:80]}")

        for attempt in range(1, self.max_retries + 1):
            print(f"Attempt {attempt}/{self.max_retries}")

            code = self._generate_code(task_description, attempt)

            result = self.sandbox.run_python(code)

            if result["success"]:
                print("Code ran successfully")
                return {
                    "success": True,
                    "code": code,
                    "output": result["stdout"],
                    "attempts": attempt,
                }
            else:
                error_msg = (
                    result["stderr"][:300] if result["stderr"] else "Unknown error"
                )
                print(f"Code failed: {error_msg}")

                if "SyntaxError" in error_msg or "IndentationError" in error_msg:
                    fix_instruction = f"The code has a syntax error. Fix it and return ONLY the corrected Python code."
                elif "NameError" in error_msg:
                    fix_instruction = f"The code has a NameError (undefined variable). Fix it and return ONLY the corrected Python code."
                elif "TypeError" in error_msg:
                    fix_instruction = f"The code has a TypeError. Fix it and return ONLY the corrected Python code."
                elif "ZeroDivisionError" in error_msg:
                    fix_instruction = f"The code has a ZeroDivisionError. Fix it and return ONLY the corrected Python code."
                elif "IndexError" in error_msg:
                    fix_instruction = f"The code has an IndexError. Fix it and return ONLY the corrected Python code."
                elif "ModuleNotFoundError" in error_msg:
                    fix_instruction = f"The code uses an invalid import. Use only standard library modules and return ONLY the corrected Python code."
                else:
                    fix_instruction = f"The code failed with error: {error_msg}. Fix it and return ONLY the corrected Python code."

                task_description = (
                    f"Original task: {task_description}\n\n"
                    f"Error: {error_msg}\n\n"
                    f"{fix_instruction}"
                )

        return {
            "success": False,
            "final_error": result.get("stderr", "Unknown error"),
            "attempts": self.max_retries,
            "code": code,
        }

    def _generate_code(self, task: str, attempt: int) -> str:
        if attempt == 1:
            prompt = f"""You are a Python coder. Write code to solve this:

{task}

Requirements:
1. Use ONLY standard library (no pip packages)
2. Code must run without errors
3. Print output to stdout
4. Include error handling
5. Return ONLY the code, no explanations, no markdown

Example format:
print("result")
"""
        else:
            prompt = f"""Fix the Python code below. The previous attempt had errors.

Task: {task}

Write the corrected code. Use ONLY standard library.
Return ONLY the code, no explanations, no markdown."""

        response = self.router.think(prompt)

        code = response.strip()

        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]

        return code.strip()

    def can_handle(self, task: str) -> bool:
        task_lower = task.lower()
        indicators = [
            "write code",
            "create function",
            "implement",
            "calculate",
            "python",
            "program",
            "script",
            "algorithm",
            "fibonacci",
            "factorial",
            "sort",
            "search",
            "reverse",
            "convert",
            "sum of",
            "product of",
            "generate",
            "print numbers",
            "loop",
            "iterate",
            "def ",
            "class ",
        ]
        return any(ind in task_lower for ind in indicators)


def execute_code_task(router, task_description: str) -> dict:
    executor = CodeExecutor(router)
    if executor.can_handle(task_description):
        return executor.execute_task(task_description)
    return None

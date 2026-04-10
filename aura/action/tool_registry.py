from typing import Callable, Any
import httpx
import json
import os
import subprocess
import urllib.parse
from pathlib import Path
from aura.action.system_controller import (
    open_app,
    open_url,
    run_command,
    get_system_info,
    take_screenshot,
    search_web,
    play_youtube,
    get_weather,
    control_volume,
    get_ip,
    get_date,
    create_file,
    read_file,
    list_files,
)
from aura.action.brd_generator import generate_brd
from aura.skills import create_skills_registry

_skills_registry = None


def get_skills():
    global _skills_registry
    if _skills_registry is None:
        _skills_registry = create_skills_registry()
    return _skills_registry


class Tool:
    def __init__(self, name: str, description: str, function: Callable):
        self.name = name
        self.description = description
        self.function = function

    def call(self, **kwargs) -> Any:
        return self.function(**kwargs)


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self._register_default_tools()
        self._register_skills()

    def _register_skills(self):
        skills = get_skills()

        self.register(
            "list_skills",
            "List all available skills",
            lambda **_: "\n".join(
                [f"{s['name']}: {s['description']}" for s in skills.list()]
            ),
        )

        for s in skills.list():
            name = s["name"]

            def make_handler(skill_name):
                def handler(**kwargs):
                    skill = skills.get(skill_name)
                    if not skill:
                        return f"Skill {skill_name} not found"
                    return skill.run(skill_name, kwargs)

                return handler

            self.register(f"skill_{name}", f"Aura skill: {name}", make_handler(name))

    def register(self, name: str, description: str, function: Callable):
        self.tools[name] = Tool(name, description, function)

    def call(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return self.tools[tool_name].call(**kwargs)

    def list_tools(self) -> str:
        lines = ["Available tools:"]
        for name, tool in self.tools.items():
            lines.append(f"  - {name}: {tool.description}")
        return "\n".join(lines)

    def _register_default_tools(self):
        self.register(
            "read_file",
            "Read the contents of a file by path",
            lambda path: open(path).read(),
        )
        self.register(
            "write_file",
            "Write content to a file",
            lambda path, content: open(path, "w").write(content),
        )
        self.register(
            "list_dir",
            "List files in a directory",
            lambda path: str(list(Path(path).iterdir())),
        )
        self.register(
            "web_search",
            "Search the web for information using DuckDuckGo",
            self._web_search,
        )
        self.register("fetch_url", "Fetch content from a URL", self._fetch_url)
        self.register(
            "http_request",
            "Make HTTP requests (GET, POST, PUT, DELETE)",
            self._http_request,
        )
        self.register(
            "run_command", "Run a shell command and return output", self._run_command
        )
        self.register("get_weather", "Get weather for a city", get_weather)
        self.register("calculator", "Calculate a math expression", self._calculator)
        self.register("wikipedia", "Get summary from Wikipedia", self._wikipedia)
        self.register("news", "Get latest news by category", self._news)

        # System control (from Mark-XXX)
        self.register(
            "open_app", "Open an application (chrome, spotify, vscode, etc)", open_app
        )
        self.register("open_url", "Open a URL in browser", open_url)
        self.register("run_shell", "Run a shell command", run_command)
        self.register("system_info", "Get system information", get_system_info)
        self.register("screenshot", "Take a screenshot", take_screenshot)
        self.register("web_search", "Search the web", search_web)
        self.register("youtube", "Play YouTube video", play_youtube)
        self.register("volume", "Control volume (up, down, mute)", control_volume)
        self.register("get_ip", "Get public IP address", get_ip)
        self.register("get_date", "Get current date/time", get_date)
        self.register("create_file", "Create a file", create_file)
        self.register("read_file", "Read a file", read_file)
        self.register("list_files", "List files in directory", list_files)

    def _web_search(self, query: str, num_results: int = 5) -> dict:
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            response = httpx.get(ddg_url, timeout=10, verify=False)

            results = []
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")

            for result in soup.select(".result")[:num_results]:
                title = result.select_one(".result__title")
                snippet = result.select_one(".result__snippet")
                link = result.select_one("a.result__a")

                if title and link:
                    results.append(
                        {
                            "title": title.get_text(strip=True),
                            "url": link.get("href", ""),
                            "snippet": snippet.get_text(strip=True) if snippet else "",
                        }
                    )

            return {"success": True, "results": results, "query": query}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _fetch_url(self, url: str) -> dict:
        try:
            response = httpx.get(url, timeout=30, verify=False, follow_redirects=True)
            return {
                "success": True,
                "status": response.status_code,
                "content": response.text[:10000],
                "headers": dict(response.headers),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _http_request(
        self, method: str, url: str, data: dict = None, headers: dict = None
    ) -> dict:
        try:
            client = httpx.Client(timeout=30)

            req_headers = {"User-Agent": "AURA-Agent/1.0"}
            if headers:
                req_headers.update(headers)

            if method.upper() == "GET":
                response = client.get(url, headers=req_headers)
            elif method.upper() == "POST":
                response = client.post(url, json=data, headers=req_headers)
            elif method.upper() == "PUT":
                response = client.put(url, json=data, headers=req_headers)
            elif method.upper() == "DELETE":
                response = client.delete(url, headers=req_headers)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}

            return {
                "success": True,
                "status": response.status_code,
                "body": response.text[:5000],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_command(self, command: str, timeout: int = 30) -> dict:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:500],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_weather(self, city: str) -> dict:
        try:
            wttr_url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
            response = httpx.get(wttr_url, timeout=10)
            data = response.json()

            current = data.get("current_condition", [{}])[0]
            return {
                "success": True,
                "city": city,
                "temp": current.get("temp_C", "N/A"),
                "condition": current.get("weatherDesc", [{}])[0].get("value", "N/A"),
                "humidity": current.get("humidity", "N/A"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculator(self, expression: str) -> dict:
        try:
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return {"success": False, "error": "Invalid characters in expression"}

            result = eval(expression)
            return {"success": True, "expression": expression, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _wikipedia(self, query: str) -> dict:
        try:
            import wikipedia

            result = wikipedia.summary(query, sentences=2)
            return {"success": True, "result": result, "query": query}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _news(self, category: str = "general") -> dict:
        try:
            api_key = os.getenv("NEWSDATA_API_KEY", "")
            if not api_key:
                return {"success": False, "error": "NEWSDATA_API_KEY not set"}
            url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={category}&language=en"
            response = httpx.get(url, timeout=10)
            data = response.json()

            if data.get("results"):
                articles = []
                for article in data["results"][:5]:
                    articles.append(
                        {
                            "title": article.get("title", ""),
                            "description": article.get("description", "")[:200],
                        }
                    )
                return {"success": True, "articles": articles}
            return {"success": False, "error": "No news found"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def register_skills(registry: "ToolRegistry"):
    """Register skills as tools."""
    skills = get_skills()
    registry.register(
        "list_skills",
        "List all available skills",
        lambda: "\n".join([f"{s['name']}: {s['description']}" for s in skills.list()]),
    )
    registry.register(
        "skill_weather",
        "Get weather for a city",
        lambda city: (
            skills.get("weather").run("weather", {"city": city})
            if skills.get("weather")
            else "Not found"
        ),
    )
    registry.register(
        "skill_system",
        "Get system information",
        lambda: (
            skills.get("system").run("sysinfo", {})
            if skills.get("system")
            else "Not found"
        ),
    )
    registry.register(
        "skill_github",
        "GitHub operations",
        lambda action="", repo="", number="": (
            skills.get("github").run(
                action, {"action": action, "repo": repo, "number": number}
            )
            if skills.get("github")
            else "Not found"
        ),
    )


if __name__ == "__main__":
    tools = ToolRegistry()
    register_skills(tools)
    print(tools.list_tools())
    print("\n--- Test Weather Skill ---")
    print(tools.call("skill_weather", city="London"))

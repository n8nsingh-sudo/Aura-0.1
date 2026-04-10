import os
import json
from pathlib import Path
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


def use_local_llm() -> bool:
    """Check if local Ollama is available."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def get_gemini_key() -> str:
    """Get Gemini API key - only use if local LLM not available."""
    if use_local_llm():
        return ""

    env_key = os.getenv("GEMINI_API_KEY", "")
    if env_key:
        return env_key

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("gemini_api_key", "")
    return ""


def get_openai_key() -> str:
    env_key = os.getenv("OPENAI_API_KEY", "")
    if env_key:
        return env_key

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("openai_api_key", "")
    return ""


def get_anthropic_key() -> str:
    env_key = os.getenv("ANTHROPIC_API_KEY", "")
    if env_key:
        return env_key

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("anthropic_api_key", "")
    return ""


def call_local_llm(prompt: str, model: str = "qwen2.5-coder:14b") -> str:
    """Call local Ollama LLM."""
    try:
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        return f"Error calling local LLM: {e}"


def set_gemini_key(key: str):
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data["gemini_api_key"] = key
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

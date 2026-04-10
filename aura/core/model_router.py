import httpx
import json
from enum import Enum
from aura import config


class ModelTier(Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class ModelRouter:
    def __init__(self):
        self.local_available = False
        self._check_local_model()

    def _check_local_model(self):
        try:
            response = httpx.get(f"{config.LOCAL_MODEL_URL}/api/tags", timeout=3)
            if response.status_code == 200:
                self.local_available = True
                print(f"✓ Local model ready: {config.LOCAL_MODEL}")
        except Exception:
            print("⚠ Ollama not running. Will use cloud model.")
            self.local_available = False

    def get_available_local_models(self) -> list:
        try:
            response = httpx.get(f"{config.LOCAL_MODEL_URL}/api/tags", timeout=3)
            if response.status_code == 200:
                data = response.json()
                return [m.get("name") for m in data.get("models", [])]
            return []
        except:
            return []

    def set_local_model(self, model_name: str):
        config.LOCAL_MODEL = model_name
        self._check_local_model()
        
        # Persist to .env
        try:
            import os
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    lines = f.readlines()
                with open(env_path, "w") as f:
                    for line in lines:
                        if line.startswith("LOCAL_MODEL="):
                            f.write(f"LOCAL_MODEL={model_name}\n")
                        else:
                            f.write(line)
        except Exception as e:
            print(f"Failed to update .env: {e}")

    def think(self, prompt: str, tier: ModelTier = None) -> str:
        # Use MODEL_PROVIDER from config
        provider = config.MODEL_PROVIDER.lower()

        if provider == "local":
            if self.local_available:
                return self._call_local(prompt)
            else:
                # Fallback to cloud if local not available
                return self._call_openrouter(prompt)

        elif provider == "openrouter":
            return self._call_openrouter(prompt)

        elif provider == "anthropic":
            if config.ANTHROPIC_API_KEY:
                return self._call_anthropic(prompt)
            else:
                print("⚠ No Anthropic key, falling back to OpenRouter")
                return self._call_openrouter(prompt)

        elif provider == "openai":
            if config.OPENAI_API_KEY:
                return self._call_openai(prompt)
            else:
                print("⚠ No OpenAI key, falling back to OpenRouter")
                return self._call_openrouter(prompt)

        else:
            # Default: try local, then OpenRouter
            if self.local_available:
                return self._call_local(prompt)
            return self._call_openrouter(prompt)

    def _call_local(self, prompt: str) -> str:
        if not self.local_available:
            raise RuntimeError("Local model not available. Is Ollama running?")

        payload = {"model": config.LOCAL_MODEL, "prompt": prompt, "stream": False}

        response = httpx.post(
            f"{config.LOCAL_MODEL_URL}/api/generate", json=payload, timeout=120
        )

        data = response.json()
        return data.get("response", "")

    def _call_openrouter(self, prompt: str) -> str:
        if not config.OPENROUTER_API_KEY:
            raise RuntimeError(
                "OpenRouter API key not set. Set OPENROUTER_API_KEY in .env"
            )

        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/n8nsingh-sudo/Aura-0.1",
            "X-Title": "AURA AI Assistant",
        }

        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_anthropic(self, prompt: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def _call_openai(self, prompt: str) -> str:
        import openai

        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

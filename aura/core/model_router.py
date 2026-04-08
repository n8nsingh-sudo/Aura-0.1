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
                print(f"Local model ready: {config.LOCAL_MODEL}")
        except Exception:
            print("WARNING: Ollama is not running. Start it with: ollama serve")
            self.local_available = False

    def think(self, prompt: str, tier: ModelTier = ModelTier.LOCAL) -> str:
        if tier == ModelTier.LOCAL and self.local_available:
            return self._call_local(prompt)
        elif config.ANTHROPIC_API_KEY:
            return self._call_cloud(prompt)
        else:
            return self._call_local(prompt)

    def _call_local(self, prompt: str) -> str:
        if not self.local_available:
            raise RuntimeError("Local model not available. Is Ollama running?")

        payload = {"model": config.LOCAL_MODEL, "prompt": prompt, "stream": False}

        response = httpx.post(
            f"{config.LOCAL_MODEL_URL}/api/generate", json=payload, timeout=120
        )

        data = response.json()
        return data.get("response", "")

    def _call_cloud(self, prompt: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

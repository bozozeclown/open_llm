import requests
from typing import Dict, Any
from .base import AIModelIntegration

class OllamaIntegration(AIModelIntegration):
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self._models = None

    @property
    def model_name(self) -> str:
        return "Ollama"
    
    def generate(self, prompt: str, model: str = "llama2", **kwargs) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()["response"]
    
    def get_available_models(self) -> Dict[str, Any]:
        if self._models is None:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            self._models = {
                m["name"]: m for m in response.json()["models"]
            }
        return self._models
    
    def pull_model(self, model_name: str):
        """Download a model if not available locally"""
        response = requests.post(
            f"{self.base_url}/api/pull",
            json={"name": model_name}
        )
        return response.json()
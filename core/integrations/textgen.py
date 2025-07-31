import requests
from typing import Dict, Any

class TextGenIntegration(AIModelIntegration):
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    @property
    def model_name(self) -> str:
        return "text-generation-webui"
    
    def generate(self, prompt: str, **kwargs) -> str:
        response = requests.post(
            f"{self.base_url}/api/v1/generate",
            json={
                "prompt": prompt,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()["results"][0]["text"]
    
    def get_available_models(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/api/v1/model")
        return {
            "current": response.json()["model_name"],
            "available": self._get_model_list()
        }
    
    def _get_model_list(self) -> list:
        response = requests.get(f"{self.base_url}/api/v1/models")
        return response.json()["model_names"]
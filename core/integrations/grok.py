import requests
import time
from core.plugin import PluginBase, PluginMetadata
from typing import Dict, Any, List
from datetime import datetime

class Plugin(PluginBase):
    def get_metadata(self):
        return PluginMetadata(
            name="grok",
            version="0.3.0",
            required_config={
                "api_key": str,
                "rate_limit": int,
                "timeout": int
            },
            dependencies=["requests"],
            description="Grok AI API integration with batching"
        )

    def initialize(self):
        self.api_key = self.config["api_key"]
        self.rate_limit = self.config.get("rate_limit", 5)
        self.timeout = self.config.get("timeout", 10)
        self.last_calls = []
        self._initialized = True
        return True

    @property
    def supports_batching(self) -> bool:
        return True

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self._check_rate_limit():
            return {"error": "Rate limit exceeded"}

        try:
            self.last_calls.append(time.time())
            if isinstance(input_data["prompt"], list):
                return self._batch_execute(input_data)
            return self._single_execute(input_data)
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _single_execute(self, input_data: Dict) -> Dict:
        response = requests.post(
            "https://api.grok.ai/v1/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": input_data["prompt"],
                "max_tokens": input_data.get("max_tokens", 150)
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def _batch_execute(self, input_data: Dict) -> Dict:
        responses = []
        for prompt in input_data["prompt"]:
            responses.append(self._single_execute({"prompt": prompt}))
        return {"responses": responses}

    def _check_rate_limit(self):
        now = time.time()
        self.last_calls = [t for t in self.last_calls if t > now - 60]
        return len(self.last_calls) < self.rate_limit

    def health_check(self):
        return {
            "ready": self._initialized,
            "rate_limit": f"{len(self.last_calls)}/{self.rate_limit}",
            "last_call": self.last_calls[-1] if self.last_calls else None
        }
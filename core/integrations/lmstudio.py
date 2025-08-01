import requests
from core.plugin import PluginBase, PluginMetadata
from typing import Dict, Any, List
import time

class Plugin(PluginBase):
    def get_metadata(self):
        return PluginMetadata(
            name="lmstudio",
            version="0.4.0",
            required_config={
                "base_url": str,
                "timeout": int,
                "batch_support": bool
            },
            dependencies=["requests"],
            description="LM Studio local server with batching"
        )

    def initialize(self):
        self.base_url = self.config["base_url"].rstrip("/")
        self.timeout = self.config.get("timeout", 60)
        self._batch_support = self.config.get("batch_support", False)
        self._initialized = True
        return True

    @property
    def supports_batching(self) -> bool:
        return self._batch_support

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            if self.supports_batching and isinstance(input_data["prompt"], list):
                return self._batch_execute(input_data)
            return self._single_execute(input_data)
        finally:
            self._log_latency(start)

    def _single_execute(self, input_data: Dict) -> Dict:
        response = requests.post(
            f"{self.base_url}/v1/completions",
            json={
                "prompt": input_data["prompt"],
                "max_tokens": input_data.get("max_tokens", 200),
                **input_data.get("parameters", {})
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

    def _log_latency(self, start_time: float):
        self.context.monitor.LATENCY.labels("lmstudio").observe(time.time() - start_time)

    def health_check(self):
        base_status = super().health_check()
        try:
            resp = requests.get(f"{self.base_url}/v1/models", timeout=5)
            base_status["status"] = "online" if resp.ok else "offline"
        except requests.exceptions.RequestException:
            base_status["status"] = "offline"
        return base_status
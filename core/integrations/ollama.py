import requests
from core.plugin import PluginBase, PluginMetadata
from typing import Dict, Any, List
import time

class Plugin(PluginBase):
    def get_metadata(self):
        return PluginMetadata(
            name="ollama",
            version="0.5.0",
            required_config={
                "base_url": str,
                "default_model": str,
                "batch_size": int
            },
            dependencies=["requests"],
            description="Ollama with experimental batching"
        )

    def initialize(self):
        self.base_url = self.config["base_url"].rstrip("/")
        self.default_model = self.config.get("default_model", "llama2")
        self.batch_size = self.config.get("batch_size", 1)  # Default to no batching
        self._initialized = True
        return True

    @property
    def supports_batching(self) -> bool:
        return self.batch_size > 1

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
            f"{self.base_url}/api/generate",
            json={
                "model": input_data.get("model", self.default_model),
                "prompt": input_data["prompt"],
                "stream": False,
                **input_data.get("options", {})
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _batch_execute(self, input_data: Dict) -> Dict:
        # Note: Ollama doesn't natively support batching, so we parallelize
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            results = list(executor.map(
                lambda p: self._single_execute({"prompt": p}),
                input_data["prompt"]
            ))
        return {"responses": results}

    def _log_latency(self, start_time: float):
        self.context.monitor.LATENCY.labels("ollama").observe(time.time() - start_time)

    def health_check(self):
        base_status = super().health_check()
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            base_status.update({
                "status": "online" if resp.ok else "offline",
                "models": [m["name"] for m in resp.json().get("models", [])]
            })
        except requests.exceptions.RequestException:
            base_status["status"] = "offline"
        return base_status
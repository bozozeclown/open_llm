import requests
from core.plugin import PluginBase, PluginMetadata
from typing import Dict, Any, List
import time

class Plugin(PluginBase):
    def get_metadata(self):
        return PluginMetadata(
            name="textgen",
            version="0.4.0",
            required_config={
                "base_url": str,
                "api_key": str,
                "batch_size": int,
                "timeout": int
            },
            dependencies=["requests"],
            description="Text Generation WebUI API with batching"
        )

    def initialize(self):
        self.base_url = self.config["base_url"].rstrip("/")
        self.api_key = self.config["api_key"]
        self.batch_size = self.config.get("batch_size", 1)
        self.timeout = self.config.get("timeout", 30)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self._initialized = True
        return True

    @property
    def supports_batching(self) -> bool:
        return self.batch_size > 1

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        try:
            if self.supports_batching and isinstance(input_data["prompt"], list):
                return self._batch_execute(input_data)
            return self._single_execute(input_data)
        finally:
            self._log_latency(start_time)

    def _single_execute(self, input_data: Dict) -> Dict:
        response = requests.post(
            f"{self.base_url}/api/v1/generate",
            headers=self.headers,
            json={
                "prompt": input_data["prompt"],
                **input_data.get("parameters", {})
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def _batch_execute(self, input_data: Dict) -> Dict:
        """Execute multiple prompts as a batch"""
        responses = []
        prompts = input_data["prompt"]
        
        # Process in chunks of batch_size
        for i in range(0, len(prompts), self.batch_size):
            chunk = prompts[i:i + self.batch_size]
            response = requests.post(
                f"{self.base_url}/api/v1/generate_batch",  # Note: Your API must support this endpoint
                headers=self.headers,
                json={
                    "prompts": chunk,
                    **input_data.get("parameters", {})
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            responses.extend(response.json()["results"])
            
        return {"responses": responses}

    def _log_latency(self, start_time: float):
        self.context.monitor.LATENCY.labels("textgen").observe(time.time() - start_time)

    def health_check(self):
        base_status = super().health_check()
        try:
            resp = requests.get(f"{self.base_url}/api/v1/model", 
                             headers=self.headers,
                             timeout=5)
            base_status.update({
                "status": "online" if resp.ok else "offline",
                "model": resp.json().get("model_name", "unknown")
            })
        except requests.exceptions.RequestException:
            base_status["status"] = "offline"
        return base_status
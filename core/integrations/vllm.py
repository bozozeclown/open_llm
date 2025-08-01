from vllm import LLM, SamplingParams
from core.plugin import PluginBase, PluginMetadata
from typing import Dict, Any, List
import time

class Plugin(PluginBase):
    def get_metadata(self):
        return PluginMetadata(
            name="vllm",
            version="0.4.0",
            required_config={
                "model": str,
                "tensor_parallel_size": int,
                "gpu_memory_utilization": float,
                "max_batch_size": int
            },
            dependencies=["vllm>=0.2.0"],
            description="High-performance batched inference"
        )

    def initialize(self):
        try:
            self.llm = LLM(
                model=self.config["model"],
                tensor_parallel_size=self.config.get("tensor_parallel_size", 1),
                gpu_memory_utilization=self.config.get("gpu_memory_utilization", 0.9),
                max_num_batched_tokens=self.config.get("max_batch_size", 2560)
            )
            self.default_params = SamplingParams(
                temperature=0.8,
                top_p=0.95
            )
            self._initialized = True
            return True
        except Exception as e:
            self.logger.error(f"vLLM init failed: {str(e)}")
            return False

    @property
    def supports_batching(self) -> bool:
        return True

    def execute(self, input_data: Dict) -> Dict:
        start = time.time()
        try:
            params = self.default_params.copy()
            if "parameters" in input_data:
                params = SamplingParams(**input_data["parameters"])
            
            if isinstance(input_data["prompt"], list):
                outputs = self.llm.generate(input_data["prompt"], params)
                return {
                    "responses": [o.outputs[0].text for o in outputs]
                }
            else:
                output = self.llm.generate([input_data["prompt"]], params)
                return {"response": output[0].outputs[0].text}
        finally:
            self._log_latency(start)

    def _log_latency(self, start_time: float):
        self.context.monitor.LATENCY.labels("vllm").observe(time.time() - start_time)

    def health_check(self):
        status = super().health_check()
        status["gpu_utilization"] = self._get_gpu_stats()
        status["batch_capacity"] = self.llm.llm_engine.scheduler_config.max_num_batched_tokens
        return status
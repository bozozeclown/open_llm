from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from core.plugin import PluginBase, PluginMetadata
from typing import Dict, Any, List
import torch
import time

class Plugin(PluginBase):
    def get_metadata(self):
        return PluginMetadata(
            name="huggingface",
            version="0.5.0",
            required_config={
                "model_name": str,
                "device": str,
                "quantize": bool,
                "batch_size": int
            },
            dependencies=["transformers>=4.30.0", "torch"],
            description="HuggingFace Transformers with batching"
        )

    def initialize(self):
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config["model_name"],
                device_map="auto" if self.config["device"] == "auto" else None
            )
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config["model_name"]
            )
            if self.config.get("quantize", False):
                self.model = torch.quantization.quantize_dynamic(
                    self.model,
                    {torch.nn.Linear},
                    dtype=torch.qint8
                )
            self.batch_size = self.config.get("batch_size", 4)
            self._initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    @property
    def supports_batching(self) -> bool:
        return True

    def execute(self, input_data: Dict) -> Dict:
        start = time.time()
        try:
            if isinstance(input_data["prompt"], list):
                return self._batch_execute(input_data)
            return self._single_execute(input_data)
        finally:
            self._log_latency(start)

    def _single_execute(self, input_data: Dict) -> Dict:
        inputs = self.tokenizer(input_data["prompt"], return_tensors="pt").to(self.config["device"])
        outputs = self.model.generate(**inputs)
        return {"response": self.tokenizer.decode(outputs[0])}

    def _batch_execute(self, input_data: Dict) -> Dict:
        inputs = self.tokenizer(
            input_data["prompt"],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.config["device"])
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=input_data.get("max_tokens", 50),
            num_return_sequences=1,
            batch_size=self.batch_size
        )
        
        return {
            "responses": [
                self.tokenizer.decode(output, skip_special_tokens=True)
                for output in outputs
            ]
        }

    def _log_latency(self, start_time: float):
        self.context.monitor.LATENCY.labels("huggingface").observe(time.time() - start_time)
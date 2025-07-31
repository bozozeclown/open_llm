from huggingface_hub import InferenceClient
from typing import Dict, Any

class HFIntegration(AIModelIntegration):
    def __init__(self, api_key=None, endpoint=None):
        self.client = InferenceClient(
            endpoint or "https://api-inference.huggingface.co",
            token=api_key
        )
    
    @property
    def model_name(self) -> str:
        return "HuggingFace TGI"
    
    def generate(self, prompt: str, model: str = None, **kwargs) -> str:
        return self.client.text_generation(
            prompt,
            model=model,
            **kwargs
        )
    
    def get_available_models(self) -> Dict[str, Any]:
        return {
            "note": "For HF Inference API, specify model in generate() call"
        }
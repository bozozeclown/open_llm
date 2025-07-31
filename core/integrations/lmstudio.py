import requests

class LMStudioIntegration(AIModelIntegration):
    def __init__(self, base_url="http://localhost:1234"):
        self.base_url = base_url

    @property
    def model_name(self) -> str:
        return "LM Studio"
    
    def generate(self, prompt: str, **kwargs) -> str:
        response = requests.post(
            f"{self.base_url}/v1/completions",
            json={
                "prompt": prompt,
                "temperature": 0.7,
                **kwargs
            }
        )
        return response.json()["choices"][0]["text"]
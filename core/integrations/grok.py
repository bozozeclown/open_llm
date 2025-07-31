from groq import Groq

class GroqIntegration(AIModelIntegration):
    def __init__(self, api_key=None):
        self.client = Groq(api_key=api_key)

    @property
    def model_name(self) -> str:
        return "Groq"
    
    def generate(self, prompt: str, model="mixtral-8x7b-32768", **kwargs) -> str:
        completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            **kwargs
        )
        return completion.choices[0].message.content
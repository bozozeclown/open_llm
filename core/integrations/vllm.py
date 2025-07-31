from vllm import LLM, SamplingParams

class vLLMIntegration(AIModelIntegration):
    def __init__(self, model="codellama/CodeLlama-7b-hf", gpu_memory_utilization=0.9):
        self.llm = LLM(
            model=model,
            gpu_memory_utilization=gpu_memory_utilization
        )
        self.sampling_params = SamplingParams(temperature=0.7, max_tokens=256)

    @property
    def model_name(self) -> str:
        return "vLLM"
    
    def generate(self, prompt: str, **kwargs) -> str:
        outputs = self.llm.generate([prompt], self.sampling_params)
        return outputs[0].outputs[0].text
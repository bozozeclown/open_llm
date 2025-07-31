from transformers import pipeline
from typing import List, Dict
from shared.schemas import CompletionRequest

class CodeCompleter:
    def __init__(self, model_name="deepseek-coder-6.7b"):
        self.completion_pipeline = pipeline(
            "text-generation",
            model=model_name,
            device="cuda"  # Use "cpu" if no GPU
        )

    def generate_completions(self, request: CompletionRequest) -> Dict[str, List[str]]:
        """Generate code suggestions with context awareness"""
        prompt = self._build_prompt(request.context, request.cursor_context)
        outputs = self.completion_pipeline(
            prompt,
            num_return_sequences=3,
            max_new_tokens=50,
            temperature=0.7,
            stop_sequences=["\n\n"]
        )
        return {"completions": [o["generated_text"] for o in outputs]}

    def _build_prompt(self, context: str, cursor_context: str) -> str:
        """Structured prompt for code completion"""
        return f"""# Code Context:
{context}

# Cursor Position:
{cursor_context}

# Suggested Completion:"""
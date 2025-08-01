from typing import Dict, Any
import re
from shared.schemas import Response

class QualityValidator:
    def __init__(self, config: Dict[str, Any]):
        self.standards = config.get("quality_standards", {})
        self.compiled_rules = {
            "code_safety": re.compile(r"(eval\(|system\(|os\.popen)"),
            "min_complexity": float(self.standards.get("min_complexity", 0.3))
        }

    def validate(self, response: Response) -> Dict[str, Any]:
        """Run all quality checks"""
        checks = {
            "safety": self._check_code_safety(response.content),
            "complexity": self._check_complexity(response.content),
            "formatting": self._check_formatting(response.content)
        }
        
        return {
            "passed": all(checks.values()),
            "checks": checks,
            "original_response": response
        }

    def _check_code_safety(self, content: str) -> bool:
        """Block dangerous code patterns"""
        if "code" not in content:
            return True
        return not self.compiled_rules["code_safety"].search(content["code"])

    def _check_complexity(self, content: str) -> bool:
        """Ensure sufficient solution quality"""
        complexity = self._calculate_complexity(content)
        return complexity >= self.compiled_rules["min_complexity"]

    def _calculate_complexity(self, text: str) -> float:
        """Simple complexity heuristic (0-1 scale)"""
        lines = text.split('\n')
        return min(
            (len([l for l in lines if l.strip()]) * 0.1) +
            (len(re.findall(r"\b(for|while|def|class)\b", text)) * 0.3),
            1.0
        )

    def _check_formatting(self, content: str) -> bool:
        """Validate basic structure"""
        return bool(
            isinstance(content, (str, dict)) and 
            (not isinstance(content, dict) or "answer" in content)
        )
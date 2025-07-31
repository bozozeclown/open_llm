# core/analysis.py
import re
from enum import Enum

class ContentType(Enum):
    CODE_PYTHON = "code_python"
    CODE_CSHARP = "code_csharp"
    MATH_SYMBOLIC = "math_symbolic"
    TEXT_QUERY = "text_query"

class ContentAnalyzer:
    CODE_PATTERNS = {
        ContentType.CODE_PYTHON: [
            r'def\s+\w+\(.*\):',
            r'import\s+\w+'
        ],
        ContentType.CODE_CSHARP: [
            r'public\s+(class|interface)\s+\w+',
            r'using\s+\w+;'
        ]
    }
    
    def analyze(self, text: str) -> ContentType:
        for content_type, patterns in self.CODE_PATTERNS.items():
            if any(re.search(p, text) for p in patterns):
                return content_type
        return ContentType.TEXT_QUERY
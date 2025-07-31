from typing import Dict, List
from dataclasses import dataclass
import ast
import traceback

@dataclass
class DebugFrame:
    file: str
    line: int
    context: str
    variables: Dict[str, str]
    error: str

class CodeDebugger:
    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph
        self.error_patterns = self._load_error_patterns()

    def analyze_traceback(self, code: str, error: str) -> List[DebugFrame]:
        """Convert traceback into structured debug frames"""
        frames = []
        tb = traceback.extract_tb(error.__traceback__)
        
        for frame in tb:
            context = self._get_code_context(code, frame.lineno)
            frames.append(DebugFrame(
                file=frame.filename,
                line=frame.lineno,
                context=context,
                variables=self._extract_variables(frame.locals),
                error=str(error)
            ))
        
        return frames

    def suggest_fixes(self, frames: List[DebugFrame]) -> Dict[str, List[str]]:
        """Generate fix suggestions using knowledge graph"""
        suggestions = {}
        for frame in frames:
            error_key = self._match_error_pattern(frame.error)
            if error_key in self.error_patterns:
                suggestions[frame.line] = self._enhance_suggestions(
                    self.error_patterns[error_key],
                    frame.context
                )
        return suggestions

    def _get_code_context(self, code: str, line: int, window=3) -> str:
        lines = code.split('\n')
        start = max(0, line - window - 1)
        end = min(len(lines), line + window)
        return '\n'.join(lines[start:end])

    def _extract_variables(self, locals_dict: Dict) -> Dict[str, str]:
        return {k: repr(v)[:100] for k, v in locals_dict.items() if not k.startswith('_')}

    def _match_error_pattern(self, error: str) -> str:
        for pattern in self.error_patterns:
            if pattern in error:
                return pattern
        return "unknown"

    def _enhance_suggestions(self, base_suggestions: List[str], context: str) -> List[str]:
        enhanced = []
        for suggestion in base_suggestions:
            # Augment with knowledge graph matches
            related = self.kg.find_semantic_matches(context + " " + suggestion)[:2]
            if related:
                enhanced.append(f"{suggestion} (Related: {', '.join(r['content'] for r in related)})")
            else:
                enhanced.append(suggestion)
        return enhanced

    def _load_error_patterns(self) -> Dict[str, List[str]]:
        return {
            "IndexError": [
                "Check list length before accessing",
                "Verify array bounds"
            ],
            "KeyError": [
                "Check if key exists in dictionary",
                "Use dict.get() for safe access"
            ],
            # ... other patterns
        }
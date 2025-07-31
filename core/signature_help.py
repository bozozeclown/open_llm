import re
from typing import Dict, List, Optional
from shared.schemas import SignatureHelp

class SignatureProvider:
    def __init__(self):
        self.patterns = {
            "python": r"def\s+(\w+)\s*\((.*?)\)",
            "javascript": r"function\s+(\w+)\s*\((.*?)\)",
            "csharp": r"public\s+\w+\s+(\w+)\s*\((.*?)\)"
        }

    def get_signature_help(self, code: str, language: str, cursor_pos: int) -> Optional[SignatureHelp]:
        """Extract function signature at cursor position"""
        matches = self._find_function_defs(code, language)
        current_func = self._get_function_at_pos(matches, cursor_pos)
        
        if current_func:
            params = self._parse_parameters(current_func[1])
            return SignatureHelp(
                name=current_func[0],
                parameters=params,
                active_parameter=self._get_active_param(current_func[1], cursor_pos)
            )
        return None

    def _find_function_defs(self, code: str, language: str) -> List[tuple]:
        """Find all function definitions in code"""
        pattern = self.patterns.get(language, self.patterns["python"])
        return re.findall(pattern, code, re.DOTALL)

    def _get_function_at_pos(self, functions: List[tuple], cursor_pos: int) -> Optional[tuple]:
        """Find which function contains the cursor position"""
        # Simplified - in reality would need AST parsing
        for func in functions:
            # Check if cursor is within function bounds
            if func[2] <= cursor_pos <= func[3]:  # (start_pos, end_pos)
                return func
        return None

    def _parse_parameters(self, param_str: str) -> List[Dict[str, str]]:
        """Parse parameter string into structured format"""
        params = []
        for p in param_str.split(','):
            p = p.strip()
            if p:
                parts = p.split()
                params.append({
                    "name": parts[-1],
                    "type": parts[0] if len(parts) > 1 else "any"
                })
        return params

    def _get_active_param(self, param_str: str, cursor_pos: int) -> int:
        """Determine which parameter is active based on cursor position"""
        if not param_str:
            return 0
        commas = [m.start() for m in re.finditer(',', param_str)]
        for i, pos in enumerate(commas):
            if cursor_pos <= pos:
                return i
        return len(commas)
CODE_PATTERNS = {
    "list_comprehension": {
        "pattern": "[x for x in iterable if condition]",
        "transform": lambda match: {
            "template": match["pattern"],
            "variables": ["iterable", "condition"]
        }
    },
    "context_manager": {
        "pattern": "with expression as var:",
        "transform": lambda match: {
            "solution": f"with {match['expression']} as {match['var']}:"
        }
    }
}

class RuleEngine:
    @staticmethod
    def apply_pattern(code: str) -> Dict|None:
        """Match code against known patterns"""
        for pattern_name, pattern_data in CODE_PATTERNS.items():
            if pattern_data["pattern"] in code:
                return pattern_data["transform"](code)
        return None
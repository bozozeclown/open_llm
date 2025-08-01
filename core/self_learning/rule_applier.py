import ast
from typing import Dict, Any

class RuleApplier:
    @staticmethod
    def apply_learned_rules(code: str, rules: list) -> Dict[str, Any]:
        """Apply learned rules to code context"""
        try:
            tree = ast.parse(code)
            for rule in sorted(rules, key=lambda x: x['success_rate'], reverse=True):
                if RuleApplier._matches_pattern(tree, rule['template']):
                    return {
                        "solution": rule['template'],
                        "confidence": rule['success_rate'],
                        "source": "learned_rule"
                    }
        except SyntaxError:
            pass
        return {}

    @staticmethod
    def _matches_pattern(tree: ast.AST, template: str) -> bool:
        """Check if code matches rule pattern"""
        try:
            template_tree = ast.parse(template)
            return ast.dump(tree) == ast.dump(template_tree)
        except:
            return False
from typing import Dict, Any
from pathlib import Path
import json
import hashlib
from datetime import datetime
from ..knowledge.graph import KnowledgeGraph

class SelfLearningEngine:
    def __init__(self, context: ContextManager):
        self.context = context
        self.graph: KnowledgeGraph = context.graph
        self.learned_rules_path = Path("data/learned_rules.json")
        self._init_storage()

    def _init_storage(self):
        """Ensure learning storage exists"""
        self.learned_rules_path.parent.mkdir(exist_ok=True)
        if not self.learned_rules_path.exists():
            with open(self.learned_rules_path, 'w') as f:
                json.dump({"rules": []}, f)

    def observe_solution(self, problem: str, solution: str, source: str):
        """Record successful solutions"""
        problem_hash = hashlib.sha256(problem.encode()).hexdigest()
        
        # Store in knowledge graph
        self.graph.cache_solution(
            problem=problem,
            solution=solution,
            metadata={
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
                "usage_count": 0
            }
        )
        
        # Auto-generate rules for pattern-like solutions
        if self._is_pattern_candidate(solution):
            self._extract_rule(problem, solution)

    def _is_pattern_candidate(self, solution: str) -> bool:
        """Check if solution is generalizable"""
        return (solution.count('\n') <= 2 and 
                solution.count('(') < 3 and 
                'for ' in solution or 'with ' in solution)

    def _extract_rule(self, problem: str, solution: str):
        """Convert solutions into reusable rules"""
        # Basic pattern extraction
        vars = {
            'iterable': self._find_between(solution, 'for ', ' in'),
            'var': self._find_between(solution, 'for ', ' in').split()[0]
        } if 'for ' in solution else {
            'expr': self._find_between(solution, 'with ', ' as'),
            'var': self._find_between(solution, 'as ', ':').strip()
        }
        
        new_rule = {
            "template": solution,
            "vars": list(vars.keys()),
            "source_problem": problem,
            "last_used": None,
            "success_rate": 1.0
        }
        
        self._save_rule(new_rule)

    def _save_rule(self, rule: Dict[str, Any]):
        """Persist learned rules"""
        with open(self.learned_rules_path, 'r+') as f:
            data = json.load(f)
            data["rules"].append(rule)
            f.seek(0)
            json.dump(data, f, indent=2)
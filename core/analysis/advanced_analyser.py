# core/analysis/advanced_analyzer.py
import ast
import re
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

class CodeComplexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class CodeSmell(Enum):
    LONG_METHOD = "long_method"
    LARGE_CLASS = "large_class"
    DUPLICATE_CODE = "duplicate_code"
    COMPLEX_CONDITIONAL = "complex_conditional"
    MAGIC_NUMBER = "magic_number"
    LONG_PARAMETER_LIST = "long_parameter_list"

@dataclass
class CodeIssue:
    type: CodeSmell
    severity: str  # "low", "medium", "high", "critical"
    description: str
    line_number: int
    suggestion: str

@dataclass
class CodeMetrics:
    complexity: CodeComplexity
    maintainability: float  # 0-1 scale
    reliability: float    # 0-1 scale
    security_score: float  # 0-1 scale
    issues: List[CodeIssue]
    total_lines: int
    comment_ratio: float

class AdvancedCodeAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.code_patterns = self._load_code_patterns()
        self.security_patterns = self._load_security_patterns()
    
    def analyze_code(self, code: str, language: str) -> CodeMetrics:
        """Comprehensive code analysis"""
        if language == "python":
            return self._analyze_python_code(code)
        elif language == "javascript":
            return self._analyze_javascript_code(code)
        else:
            return self._analyze_generic_code(code)
    
    def _analyze_python_code(self, code: str) -> CodeMetrics:
        """Analyze Python code with AST"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Handle syntax errors
            return CodeMetrics(
                complexity=CodeComplexity.HIGH,
                maintainability=0.1,
                reliability=0.1,
                security_score=0.5,
                issues=[],
                total_lines=len(code.split('\n')),
                comment_ratio=0.0
            )
        
        # Calculate various metrics
        complexity = self._calculate_complexity(tree, code)
        maintainability = self._calculate_maintainability(tree, code)
        reliability = self._calculate_reliability(tree, code)
        security_score = self._calculate_security_score(tree, code)
        issues = self._detect_code_smells(tree, code)
        total_lines = len(code.split('\n'))
        comment_ratio = self._calculate_comment_ratio(code)
        
        return CodeMetrics(
            complexity=complexity,
            maintainability=maintainability,
            reliability=reliability,
            security_score=security_score,
            issues=issues,
            total_lines=total_lines,
            comment_ratio=comment_ratio
        )
    
    def _calculate_complexity(self, tree: ast.AST, code: str) -> CodeComplexity:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        if complexity <= 5:
            return CodeComplexity.LOW
        elif complexity <= 10:
            return CodeComplexity.MEDIUM
        else:
            return CodeComplexity.HIGH
    
    def _calculate_maintainability(self, tree: ast.AST, code: str) -> float:
        """Calculate maintainability score (0-1)"""
        # Factors: function length, class size, comment ratio, naming conventions
        score = 1.0
        
        # Check function lengths
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_length = node.end_lineno - node.lineno
                if func_length > 50:
                    score -= 0.1
                elif func_length > 100:
                    score -= 0.2
        
        # Check class sizes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_length = node.end_lineno - node.lineno
                if class_length > 200:
                    score -= 0.15
                elif class_length > 500:
                    score -= 0.3
        
        # Check naming conventions
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                        score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def _calculate_reliability(self, tree: ast.AST, code: str) -> float:
        """Calculate reliability score (0-1)"""
        score = 1.0
        
        # Check for error handling
        try_blocks = [node for node in ast.walk(tree) if isinstance(node, ast.Try)]
        if not try_blocks:
            score -= 0.2
        
        # Check for bare excepts
        for node in try_blocks:
            for handler in node.handlers:
                if handler.type is None:
                    score -= 0.3
        
        # Check for resource management
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_security_score(self, tree: ast.AST, code: str) -> float:
        """Calculate security score (0-1)"""
        score = 1.0
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'subprocess\.',
            r'os\.system\s*\(',
            r'pickle\.loads\s*\(',
            r'marshal\.loads\s*\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                score -= 0.2
        
        # Check for hardcoded credentials
        credential_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]
        
        for pattern in credential_patterns:
            if re.search(pattern, code):
                score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _detect_code_smells(self, tree: ast.AST, code: str) -> List[CodeIssue]:
        """Detect code smells and issues"""
        issues = []
        
        # Long methods
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                length = node.end_lineno - node.lineno
                if length > 50:
                    issues.append(CodeIssue(
                        type=CodeSmell.LONG_METHOD,
                        severity="medium",
                        description=f"Method {node.name} is too long ({length} lines)",
                        line_number=node.lineno,
                        suggestion="Consider breaking this method into smaller functions"
                    ))
        
        # Large classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                length = node.end_lineno - node.lineno
                if length > 200:
                    issues.append(CodeIssue(
                        type=CodeSmell.LARGE_CLASS,
                        severity="medium",
                        description=f"Class {node.name} is too large ({length} lines)",
                        line_number=node.lineno,
                        suggestion="Consider splitting this class into smaller classes"
                    ))
        
        # Magic numbers
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value not in [0, 1, -1, 0.0, 1.0, -1.0]:
                    issues.append(CodeIssue(
                        type=CodeSmell.MAGIC_NUMBER,
                        severity="low",
                        description=f"Magic number {node.value} found",
                        line_number=node.lineno,
                        suggestion="Consider using a named constant"
                    ))
        
        return issues
    
    def _calculate_comment_ratio(self, code: str) -> float:
        """Calculate comment to code ratio"""
        lines = code.split('\n')
        code_lines = 0
        comment_lines = 0
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                code_lines += 1
            elif line.startswith('#'):
                comment_lines += 1
        
        if code_lines == 0:
            return 0.0
        
        return comment_lines / (code_lines + comment_lines)
    
    def generate_code_improvements(self, code: str, language: str) -> Dict[str, Any]:
        """Generate code improvement suggestions"""
        metrics = self.analyze_code(code, language)
        
        improvements = {
            "original_metrics": {
                "complexity": metrics.complexity.value,
                "maintainability": metrics.maintainability,
                "reliability": metrics.reliability,
                "security_score": metrics.security_score
            },
            "suggested_improvements": []
        }
        
        # Generate suggestions based on metrics
        if metrics.maintainability < 0.7:
            improvements["suggested_improvements"].append({
                "type": "maintainability",
                "description": "Improve code maintainability",
                "suggestions": [
                    "Break down large functions into smaller ones",
                    "Use more descriptive variable names",
                    "Add comments to explain complex logic"
                ]
            })
        
        if metrics.reliability < 0.7:
            improvements["suggested_improvements"].append({
                "type": "reliability",
                "description": "Improve code reliability",
                "suggestions": [
                    "Add proper error handling",
                    "Use context managers for resource management",
                    "Add input validation"
                ]
            })
        
        if metrics.security_score < 0.8:
            improvements["suggested_improvements"].append({
                "type": "security",
                "description": "Improve code security",
                "suggestions": [
                    "Avoid using eval() or exec()",
                    "Use parameterized queries instead of string concatenation",
                    "Store sensitive data in environment variables"
                ]
            })
        
        # Add specific issue-based suggestions
        for issue in metrics.issues:
            improvements["suggested_improvements"].append({
                "type": issue.type.value,
                "description": issue.description,
                "suggestions": [issue.suggestion]
            })
        
        return improvements
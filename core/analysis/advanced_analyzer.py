# core/analysis/advanced_analyser.py
import ast
import re
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from .config_loader import ConfigLoader

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
    def __init__(self, config_path: str = "./configs/base.yaml"):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.get_config()
        self.code_patterns = self._load_code_patterns()
        self.security_patterns = self._load_security_patterns()
        self.quality_standards = self.config.get('quality_standards', {})
    
    def analyze_code(self, code: str, language: str) -> CodeMetrics:
        """Comprehensive code analysis with language-specific handling"""
        language = language.lower()
        
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
                issues=[CodeIssue(
                    type=CodeSmell.COMPLEX_CONDITIONAL,
                    severity="critical",
                    description="Syntax error in Python code",
                    line_number=1,
                    suggestion="Fix syntax errors before analysis"
                )],
                total_lines=len(code.split('\n')),
                comment_ratio=0.0
            )
        
        # Get language-specific standards
        language_standards = self.config_loader.get_language_standards('python')
        code_smell_thresholds = self.config_loader.get_code_smell_thresholds('python')
        
        # Calculate various metrics
        complexity = self._calculate_complexity(tree, code)
        maintainability = self._calculate_maintainability(tree, code, language_standards)
        reliability = self._calculate_reliability(tree, code)
        security_score = self._calculate_security_score(tree, code)
        issues = self._detect_code_smells(tree, code, code_smell_thresholds)
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
    
    def _analyze_javascript_code(self, code: str) -> CodeMetrics:
        """Analyze JavaScript code with a focus on modularity and scalability patterns"""
        try:
            # Get language-specific standards
            language_standards = self.config_loader.get_language_standards('javascript')
            code_smell_thresholds = self.config_loader.get_code_smell_thresholds('javascript')
            
            total_lines = len(code.split('\n'))
            comment_ratio = self._calculate_comment_ratio(code)
            
            # Calculate complexity based on JavaScript patterns
            complexity_score = self._calculate_js_complexity(code)
            complexity = self._map_score_to_complexity(complexity_score)
            
            # Calculate maintainability
            maintainability = self._calculate_js_maintainability(code, language_standards)
            
            # Calculate reliability
            reliability = self._calculate_js_reliability(code)
            
            # Calculate security score
            security_score = self._calculate_js_security_score(code)
            
            # Detect JavaScript-specific issues
            issues = self._detect_js_code_smells(code, code_smell_thresholds)
            
            return CodeMetrics(
                complexity=complexity,
                maintainability=maintainability,
                reliability=reliability,
                security_score=security_score,
                issues=issues,
                total_lines=total_lines,
                comment_ratio=comment_ratio
            )
        except Exception as e:
            # Fallback to generic analysis if JavaScript-specific analysis fails
            return self._analyze_generic_code(code)
    
    def _analyze_generic_code(self, code: str) -> CodeMetrics:
        """Generic code analysis for any programming language"""
        # Get generic standards
        language_standards = self.config_loader.get_language_standards('generic')
        code_smell_thresholds = self.config_loader.get_code_smell_thresholds('generic')
        
        total_lines = len(code.split('\n'))
        comment_ratio = self._calculate_comment_ratio(code)
        
        # Basic complexity analysis using control flow keywords
        control_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch', 'except', 'do', 'until', 'repeat']
        complexity_count = sum(1 for line in code.split('\n') 
                             if any(keyword in line.lower() for keyword in control_keywords))
        
        complexity = self._map_score_to_complexity(complexity_count / max(1, total_lines) * 100)
        
        # Basic maintainability based on size and structure
        maintainability = 1.0
        max_file_size = language_standards.get('max_class_length', 500)
        if total_lines > max_file_size:
            maintainability -= 0.3
        elif total_lines > max_file_size * 0.6:
            maintainability -= 0.2
        elif total_lines > max_file_size * 0.4:
            maintainability -= 0.1
        
        # Adjust by comment ratio
        maintainability += comment_ratio * 0.2
        maintainability = max(0.0, min(1.0, maintainability))
        
        # Basic reliability check
        reliability = 0.7
        error_handling_keywords = ['try', 'catch', 'except', 'throw', 'raise', 'error', 'exception']
        if any(keyword in code.lower() for keyword in error_handling_keywords):
            reliability += 0.2
        
        # Security check using common dangerous patterns
        security_score = 0.7
        dangerous_patterns = self.quality_standards.get('banned_patterns', [])
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                security_score -= 0.2
        
        security_score = max(0.0, min(1.0, security_score))
        
        # Basic issue detection
        issues = []
        max_file_size = code_smell_thresholds.get('large_class', 500)
        if total_lines > max_file_size:
            issues.append(CodeIssue(
                type=CodeSmell.LARGE_CLASS,
                severity="medium",
                description=f"File is too large ({total_lines} lines)",
                line_number=1,
                suggestion="Consider splitting this file into smaller modules"
            ))
        
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
        """Calculate cyclomatic complexity for Python"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        # Get complexity thresholds from configuration
        complexity_thresholds = self.quality_standards.get('complexity_thresholds', {
            'low': 5,
            'medium': 10
        })
        
        if complexity <= complexity_thresholds.get('low', 5):
            return CodeComplexity.LOW
        elif complexity <= complexity_thresholds.get('medium', 10):
            return CodeComplexity.MEDIUM
        else:
            return CodeComplexity.HIGH
    
    def _calculate_maintainability(self, tree: ast.AST, code: str, language_standards: Dict[str, Any]) -> float:
        """Calculate maintainability score for Python (0-1)"""
        score = 1.0
        
        # Get language-specific standards
        max_function_length = language_standards.get('max_function_length', 50)
        max_class_length = language_standards.get('max_class_length', 200)
        
        # Check function lengths
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_length = node.end_lineno - node.lineno
                if func_length > max_function_length:
                    score -= 0.1
                elif func_length > max_function_length * 2:
                    score -= 0.2
        
        # Check class sizes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_length = node.end_lineno - node.lineno
                if class_length > max_class_length:
                    score -= 0.15
                elif class_length > max_class_length * 2:
                    score -= 0.3
        
        # Check naming conventions
        naming_convention = language_standards.get('naming_convention', 'snake_case')
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    if naming_convention == 'snake_case' and not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                        score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def _calculate_reliability(self, tree: ast.AST, code: str) -> float:
        """Calculate reliability score for Python (0-1)"""
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
        """Calculate security score for Python (0-1)"""
        score = 1.0
        
        # Check for dangerous patterns from configuration
        dangerous_patterns = self.quality_standards.get('banned_patterns', [])
        
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
    
    def _detect_code_smells(self, tree: ast.AST, code: str, code_smell_thresholds: Dict[str, Any]) -> List[CodeIssue]:
        """Detect Python-specific code smells using configuration"""
        issues = []
        severity_levels = self.config_loader.get_severity_levels()
        
        # Long methods
        max_function_length = code_smell_thresholds.get('long_method', 50)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                length = node.end_lineno - node.lineno
                if length > max_function_length:
                    severity = "medium"
                    if length > max_function_length * 2:
                        severity = "high"
                    
                    issues.append(CodeIssue(
                        type=CodeSmell.LONG_METHOD,
                        severity=severity,
                        description=f"Method {node.name} is too long ({length} lines)",
                        line_number=node.lineno,
                        suggestion="Consider breaking this method into smaller functions"
                    ))
        
        # Large classes
        max_class_length = code_smell_thresholds.get('large_class', 200)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                length = node.end_lineno - node.lineno
                if length > max_class_length:
                    severity = "medium"
                    if length > max_class_length * 2:
                        severity = "high"
                    
                    issues.append(CodeIssue(
                        type=CodeSmell.LARGE_CLASS,
                        severity=severity,
                        description=f"Class {node.name} is too large ({length} lines)",
                        line_number=node.lineno,
                        suggestion="Consider splitting this class into smaller classes"
                    ))
        
        # Magic numbers
        magic_numbers_config = code_smell_thresholds.get('magic_number', {})
        allowed_values = magic_numbers_config.get('allowed_values', [0, 1, -1, 0.0, 1.0, -1.0])
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value not in allowed_values:
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
    
    def _calculate_js_complexity(self, code: str) -> float:
        """Calculate JavaScript code complexity score"""
        # Count control structures
        control_structures = [
            r'if\s*\(', r'else\s*\{', r'for\s*\(', r'while\s*\(', 
            r'switch\s*\(', r'case\s+', r'try\s*\{', r'catch\s*\(',
            r'do\s*\{', r'function\s*\w*\s*\(', r'=>', r'async\s+function'
        ]
        
        complexity = 0
        for pattern in control_structures:
            complexity += len(re.findall(pattern, code))
        
        # Normalize by code length
        lines = len(code.split('\n'))
        return min(100, complexity / max(1, lines) * 100)
    
    def _calculate_js_maintainability(self, code: str, language_standards: Dict[str, Any]) -> float:
        """Calculate JavaScript code maintainability score"""
        score = 1.0
        lines = len(code.split('\n'))
        
        # Get language-specific standards
        max_function_length = language_standards.get('max_function_length', 40)
        max_class_length = language_standards.get('max_class_length', 150)
        
        # Penalty for long files
        if lines > max_class_length * 2:
            score -= 0.3
        elif lines > max_class_length * 1.5:
            score -= 0.2
        elif lines > max_class_length:
            score -= 0.1
        
        # Penalty for deeply nested code
        max_indent = max(len(line) - len(line.lstrip()) for line in code.split('\n') if line.strip())
        if max_indent > 16:
            score -= 0.2
        elif max_indent > 12:
            score -= 0.1
        
        # Penalty for long functions
        function_pattern = r'(function\s+\w+\s*\([^)]*\)\s*\{|=>\s*\{|\w+\s*\([^)]*\)\s*=>\s*\{)'
        functions = re.finditer(function_pattern, code)
        
        for match in functions:
            start_pos = match.end()
            # Find matching closing brace (simplified)
            brace_count = 1
            pos = start_pos
            while pos < len(code) and brace_count > 0:
                if code[pos] == '{':
                    brace_count += 1
                elif code[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            func_lines = code[start_pos:pos].count('\n')
            if func_lines > max_function_length:
                score -= 0.1
            elif func_lines > max_function_length * 2:
                score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_js_reliability(self, code: str) -> float:
        """Calculate JavaScript code reliability score"""
        score = 0.7
        
        # Check for error handling
        if re.search(r'try\s*\{', code) and re.search(r'catch\s*\(', code):
            score += 0.2
        
        # Check for null checks
        if re.search(r'===\s*null|!==\s*null', code):
            score += 0.1
        
        # Check for validation
        if re.search(r'validate|check|verify', code, re.IGNORECASE):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_js_security_score(self, code: str) -> float:
        """Calculate JavaScript code security score"""
        score = 0.7
        
        # Check for dangerous patterns from configuration
        dangerous_patterns = self.quality_standards.get('banned_patterns', [])
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                score -= 0.2
        
        # Check for XSS vulnerabilities
        xss_patterns = [
            r'\.innerHTML\s*=\s*.*\+',
            r'\.outerHTML\s*=\s*.*\+',
            r'document\.write\s*\([^)]*\+'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                score -= 0.15
        
        return max(0.0, min(1.0, score))
    
    def _detect_js_code_smells(self, code: str, code_smell_thresholds: Dict[str, Any]) -> List[CodeIssue]:
        """Detect JavaScript-specific code smells"""
        issues = []
        lines = code.split('\n')
        
        # Get thresholds
        max_function_length = code_smell_thresholds.get('long_method', 40)
        
        # Check for long functions
        function_pattern = r'(function\s+\w+\s*\([^)]*\)\s*\{|=>\s*\{|\w+\s*\([^)]*\)\s*=>\s*\{)'
        functions = re.finditer(function_pattern, code)
        
        for match in functions:
            start_pos = match.end()
            line_num = code[:start_pos].count('\n') + 1
            
            # Find matching closing brace (simplified)
            brace_count = 1
            pos = start_pos
            while pos < len(code) and brace_count > 0:
                if code[pos] == '{':
                    brace_count += 1
                elif code[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            func_lines = code[start_pos:pos].count('\n')
            if func_lines > max_function_length:
                severity = "medium"
                if func_lines > max_function_length * 2:
                    severity = "high"
                
                issues.append(CodeIssue(
                    type=CodeSmell.LONG_METHOD,
                    severity=severity,
                    description=f"Function is too long ({func_lines} lines)",
                    line_number=line_num,
                    suggestion="Consider breaking this function into smaller functions"
                ))
        
        # Check for global variables
        global_vars = re.finditer(r'(var|let|const)\s+(\w+)', code)
        for match in global_vars:
            var_name = match.group(2)
            line_num = code[:match.start()].count('\n') + 1
            
            # Check if variable is used in a function
            func_pattern = r'function\s+\w+\s*\([^)]*\)\s*\{'
            if re.search(func_pattern, code):
                issues.append(CodeIssue(
                    type=CodeSmell.MAGIC_NUMBER,  # Using as a proxy for global variable issue
                    severity="low",
                    description=f"Global variable '{var_name}' detected",
                    line_number=line_num,
                    suggestion="Consider using local variables or encapsulating in a module"
                ))
        
        return issues
    
    def _map_score_to_complexity(self, score: float) -> CodeComplexity:
        """Map a numerical score to a complexity level"""
        complexity_thresholds = self.quality_standards.get('complexity_thresholds', {
            'low': 20,
            'medium': 50
        })
        
        if score <= complexity_thresholds.get('low', 20):
            return CodeComplexity.LOW
        elif score <= complexity_thresholds.get('medium', 50):
            return CodeComplexity.MEDIUM
        else:
            return CodeComplexity.HIGH
    
    def _load_code_patterns(self) -> Dict[str, List[str]]:
        """Load code patterns for different languages"""
        return {
            "python": [
                r'def\s+\w+\(.*\):',
                r'import\s+\w+',
                r'class\s+\w+'
            ],
            "javascript": [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*=',
                r'let\s+\w+\s*='
            ]
        }
    
    def _load_security_patterns(self) -> Dict[str, List[str]]:
        """Load security patterns for different languages"""
        return {
            "python": [
                r'eval\s*\(',
                r'exec\s*\(',
                r'pickle\.loads'
            ],
            "javascript": [
                r'eval\s*\(',
                r'document\.write',
                r'innerHTML\s*='
            ]
        }
    
    def generate_code_improvements(self, code: str, language: str) -> Dict[str, Any]:
        """Generate code improvement suggestions"""
        metrics = self.analyze_code(code, language)
        
        improvements = {
            "original_metrics": {
                "complexity": metrics.complexity.value,
                "maintainability": metrics.maintainability,
                "reliability": metrics.reliability,
                "security_score": metrics.security_score,
                "total_issues": len(metrics.issues)
            },
            "suggestions": []
        }
        
        # Get quality standards
        min_maintainability = self.quality_standards.get('min_maintainability', 0.6)
        min_security_score = self.quality_standards.get('min_security_score', 0.7)
        min_reliability = self.quality_standards.get('min_reliability', 0.7)
        
        # Generate suggestions based on metrics
        if metrics.maintainability < min_maintainability:
            improvements["suggestions"].append({
                "type": "maintainability",
                "priority": "high",
                "description": "Code maintainability is low. Consider refactoring large functions and classes."
            })
        
        if metrics.security_score < min_security_score:
            improvements["suggestions"].append({
                "type": "security",
                "priority": "critical",
                "description": "Security vulnerabilities detected. Review and fix dangerous patterns."
            })
        
        if metrics.reliability < min_reliability:
            improvements["suggestions"].append({
                "type": "reliability",
                "priority": "medium",
                "description": "Reliability could be improved. Add proper error handling."
            })
        
        # Add specific issue suggestions
        for issue in metrics.issues:
            improvements["suggestions"].append({
                "type": "code_smell",
                "priority": issue.severity,
                "description": issue.description,
                "suggestion": issue.suggestion,
                "line_number": issue.line_number
            })
        
        return improvements
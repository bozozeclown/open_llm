# core/refactoring/refactor_engine.py
import ast
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class RefactoringType(Enum):
    EXTRACT_FUNCTION = "extract_function"
    RENAME_VARIABLE = "rename_variable"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    INTRODUCE_CONSTANT = "introduce_constant"
    REMOVE_DEAD_CODE = "remove_dead_code"
    ADD_TYPE_HINTS = "add_type_hints"

@dataclass
class RefactoringSuggestion:
    type: RefactoringType
    title: str
    description: str
    original_code: str
    suggested_code: str
    confidence: float
    line_range: tuple[int, int]
    effort: str  # "low", "medium", "high"

class RefactoringEngine:
    def __init__(self):
        self.patterns = {
            RefactoringType.EXTRACT_FUNCTION: self._detect_extract_function_opportunities,
            RefactoringType.RENAME_VARIABLE: self._detect_poor_variable_names,
            RefactoringType.SIMPLIFY_CONDITIONAL: self._detect_complex_conditionals,
            RefactoringType.INTRODUCE_CONSTANT: self._detect_magic_numbers,
            RefactoringType.REMOVE_DEAD_CODE: self._detect_dead_code,
            RefactoringType.ADD_TYPE_HINTS: self._detect_missing_type_hints
        }
    
    def analyze_code(self, code: str, language: str) -> List[RefactoringSuggestion]:
        """Analyze code and suggest refactorings"""
        suggestions = []
        
        try:
            if language == "python":
                tree = ast.parse(code)
                suggestions.extend(self._analyze_python_code(tree, code))
            elif language == "javascript":
                # Add JavaScript analysis logic
                pass
        except SyntaxError as e:
            print(f"Syntax error in code: {e}")
        
        return suggestions
    
    def _analyze_python_code(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Analyze Python code for refactoring opportunities"""
        suggestions = []
        
        # Check each refactoring pattern
        for refactoring_type, detector in self.patterns.items():
            new_suggestions = detector(tree, code)
            suggestions.extend(new_suggestions)
        
        # Sort by confidence and effort
        suggestions.sort(key=lambda x: (x.confidence, x.effort), reverse=True)
        return suggestions
    
    def _detect_extract_function_opportunities(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Detect opportunities to extract functions"""
        suggestions = []
        
        # Look for long functions (> 20 lines)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno
                if func_lines > 20:
                    # Find code blocks that could be extracted
                    extractable_blocks = self._find_extractable_blocks(node)
                    
                    for block in extractable_blocks:
                        suggestions.append(RefactoringSuggestion(
                            type=RefactoringType.EXTRACT_FUNCTION,
                            title=f"Extract function from {node.name}",
                            description=f"Extract {len(block)} lines into a separate function",
                            original_code=self._get_code_lines(code, block[0], block[1]),
                            suggested_code=self._generate_extracted_function(block, node.name),
                            confidence=0.8,
                            line_range=block,
                            effort="medium"
                        ))
        
        return suggestions
    
    def _detect_poor_variable_names(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Detect poorly named variables"""
        suggestions = []
        
        poor_name_patterns = [
            r'^[a-z]$',  # Single letter names
            r'^[a-z][0-9]+$',  # Names like x1, x2
            r'^temp$',  # Generic temp names
            r'^data$',  # Generic data names
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                var_name = node.id
                
                for pattern in poor_name_patterns:
                    if re.match(pattern, var_name):
                        suggestions.append(RefactoringSuggestion(
                            type=RefactoringType.RENAME_VARIABLE,
                            title=f"Rename variable '{var_name}'",
                            description=f"Variable name '{var_name}' is not descriptive",
                            original_code=var_name,
                            suggested_code=self._suggest_better_name(var_name, node),
                            confidence=0.7,
                            line_range=(node.lineno, node.lineno),
                            effort="low"
                        ))
                        break
        
        return suggestions
    
    def _detect_complex_conditionals(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Detect complex conditional statements"""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check for nested conditionals
                nested_count = self._count_nested_ifs(node)
                if nested_count > 2:
                    suggestions.append(RefactoringSuggestion(
                        type=RefactoringType.SIMPLIFY_CONDITIONAL,
                        title="Simplify complex conditional",
                        description=f"Conditional has {nested_count} levels of nesting",
                        original_code=self._get_code_lines(code, node.lineno, node.end_lineno),
                        suggested_code=self._simplify_conditional(node, code),
                        confidence=0.9,
                        line_range=(node.lineno, node.end_lineno),
                        effort="high"
                    ))
        
        return suggestions
    
    def _detect_magic_numbers(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Detect magic numbers that should be constants"""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # Skip common small numbers
                if node.value in [0, 1, 2, -1, 0.0, 1.0]:
                    continue
                
                # Check if it's used multiple times
                usage_count = self._count_number_usage(tree, node.value)
                if usage_count > 2:
                    suggestions.append(RefactoringSuggestion(
                        type=RefactoringType.INTRODUCE_CONSTANT,
                        title=f"Introduce constant for {node.value}",
                        description=f"Number {node.value} is used {usage_count} times",
                        original_code=str(node.value),
                        suggested_code=f"{self._suggest_constant_name(node.value)} = {node.value}",
                        confidence=0.8,
                        line_range=(node.lineno, node.lineno),
                        effort="low"
                    ))
        
        return suggestions
    
    def _detect_dead_code(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Detect dead code that can be removed"""
        suggestions = []
        
        # Look for unreachable code after return statements
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return_statements = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                
                for return_stmt in return_statements:
                    if return_stmt.lineno < node.end_lineno:
                        # Code after return
                        suggestions.append(RefactoringSuggestion(
                            type=RefactoringType.REMOVE_DEAD_CODE,
                            title="Remove dead code",
                            description=f"Unreachable code after return statement on line {return_stmt.lineno}",
                            original_code=self._get_code_lines(code, return_stmt.lineno + 1, node.end_lineno),
                            suggested_code="",
                            confidence=1.0,
                            line_range=(return_stmt.lineno + 1, node.end_lineno),
                            effort="low"
                        ))
        
        return suggestions
    
    def _detect_missing_type_hints(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Detect missing type hints in Python code"""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function arguments
                missing_args = []
                for arg in node.args.args:
                    if arg.annotation is None:
                        missing_args.append(arg.arg)
                
                # Check return type
                missing_return = node.returns is None
                
                if missing_args or missing_return:
                    suggestions.append(RefactoringSuggestion(
                        type=RefactoringType.ADD_TYPE_HINTS,
                        title=f"Add type hints to {node.name}",
                        description=f"Function {node.name} is missing type hints",
                        original_code=self._get_function_signature(code, node),
                        suggested_code=self._add_type_hints(node, code),
                        confidence=0.6,
                        line_range=(node.lineno, node.lineno),
                        effort="low"
                    ))
        
        return suggestions
    
    # Helper methods for refactoring analysis
    def _find_extractable_blocks(self, func_node: ast.FunctionDef) -> List[tuple[int, int]]:
        """Find blocks of code that could be extracted into functions"""
        # Simplified implementation - in practice, this would be more sophisticated
        blocks = []
        current_block_start = None
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While, ast.If)):
                if current_block_start is None:
                    current_block_start = node.lineno
            elif isinstance(node, (ast.Return, ast.Break, ast.Continue)):
                if current_block_start is not None:
                    blocks.append((current_block_start, node.lineno))
                    current_block_start = None
        
        return blocks
    
    def _suggest_better_name(self, var_name: str, node: ast.Name) -> str:
        """Suggest a better variable name"""
        # Simple heuristic - in practice, use context analysis
        name_mapping = {
            'x': 'value',
            'y': 'result',
            'i': 'index',
            'j': 'counter',
            'temp': 'temporary',
            'data': 'input_data'
        }
        return name_mapping.get(var_name, f"{var_name}_descriptive")
    
    def _suggest_constant_name(self, value: Any) -> str:
        """Suggest a constant name for a magic number"""
        if isinstance(value, int):
            if value == 100:
                return "PERCENTAGE"
            elif value == 360:
                return "DEGREES_IN_CIRCLE"
            elif value > 1000:
                return "MAX_LIMIT"
        return f"CONSTANT_{value}"
    
    # Additional helper methods would be implemented here...
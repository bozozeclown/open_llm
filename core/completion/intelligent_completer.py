# core/completion/intelligent_completer.py
import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class CompletionContext:
    file_path: str
    language: str
    imports: List[str]
    variables: Dict[str, str]
    functions: List[str]
    classes: List[str]
    current_scope: str
    cursor_position: Tuple[int, int]

@dataclass
class CompletionSuggestion:
    text: str
    type: str  # "variable", "function", "class", "method", "keyword", "import"
    description: str
    confidence: float
    context: str

class IntelligentCodeCompleter:
    def __init__(self):
        self.context_cache = {}
        self.completion_history = defaultdict(list)
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.completion_embeddings = None
        self.language_patterns = self._load_language_patterns()
    
    def get_completions(self, code: str, cursor_pos: int, file_path: str, language: str) -> List[CompletionSuggestion]:
        """Get intelligent code completions"""
        # Parse and analyze context
        context = self._analyze_context(code, cursor_pos, file_path, language)
        
        # Generate different types of completions
        completions = []
        
        # Local variable completions
        completions.extend(self._get_variable_completions(context))
        
        # Function/method completions
        completions.extend(self._get_function_completions(context))
        
        # Class completions
        completions.extend(self._get_class_completions(context))
        
        # Keyword completions
        completions.extend(self._get_keyword_completions(context))
        
        # Import completions
        completions.extend(self._get_import_completions(context))
        
        # Context-aware completions
        completions.extend(self._get_context_aware_completions(context))
        
        # Sort by confidence and return top suggestions
        completions.sort(key=lambda x: x.confidence, reverse=True)
        return completions[:10]  # Return top 10 completions
    
    def _analyze_context(self, code: str, cursor_pos: int, file_path: str, language: str) -> CompletionContext:
        """Analyze code context for intelligent completions"""
        # Get current line and surrounding context
        lines = code.split('\n')
        current_line_idx = cursor_pos // (len(code) // len(lines)) if len(lines) > 0 else 0
        current_line = lines[current_line_idx]
        
        # Extract imports
        imports = self._extract_imports(code, language)
        
        # Extract variables, functions, and classes
        variables = self._extract_variables(code, language)
        functions = self._extract_functions(code, language)
        classes = self._extract_classes(code, language)
        
        # Determine current scope
        current_scope = self._determine_current_scope(code, cursor_pos, language)
        
        return CompletionContext(
            file_path=file_path,
            language=language,
            imports=imports,
            variables=variables,
            functions=functions,
            classes=classes,
            current_scope=current_scope,
            cursor_position=(current_line_idx, cursor_pos % len(lines[current_line_idx]) if current_line_idx < len(lines) else 0)
        )
    
    def _extract_imports(self, code: str, language: str) -> List[str]:
        """Extract import statements"""
        imports = []
        
        if language == "python":
            import_pattern = r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            from_pattern = r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
            
            imports.extend(re.findall(import_pattern, code))
            imports.extend(re.findall(from_pattern, code))
        
        elif language == "javascript":
            import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
            require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'
            
            imports.extend(re.findall(import_pattern, code))
            imports.extend(re.findall(require_pattern, code))
        
        return imports
    
    def _extract_variables(self, code: str, language: str) -> Dict[str, str]:
        """Extract variable declarations"""
        variables = {}
        
        if language == "python":
            # Variable assignments
            var_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^#\n]+)'
            for match in re.finditer(var_pattern, code):
                var_name = match.group(1)
                var_value = match.group(2).strip()
                variables[var_name] = var_value
        
        elif language == "javascript":
            # Variable declarations
            var_patterns = [
                r'var\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;\n]+)',
                r'let\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;\n]+)',
                r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;\n]+)'
            ]
            
            for pattern in var_patterns:
                for match in re.finditer(pattern, code):
                    var_name = match.group(1)
                    var_value = match.group(2).strip()
                    variables[var_name] = var_value
        
        return variables
    
    def _extract_functions(self, code: str, language: str) -> List[str]:
        """Extract function definitions"""
        functions = []
        
        if language == "python":
            func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            functions.extend(re.findall(func_pattern, code))
        
        elif language == "javascript":
            func_patterns = [
                r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*function\s*\(',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\([^)]*\)\s*=>'
            ]
            
            for pattern in func_patterns:
                functions.extend(re.findall(pattern, code))
        
        return functions
    
    def _extract_classes(self, code: str, language: str) -> List[str]:
        """Extract class definitions"""
        classes = []
        
        if language == "python":
            class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            classes.extend(re.findall(class_pattern, code))
        
        elif language == "javascript":
            class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            classes.extend(re.findall(class_pattern, code))
        
        return classes
    
    def _determine_current_scope(self, code: str, cursor_pos: int, language: str) -> str:
        """Determine the current scope at cursor position"""
        # Simplified scope detection
        lines = code.split('\n')
        current_line_idx = cursor_pos // (len(code) // len(lines)) if len(lines) > 0 else 0
        
        # Look for class or function definitions before cursor
        for i in range(current_line_idx, -1, -1):
            line = lines[i].strip()
            
            if language == "python":
                if line.startswith('class '):
                    return f"class:{line.split()[1]}"
                elif line.startswith('def '):
                    return f"function:{line.split()[1]}"
            
            elif language == "javascript":
                if line.startswith('class '):
                    return f"class:{line.split()[1]}"
                elif line.startswith('function '):
                    return f"function:{line.split()[1]}"
                elif '=' in line and 'function' in line:
                    func_name = line.split('=')[0].strip()
                    return f"function:{func_name}"
        
        return "global"
    
    def _get_variable_completions(self, context: CompletionContext) -> List[CompletionSuggestion]:
        """Get variable completions"""
        completions = []
        
        for var_name, var_value in context.variables.items():
            # Only suggest variables that are accessible in current scope
            if self._is_accessible(var_name, context):
                completions.append(CompletionSuggestion(
                    text=var_name,
                    type="variable",
                    description=f"Variable: {var_value[:50]}...",
                    confidence=0.9,
                    context=context.current_scope
                ))
        
        return completions
    
    def _get_function_completions(self, context: CompletionContext) -> List[CompletionSuggestion]:
        """Get function completions"""
        completions = []
        
        for func_name in context.functions:
            completions.append(CompletionSuggestion(
                text=func_name,
                type="function",
                description=f"Function: {func_name}",
                confidence=0.8,
                context=context.current_scope
            ))
        
        return completions
    
    def _get_class_completions(self, context: CompletionContext) -> List[CompletionSuggestion]:
        """Get class completions"""
        completions = []
        
        for class_name in context.classes:
            completions.append(CompletionSuggestion(
                text=class_name,
                type="class",
                description=f"Class: {class_name}",
                confidence=0.8,
                context=context.current_scope
            ))
        
        return completions
    
    def _get_keyword_completions(self, context: CompletionContext) -> List[CompletionSuggestion]:
        """Get keyword completions"""
        completions = []
        
        if context.language == "python":
            keywords = [
                "def", "class", "if", "else", "elif", "for", "while", "try", "except",
                "finally", "with", "import", "from", "as", "return", "yield", "raise",
                "assert", "del", "pass", "break", "continue", "global", "nonlocal", "lambda",
                "and", "or", "not", "in", "is", "True", "False", "None"
            ]
        elif context.language == "javascript":
            keywords = [
                "function", "class", "if", "else", "for", "while", "do", "switch", "case",
                "break", "continue", "return", "yield", "await", "async", "try", "catch",
                "finally", "throw", "new", "this", "super", "import", "export", "default",
                "const", "let", "var", "true", "false", "null", "undefined", "typeof", "instanceof"
            ]
        
        for keyword in keywords:
            completions.append(CompletionSuggestion(
                text=keyword,
                type="keyword",
                description=f"Keyword: {keyword}",
                confidence=0.7,
                context=context.current_scope
            ))
        
        return completions
    
    def _get_import_completions(self, context: CompletionContext) -> List[CompletionSuggestion]:
        """Get import completions"""
        completions = []
        
        # Get current line to check if we're in an import statement
        lines = context.file_path.split('\n')
        current_line_idx = context.cursor_position[0]
        current_line = lines[current_line_idx] if current_line_idx < len(lines) else ""
        
        if context.language == "python":
            if current_line.strip().startswith(('import ', 'from ')):
                # Suggest common Python modules
                common_modules = [
                    "os", "sys", "json", "datetime", "math", "random", "re", "collections",
                    "itertools", "functools", "pathlib", "typing", "asyncio", "threading"
                ]
                
                for module in common_modules:
                    if module not in context.imports:
                        completions.append(CompletionSuggestion(
                            text=module,
                            type="import",
                            description=f"Module: {module}",
                            confidence=0.6,
                            context=context.current_scope
                        ))
        
        return completions
    
    def _get_context_aware_completions(self, context: CompletionContext) -> List[CompletionSuggestion]:
        """Get context-aware completions based on code patterns"""
        completions = []
        
        # Get current line content
        lines = context.file_path.split('\n')
        current_line_idx = context.cursor_position[0]
        current_line = lines[current_line_idx] if current_line_idx < len(lines) else ""
        
        # Pattern-based completions
        if context.language == "python":
            # For loop pattern
            if re.search(r'for\s+\w+\s+in', current_line):
                completions.append(CompletionSuggestion(
                    text="range(",
                    type="pattern",
                    description="For loop with range",
                    confidence=0.8,
                    context=context.current_scope
                ))
                completions.append(CompletionSuggestion(
                    text="enumerate(",
                    type="pattern",
                    description="For loop with enumerate",
                    confidence=0.8,
                    context=context.current_scope
                ))
            
            # List comprehension pattern
            if re.search(r'\[\s*\w+\s+for', current_line):
                completions.append(CompletionSuggestion(
                    text="if ",
                    type="pattern",
                    description="List comprehension condition",
                    confidence=0.7,
                    context=context.current_scope
                ))
            
            # Method call pattern
            if re.search(r'\.\w+\s*$', current_line):
                completions.append(CompletionSuggestion(
                    text="(",
                    type="pattern",
                    description="Method call with arguments",
                    confidence=0.9,
                    context=context.current_scope
                ))
        
        return completions
    
    def _is_accessible(self, var_name: str, context: CompletionContext) -> bool:
        """Check if a variable is accessible in the current scope"""
        # Simplified accessibility check
        # In practice, this would involve proper scope analysis
        return True
    
    def learn_from_user_selection(self, completion: CompletionSuggestion, context: CompletionContext):
        """Learn from user's completion selections"""
        # Store completion selection for future learning
        self.completion_history[context.language].append({
            "context": context,
            "completion": completion,
            "timestamp": datetime.now()
        })
        
        # Update completion model periodically
        if len(self.completion_history[context.language]) > 100:
            self._update_completion_model(context.language)
    
    def _update_completion_model(self, language: str):
        """Update completion model based on user feedback"""
        # Extract features from completion history
        contexts = []
        completions = []
        
        for entry in self.completion_history[language][-100:]:  # Last 100 entries
            contexts.append(entry["context"])
            completions.append(entry["completion"])
        
        # Update vectorizer and embeddings
        if contexts:
            context_texts = [self._context_to_text(ctx) for ctx in contexts]
            self.vectorizer.fit(context_texts)
            self.completion_embeddings = self.vectorizer.transform(context_texts)
    
    def _context_to_text(self, context: CompletionContext) -> str:
        """Convert context to text representation"""
        return f"{context.current_scope} {' '.join(context.variables.keys())} {' '.join(context.functions)} {' '.join(context.classes)}"
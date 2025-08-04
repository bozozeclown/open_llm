# core/analysis.py
import re
from enum import Enum
from typing import Optional
from .analysis.advanced_analyzer import AdvancedCodeAnalyzer

class ContentType(Enum):
    CODE_PYTHON = "code_python"
    CODE_CSHARP = "code_csharp"
    MATH_SYMBOLIC = "math_symbolic"
    TEXT_QUERY = "text_query"

class ContentAnalyzer:
    """
    Legacy content analyzer for basic content type detection.
    This class is kept for backward compatibility.
    For advanced code analysis, use AdvancedCodeAnalyzer.
    """
    
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
    
    def __init__(self, use_advanced: bool = True):
        """
        Initialize the content analyzer.
        
        Args:
            use_advanced: If True, delegate to AdvancedCodeAnalyzer for code analysis
        """
        self.use_advanced = use_advanced
        if use_advanced:
            self.advanced_analyzer = AdvancedCodeAnalyzer()
    
    def analyze(self, text: str, language: str = None) -> ContentType:
        """
        Analyze content and determine its type.
        
        Args:
            text: The text content to analyze
            language: Optional language hint for better analysis
            
        Returns:
            ContentType enum indicating the type of content
        """
        # If advanced analyzer is enabled and language is provided, use it
        if self.use_advanced and language:
            try:
                # Use advanced analyzer for code analysis
                metrics = self.advanced_analyzer.analyze_code(text, language)
                # Map language to content type
                language_to_type = {
                    'python': ContentType.CODE_PYTHON,
                    'csharp': ContentType.CODE_CSHARP
                }
                return language_to_type.get(language.lower(), ContentType.TEXT_QUERY)
            except Exception:
                # Fall back to basic analysis if advanced fails
                pass
        
        # Basic pattern-based analysis
        for content_type, patterns in self.CODE_PATTERNS.items():
            if any(re.search(p, text) for p in patterns):
                return content_type
        
        return ContentType.TEXT_QUERY
    
    def get_detailed_analysis(self, text: str, language: str = None):
        """
        Get detailed analysis using the advanced analyzer if available.
        
        Args:
            text: The text content to analyze
            language: The programming language (required for detailed analysis)
            
        Returns:
            Detailed analysis metrics or None if advanced analyzer is not available
        """
        if not self.use_advanced or not language:
            return None
        
        try:
            return self.advanced_analyzer.analyze_code(text, language)
        except Exception as e:
            print(f"Advanced analysis failed: {e}")
            return None
    
    def generate_improvements(self, text: str, language: str = None):
        """
        Generate code improvements using the advanced analyzer if available.
        
        Args:
            text: The text content to analyze
            language: The programming language (required for improvements)
            
        Returns:
            Improvement suggestions or None if advanced analyzer is not available
        """
        if not self.use_advanced or not language:
            return None
        
        try:
            return self.advanced_analyzer.generate_code_improvements(text, language)
        except Exception as e:
            print(f"Improvement generation failed: {e}")
            return None
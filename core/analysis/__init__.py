# core/analysis/__init__.py
"""
Analysis module for content and code analysis.

This module provides two main analyzers:
1. ContentAnalyzer - Basic content type detection (legacy)
2. AdvancedCodeAnalyzer - Comprehensive code analysis

For new code, prefer using AdvancedCodeAnalyzer directly.
"""

from .advanced_analyzer import (
    AdvancedCodeAnalyzer,
    CodeComplexity,
    CodeSmell,
    CodeIssue,
    CodeMetrics
)

from ..analysis import ContentAnalyzer, ContentType

__all__ = [
    # Advanced analyzer (recommended for new code)
    'AdvancedCodeAnalyzer',
    'CodeComplexity',
    'CodeSmell',
    'CodeIssue',
    'CodeMetrics',
    
    # Legacy analyzer (backward compatibility)
    'ContentAnalyzer',
    'ContentType'
]

# Factory function for creating analyzers
def create_analyzer(use_advanced: bool = True, config_path: str = None):
    """
    Factory function to create the appropriate analyzer.
    
    Args:
        use_advanced: If True, create advanced analyzer (recommended)
        config_path: Path to configuration file (for advanced analyzer)
    
    Returns:
        Analyzer instance
    """
    if use_advanced:
        return AdvancedCodeAnalyzer(config_path)
    else:
        return ContentAnalyzer(use_advanced=False)

def get_recommended_analyzer(task_type: str):
    """
    Get the recommended analyzer for a specific task type.
    
    Args:
        task_type: Type of task ('basic_detection', 'code_analysis', 'code_improvements')
    
    Returns:
        Recommended analyzer class
    """
    recommendations = {
        'basic_detection': ContentAnalyzer,
        'code_analysis': AdvancedCodeAnalyzer,
        'code_improvements': AdvancedCodeAnalyzer
    }
    
    return recommendations.get(task_type, AdvancedCodeAnalyzer)
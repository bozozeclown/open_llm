# core/__init__.py
"""
Core module for the AI Code Assistant.

This module provides the main functionality including:
- Configuration management
- Code analysis
- System validation
"""

from .config_loader import ConfigLoader
from .validation import SystemValidator, validate_system, print_validation_results
from .analysis import (
    AdvancedCodeAnalyzer,
    ContentAnalyzer,
    create_analyzer,
    get_recommended_analyzer,
    CodeComplexity,
    CodeSmell,
    CodeIssue,
    CodeMetrics,
    ContentType
)

__version__ = "0.1.0"
__author__ = "AI Code Assistant Team"

# Export main classes and functions
__all__ = [
    # Configuration
    'ConfigLoader',
    
    # Validation
    'SystemValidator',
    'validate_system',
    'print_validation_results',
    
    # Analysis
    'AdvancedCodeAnalyzer',
    'ContentAnalyzer',
    'create_analyzer',
    'get_recommended_analyzer',
    'CodeComplexity',
    'CodeSmell',
    'CodeIssue',
    'CodeMetrics',
    'ContentType'
]

# Initialize global configuration loader
_config_loader = None

def get_config_loader() -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

def get_analyzer(config_path: str = None) -> AdvancedCodeAnalyzer:
    """Get a configured analyzer instance."""
    return AdvancedCodeAnalyzer(config_path)
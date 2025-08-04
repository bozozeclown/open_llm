# core/validation.py
"""
System validation and health checks.
"""

import os
import sys
from typing import Dict, List, Any, Tuple
from pathlib import Path
from .config_loader import ConfigLoader
from .analysis.advanced_analyzer import AdvancedCodeAnalyzer

class SystemValidator:
    """Validates the entire system configuration and dependencies."""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.issues = []
        self.warnings = []
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        results = {
            "status": "healthy",
            "issues": [],
            "warnings": [],
            "checks": {}
        }
        
        # Run all checks
        checks = [
            ("configuration_files", self._validate_configuration_files),
            ("environment_variables", self._validate_environment_variables),
            ("database_connectivity", self._validate_database_connectivity),
            ("model_configurations", self._validate_model_configurations),
            ("security_settings", self._validate_security_settings),
            ("language_support", self._validate_language_support),
            ("analyzer_functionality", self._validate_analyzer_functionality),
            ("cli_integration", self._validate_cli_integration)
        ]
        
        for check_name, check_func in checks:
            try:
                check_result = check_func()
                results["checks"][check_name] = check_result
                
                if check_result.get("status") == "error":
                    results["status"] = "unhealthy"
                    results["issues"].extend(check_result.get("issues", []))
                elif check_result.get("status") == "warning":
                    results["warnings"].extend(check_result.get("warnings", []))
                    
            except Exception as e:
                results["checks"][check_name] = {
                    "status": "error",
                    "issues": [f"Validation failed: {str(e)}"]
                }
                results["status"] = "unhealthy"
        
        return results
    
    def _validate_configuration_files(self) -> Dict[str, Any]:
        """Validate all configuration files exist and are valid."""
        result = {"status": "healthy", "issues": [], "warnings": []}
        
        required_files = [
            "./configs/base.yaml",
            "./configs/languages.yaml",
            "./configs/quality_standards.yaml",
            "./configs/security.yaml",
            "./configs/database.yaml",
            "./configs/integration.yaml",
            "./configs/model.yaml",
            "./configs/predictions.yaml",
            "./configs/sla_tiers.yaml"
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                result["status"] = "error"
                result["issues"].append(f"Missing configuration file: {file_path}")
        
        return result
    
    def _validate_environment_variables(self) -> Dict[str, Any]:
        """Validate required environment variables."""
        result = {"status": "healthy", "issues": [], "warnings": []}
        
        # Check for required API keys
        required_keys = [
            "GROQ_API_KEY",
            "HF_API_KEY",
            "TEXTGEN_API_KEY"
        ]
        
        missing_keys = []
        for key in required_keys:
            if not os.getenv(key):
                missing_keys.append(key)
        
        if missing_keys:
            result["status"] = "warning"
            result["warnings"].append(f"Missing environment variables: {', '.join(missing_keys)}")
        
        return result
    
    def _validate_database_connectivity(self) -> Dict[str, Any]:
        """Validate database configuration."""
        result = {"status": "healthy", "issues": [], "warnings": []}
        
        try:
            # Test database URL generation
            db_url = self.config_loader.get_database_url("development")
            if not db_url:
                result["status"] = "error"
                result["issues"].append("Failed to generate database URL")
            
            # Test Redis URL generation
            redis_url = self.config_loader.get_redis_url("development")
            if not redis_url:
                result["status"] = "error"
                result["issues"].append("Failed to generate Redis URL")
                
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Database configuration error: {str(e)}")
        
        return result
    
    def _validate_model_configurations(self) -> Dict[str, Any]:
        """Validate model configurations."""
        result = {"status": "healthy", "issues": [], "warnings": []}
        
        try:
            # Check default model
            default_model = self.config_loader.get_default_model()
            if not default_model:
                result["status"] = "error"
                result["issues"].append("No default model configured")
            
            # Check enabled providers
            enabled_providers = self.config_loader.get_enabled_providers()
            if not enabled_providers:
                result["status"] = "warning"
                result["warnings"].append("No providers enabled")
            
            # Check provider configurations
            for provider in enabled_providers:
                config = self.config_loader.get_provider_config(provider)
                if not config:
                    result["status"] = "warning"
                    result["warnings"].append(f"No configuration for provider: {provider}")
                    
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Model configuration error: {str(e)}")
        
        return result
    
    def _validate_security_settings(self) -> Dict[str, Any]:
        """Validate security configurations."""
        result = {"status": "healthy", "issues": [], "warnings": []}
        
        try:
            # Check banned patterns
            banned_patterns = self.config_loader.get_banned_patterns()
            if not banned_patterns:
                result["status"] = "warning"
                result["warnings"].append("No banned patterns configured")
            
            # Check credential patterns
            credential_patterns = self.config_loader.get_credential_patterns()
            if not credential_patterns:
                result["status"] = "warning"
                result["warnings"].append("No credential patterns configured")
            
            # Check security scoring
            scoring_config = self.config_loader.get_security_scoring_config()
            if not scoring_config:
                result["status"] = "warning"
                result["warnings"].append("No security scoring configuration")
                
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Security configuration error: {str(e)}")
        
        return result
    
    def _validate_language_support(self) -> Dict[str, Any]:
        """Validate language support configurations."""
        result = {"status": "healthy", "issues": [], "warnings": []}
        
        try:
            # Check supported languages
            supported_languages = self.config_loader.get_supported_languages()
            if not supported_languages:
                result["status"] = "error"
                result["issues"].append("No supported languages configured")
            
            # Check language detection
            test_file = "./test.py"
            if os.path.exists(test_file):
                detected_lang = self.config_loader.detect_language_from_file(test_file)
                if detected_lang != "python":
                    result["status"] = "warning"
                    result["warnings"].append(f"Language detection failed for {test_file}")
                    
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Language support error: {str(e)}")
        
        return result
    
    def _validate_analyzer_functionality(self) -> Dict[str, Any]:
        """Validate analyzer functionality."""
        result = {"status": "healthy", "issues": [], "warnings": []}
        
        try:
            # Test analyzer initialization
            analyzer = AdvancedCodeAnalyzer()
            
            # Test Python analysis
            python_code = """
def hello_world():
    print("Hello, World!")
    return True
"""
            metrics = analyzer.analyze_code(python_code, "python")
            if not metrics:
                result["status"] = "error"
                result["issues"].append("Python code analysis failed")
            
            # Test JavaScript analysis
            js_code = """
function helloWorld() {
    console.log("Hello, World!");
    return true;
}
"""
            js_metrics = analyzer.analyze_code(js_code, "javascript")
            if not js_metrics:
                result["status"] = "error"
                result["issues"].append("JavaScript code analysis failed")
            
            # Test improvement generation
            improvements = analyzer.generate_code_improvements(python_code, "python")
            if not improvements:
                result["status"] = "warning"
                result["warnings"].append("Code improvement generation failed")
                
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Analyzer functionality error: {str(e)}")
        
        return result
    
    def _validate_cli_integration(self) -> Dict[str, Any]:
        """Validate CLI integration."""
        result = {"status": "healthy", "issues": [], "warnings": []}
        
        try:
            # Check CLI configuration
            from cli.config import CLIConfig
            cli_config = CLIConfig()
            
            # Check required CLI settings
            required_settings = ["api_url", "api_key", "default_language", "default_model"]
            for setting in required_settings:
                if not cli_config.get(setting):
                    result["status"] = "warning"
                    result["warnings"].append(f"Missing CLI setting: {setting}")
            
            # Check CLI validators
            from cli.utils.validators import InputValidator
            validator = InputValidator()
            
            # Test language validation
            if not validator.validate_language("python"):
                result["status"] = "error"
                result["issues"].append("Language validation failed")
                
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"CLI integration error: {str(e)}")
        
        return result

def validate_system() -> Dict[str, Any]:
    """Validate the entire system and return results."""
    validator = SystemValidator()
    return validator.validate_all()

def print_validation_results(results: Dict[str, Any]):
    """Print validation results in a readable format."""
    print("=== System Validation Results ===")
    print(f"Overall Status: {results['status'].upper()}")
    print()
    
    if results['issues']:
        print("❌ Issues:")
        for issue in results['issues']:
            print(f"  - {issue}")
        print()
    
    if results['warnings']:
        print("⚠️  Warnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")
        print()
    
    print("Check Details:")
    for check_name, check_result in results['checks'].items():
        status_icon = "✅" if check_result['status'] == "healthy" else "❌" if check_result['status'] == "error" else "⚠️"
        print(f"  {status_icon} {check_name.replace('_', ' ').title()}: {check_result['status'].upper()}")
        
        if check_result.get('issues'):
            for issue in check_result['issues']:
                print(f"    - {issue}")
        
        if check_result.get('warnings'):
            for warning in check_result['warnings']:
                print(f"    - {warning}")

if __name__ == "__main__":
    results = validate_system()
    print_validation_results(results)
    
    # Exit with appropriate code
    if results['status'] == "unhealthy":
        sys.exit(1)
    elif results['issues']:
        sys.exit(1)
    else:
        sys.exit(0)
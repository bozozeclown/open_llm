# cli/utils/validators.py
import os
import re
from typing import Optional, Dict, Any
from pathlib import Path

class InputValidator:
    """Validate user inputs for CLI commands."""
    
    @staticmethod
    def validate_file_path(file_path: str, must_exist: bool = True) -> bool:
        """Validate file path."""
        path = Path(file_path)
        
        if must_exist and not path.exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        if not path.is_file():
            print(f"❌ Not a file: {file_path}")
            return False
        
        return True
    
    @staticmethod
    def validate_language(language: str) -> bool:
        """Validate programming language."""
        supported_languages = {
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
            'csharp', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin',
            'scala', 'html', 'css', 'sql', 'bash', 'markdown'
        }
        
        if language.lower() not in supported_languages:
            print(f"❌ Unsupported language: {language}")
            print(f"   Supported languages: {', '.join(sorted(supported_languages))}")
            return False
        
        return True
    
    @staticmethod
    def validate_analysis_type(analysis_type: str) -> bool:
        """Validate analysis type."""
        valid_types = ['refactor', 'quality', 'security']
        
        if analysis_type.lower() not in valid_types:
            print(f"❌ Invalid analysis type: {analysis_type}")
            print(f"   Valid types: {', '.join(valid_types)}")
            return False
        
        return True
    
    @staticmethod
    def validate_session_name(name: str) -> bool:
        """Validate session name."""
        if not name or len(name.strip()) == 0:
            print("❌ Session name cannot be empty")
            return False
        
        if len(name) > 100:
            print("❌ Session name too long (max 100 characters)")
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
            print("❌ Session name contains invalid characters")
            print("   Allowed: letters, numbers, spaces, hyphens, and underscores")
            return False
        
        return True
    
    @staticmethod
    def validate_code(code: str, min_length: int = 10) -> bool:
        """Validate code input."""
        if not code or len(code.strip()) == 0:
            print("❌ Code cannot be empty")
            return False
        
        if len(code.strip()) < min_length:
            print(f"❌ Code too short (minimum {min_length} characters)")
            return False
        
        return True
    
    @staticmethod
    def validate_api_url(url: str) -> bool:
        """Validate API URL."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domain
            r'(:[0-9]+)?'  # optional port
            r'(/.*)?$'  # optional path
        )
        
        if not url_pattern.match(url):
            print(f"❌ Invalid API URL: {url}")
            print("   Format: http://example.com or https://example.com:8000")
            return False
        
        return True
    
    @staticmethod
    def validate_version_description(description: str) -> bool:
        """Validate version description."""
        if not description or len(description.strip()) == 0:
            print("❌ Version description cannot be empty")
            return False
        
        if len(description) > 500:
            print("❌ Version description too long (max 500 characters)")
            return False
        
        return True

class ConfigValidator:
    """Validate configuration files."""
    
    @staticmethod
    def validate_config_file(config_path: str) -> bool:
        """Validate configuration file existence and format."""
        if not os.path.exists(config_path):
            print(f"❌ Configuration file not found: {config_path}")
            return False
        
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Basic validation
            if not isinstance(config, dict):
                print("❌ Configuration file must contain a dictionary")
                return False
            
            return True
            
        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML format: {e}")
            return False
        except Exception as e:
            print(f"❌ Error reading configuration file: {e}")
            return False
    
    @staticmethod
    def validate_api_config(config: Dict[str, Any]) -> bool:
        """Validate API configuration."""
        required_keys = ['api_url', 'api_key']
        
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required configuration key: {key}")
                return False
            
            if not config[key]:
                print(f"❌ Configuration key '{key}' cannot be empty")
                return False
        
        # Validate API URL format
        if not InputValidator.validate_api_url(config['api_url']):
            return False
        
        # Validate API key format
        if not InputValidator.validate_api_key(config['api_key']):
            return False
        
        return True
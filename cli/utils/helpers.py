# cli/utils/helpers.py
import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from core.config_loader import ConfigLoader

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        print(f"Error loading config {config_path}: {e}")
        return {}

def save_config(config_path: str, config: Dict[str, Any]) -> bool:
    """Save configuration to YAML file."""
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error saving config {config_path}: {e}")
        return False

def format_output(data: Any, format_type: str = "json") -> str:
    """Format output data."""
    if format_type == "json":
        return json.dumps(data, indent=2)
    elif format_type == "yaml":
        return yaml.dump(data, default_flow_style=False)
    else:
        return str(data)

def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key:
        return False
    # Basic validation - in production, use more sophisticated validation
    return len(api_key) >= 16 and api_key.isalnum()

def get_file_language(file_path: str) -> Optional[str]:
    """Determine programming language from file extension using centralized configuration."""
    config_loader = ConfigLoader()
    return config_loader.detect_language_from_file(file_path)

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def confirm_action(message: str) -> bool:
    """Ask user for confirmation."""
    response = input(f"{message} (y/N): ").strip().lower()
    return response in ['y', 'yes']

def get_user_home() -> Path:
    """Get user home directory."""
    return Path.home()

def create_directory_if_not_exists(path: Path) -> bool:
    """Create directory if it doesn't exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}")
        return False
import os
import json
from pathlib import Path
from typing import Dict, Any

class CLIConfig:
    def __init__(self):
        self.config_dir = Path.home() / ".openllm"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        default_config = {
            "api_url": "http://localhost:8000",
            "api_key": os.getenv("OPENLLM_API_KEY", ""),
            "default_language": "python",
            "timeout": 30
        }
        
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        self.config[key] = value
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
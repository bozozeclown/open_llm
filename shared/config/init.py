import yaml
from pathlib import Path
from typing import Any, Dict

class ConfigManager:
    _config: Dict[str, Any] = {}
    
    @classmethod
    def load_configs(cls, config_dir: str = "shared/config"):
        config_path = Path(config_dir)
        
        for config_file in config_path.glob("*.yaml"):
            with open(config_file) as f:
                cls._config[config_file.stem] = yaml.safe_load(f)
                
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = cls._config
        
        for k in keys:
            value = value.get(k)
            if value is None:
                return default
                
        return value
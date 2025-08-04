# shared/config/manager.py
import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from watchdog.observers import FileSystemObserver
from watchdog.events import FileSystemEventHandler
import threading
import time

class ConfigFileHandler(FileSystemEventHandler):
    """Handle configuration file changes."""
    
    def __init__(self, callback):
        self.callback = callback
    
    def on_modified(self, event):
        if event.src_path.endswith(('.yaml', '.yml', '.json')):
            self.callback(event.src_path)

class ConfigManager:
    """Enhanced configuration manager with hot-reload capability."""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._callbacks: List[callable] = []
        self._observer = None
        self._lock = threading.Lock()
        
        self._load_all_configs()
        self._start_file_watcher()
    
    def _load_all_configs(self):
        """Load all configuration files."""
        config_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))
        
        for config_file in config_files:
            self._load_config_file(config_file)
    
    def _load_config_file(self, config_file: Path):
        """Load a single configuration file."""
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            with self._lock:
                self._configs[config_file.stem] = config
            
            print(f"✅ Loaded configuration: {config_file.stem}")
            
        except Exception as e:
            print(f"❌ Failed to load {config_file}: {e}")
    
    def _start_file_watcher(self):
        """Start watching configuration files for changes."""
        try:
            event_handler = ConfigFileHandler(self._on_config_changed)
            self._observer = FileSystemObserver()
            self._observer.schedule(event_handler, str(self.config_dir))
            self._observer.start()
            
            print(f"👁️ Watching configuration files in {self.config_dir}")
            
        except Exception as e:
            print(f"⚠️ Could not start file watcher: {e}")
    
    def _on_config_changed(self, file_path: str):
        """Handle configuration file changes."""
        config_file = Path(file_path)
        print(f"🔄 Configuration file changed: {config_file.stem}")
        
        # Reload the configuration
        self._load_config_file(config_file)
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(config_file.stem, self.get(config_file.stem))
            except Exception as e:
                print(f"⚠️ Callback error: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        with self._lock:
            keys = key.split('.')
            value = self._configs
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set(self, key: str, value: Any, save: bool = False) -> bool:
        """Set configuration value."""
        with self._lock:
            keys = key.split('.')
            config = self._configs
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
        
        if save:
            return self._save_config(key.split('.')[0])
        
        return True
    
    def _save_config(self, config_name: str) -> bool:
        """Save configuration to file."""
        try:
            config_file = self.config_dir / f"{config_name}.yaml"
            
            with self._lock:
                config = self._configs.get(config_name, {})
            
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print(f"💾 Saved configuration: {config_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save {config_name}: {e}")
            return False
    
    def register_callback(self, callback: callable):
        """Register a callback for configuration changes."""
        self._callbacks.append(callback)
    
    def unregister_callback(self, callback: callable):
        """Unregister a configuration change callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all configurations."""
        with self._lock:
            return self._configs.copy()
    
    def reload_config(self, config_name: str) -> bool:
        """Reload a specific configuration file."""
        config_file = self.config_dir / f"{config_name}.yaml"
        
        if not config_file.exists():
            print(f"❌ Configuration file not found: {config_name}")
            return False
        
        self._load_config_file(config_file)
        return True
    
    def validate_config(self, config_name: str, schema: Dict[str, Any]) -> bool:
        """Validate configuration against schema."""
        config = self.get(config_name, {})
        
        def _validate_recursive(config_part, schema_part, path=""):
            for key, expected_type in schema_part.items():
                if key not in config_part:
                    print(f"❌ Missing required key: {path}.{key}")
                    return False
                
                if isinstance(expected_type, dict):
                    if not isinstance(config_part[key], dict):
                        print(f"❌ Expected dict at {path}.{key}")
                        return False
                    
                    if not _validate_recursive(config_part[key], expected_type, f"{path}.{key}"):
                        return False
                
                elif isinstance(expected_type, list):
                    if not isinstance(config_part[key], list):
                        print(f"❌ Expected list at {path}.{key}")
                        return False
                    
                    # Validate list elements if schema provided
                    if expected_type and len(expected_type) > 0:
                        for i, item in enumerate(config_part[key]):
                            if not isinstance(item, expected_type[0]):
                                print(f"❌ Invalid list element at {path}.{key}[{i}]")
                                return False
                
                elif not isinstance(config_part[key], expected_type):
                    print(f"❌ Expected {expected_type.__name__} at {path}.{key}")
                    return False
            
            return True
        
        return _validate_recursive(config, schema, config_name)
    
    def merge_config(self, config_name: str, override_config: Dict[str, Any]) -> bool:
        """Merge configuration with override values."""
        with self._lock:
            if config_name not in self._configs:
                self._configs[config_name] = {}
            
            def _merge_recursive(base, override):
                for key, value in override.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        _merge_recursive(base[key], value)
                    else:
                        base[key] = value
            
            _merge_recursive(self._configs[config_name], override_config)
        
        return self._save_config(config_name)
    
    def get_config_diff(self, config_name: str, base_config_name: str) -> Dict[str, Any]:
        """Get differences between two configurations."""
        config1 = self.get(config_name, {})
        config2 = self.get(base_config_name, {})
        
        diff = {
            'added': {},
            'removed': {},
            'modified': {},
            'unchanged': {}
        }
        
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            if key not in config1:
                diff['added'][key] = config2[key]
            elif key not in config2:
                diff['removed'][key] = config1[key]
            elif config1[key] != config2[key]:
                diff['modified'][key] = {
                    'old': config1[key],
                    'new': config2[key]
                }
            else:
                diff['unchanged'][key] = config1[key]
        
        return diff
    
    def cleanup(self):
        """Clean up resources."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
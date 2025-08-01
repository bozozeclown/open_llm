from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
import importlib
import logging
from pathlib import Path

# ---------- Core Definitions ----------
@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str = "Unknown"
    compatible_versions: str = ">=0.1.0"
    required_config: Dict[str, Any] = None
    dependencies: List[str] = None
    description: str = ""

class PluginBase(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metadata = self.get_metadata()
        self._initialized = False
        self.logger = logging.getLogger(f"plugin.{self.metadata.name}")
        self._validate_config()

    # ---------- Required Interface ----------
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize plugin resources"""
        pass

    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """Main execution method"""
        pass

    # ---------- Core Functionality ----------
    def is_ready(self) -> bool:
        """Check if plugin is operational"""
        return self._initialized

    def cleanup(self):
        """Release all resources"""
        self._initialized = False
        self.logger.info(f"Cleanup completed for {self.metadata.name}")

    # ---------- Advanced Features ----------
    def _validate_config(self):
        """Validate configuration against metadata requirements"""
        if self.metadata.required_config:
            for field, expected_type in self.metadata.required_config.items():
                if field not in self.config:
                    raise ValueError(f"Missing config field: {field}")
                if not isinstance(self.config[field], expected_type):
                    raise TypeError(
                        f"Config field {field} requires {expected_type}, "
                        f"got {type(self.config[field])}"
                    )

    def health_check(self) -> Dict[str, Any]:
        """Detailed health report"""
        return {
            "name": self.metadata.name,
            "ready": self.is_ready(),
            "config_keys": list(self.config.keys()),
            "dependencies": self.metadata.dependencies or []
        }

    # ---------- Context Manager Support ----------
    def __enter__(self):
        if not self._initialized:
            self._initialized = self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

# ---------- Plugin Manager ----------
class PluginManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.plugins: Dict[str, PluginBase] = {}
        self._discover_plugins()

    def _discover_plugins(self):
        """Discover and initialize all available plugins"""
        plugin_dir = Path(__file__).parent / "integrations"
        for py_file in plugin_dir.glob("*.py"):
            if py_file.stem == "__init__":
                continue
            
            try:
                module = importlib.import_module(
                    f"core.integrations.{py_file.stem}"
                )
                if hasattr(module, "Plugin"):
                    plugin_class = getattr(module, "Plugin")
                    if issubclass(plugin_class, PluginBase):
                        self._load_plugin(plugin_class)
            except Exception as e:
                logging.error(f"Failed to load {py_file.stem}: {str(e)}")

    def _load_plugin(self, plugin_class: Type[PluginBase]):
        """Initialize and register a plugin"""
        plugin_name = plugin_class.__name__.lower()
        plugin_config = self.config.get(plugin_name, {})
        
        try:
            plugin = plugin_class(plugin_config)
            if plugin.initialize():
                self.plugins[plugin_name] = plugin
                logging.info(f"Successfully loaded {plugin_name}")
        except Exception as e:
            logging.error(f"Plugin {plugin_name} failed: {str(e)}")

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Retrieve a loaded plugin by name"""
        return self.plugins.get(name.lower())

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins"""
        return {
            name: {
                "metadata": plugin.metadata,
                "ready": plugin.is_ready()
            }
            for name, plugin in self.plugins.items()
        }
    
    def reload_plugin(self, name: str) -> bool:
        """Hot-reload a plugin by name"""
        if name not in self.plugins:
            return False

        plugin = self.plugins[name]
        plugin.cleanup()
        
        try:
            module = importlib.import_module(f"core.integrations.{name}")
            importlib.reload(module)
            plugin_class = getattr(module, "Plugin")
            self._load_plugin(plugin_class)
            return True
        except Exception as e:
            logging.error(f"Failed to reload {name}: {str(e)}")
            return False

    def _resolve_dependencies(self, metadata: PluginMetadata) -> bool:
        """Install missing dependencies automatically"""
        if not metadata.dependencies:
            return True

        missing = []
        for dep in metadata.dependencies:
            try:
                req = requirements.Requirement(dep)
                importlib.import_module(req.name)
            except (ImportError, requirements.InvalidRequirement):
                missing.append(dep)

        if missing:
            logging.info(f"Installing dependencies: {', '.join(missing)}")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", *missing],
                    stdout=subprocess.DEVNULL
                )
                return True
            except subprocess.CalledProcessError:
                logging.error(f"Failed to install dependencies: {missing}")
                return False
        return True

    def _check_version_compatibility(self, metadata: PluginMetadata) -> bool:
        """Verify plugin matches core version requirements"""
        try:
            core_req = requirements.Requirement(f"open_llm{metadata.compatible_versions}")
            current_version = requirements.Requirement(f"open_llm=={self.config['version']}")
            return current_version.specifier in core_req.specifier
        except requirements.InvalidRequirement:
            logging.warning(f"Invalid version spec: {metadata.compatible_versions}")
            return False

    def _load_plugin(self, plugin_class: Type[PluginBase]):
        """Enhanced plugin loading with new features"""
        metadata = plugin_class({}).get_metadata()
        
        if not self._check_version_compatibility(metadata):
            logging.error(f"Version mismatch for {metadata.name}")
            return

        if not self._resolve_dependencies(metadata):
            logging.error(f"Missing dependencies for {metadata.name}")
            return

        plugin_name = metadata.name.lower()
        plugin_config = self.config.get(plugin_name, {})
        
        try:
            with plugin_class(plugin_config) as plugin:
                if plugin.is_ready():
                    self.plugins[plugin_name] = plugin
                    logging.info(f"Successfully loaded {plugin_name}")
        except Exception as e:
            logging.error(f"Plugin {plugin_name} failed: {str(e)}")
# core/integrations/manager.py
from core.plugin import PluginBase, PluginMetadata
from typing import Dict, Any, List, Optional, Type
from core.monitoring.service import Monitoring
import logging
import importlib
from pathlib import Path
import subprocess
import sys
import requirements

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.plugins: Dict[str, PluginBase] = {}
        self._discover_plugins()
    
    def _discover_plugins(self):
        """Discover and initialize all available plugins"""
        plugin_dir = Path(__file__).parent
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
                logger.error(f"Failed to load {py_file.stem}: {str(e)}")
    
    def _load_plugin(self, plugin_class: Type[PluginBase]):
        """Initialize and register a plugin"""
        plugin_name = plugin_class.__name__.lower()
        plugin_config = self.config.get(plugin_name, {})
        
        try:
            plugin = plugin_class(plugin_config)
            if plugin.initialize():
                self.plugins[plugin_name] = plugin
                logger.info(f"Successfully loaded {plugin_name}")
        except Exception as e:
            logger.error(f"Plugin {plugin_name} failed: {str(e)}")
    
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
            logger.error(f"Failed to reload {name}: {str(e)}")
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
            logger.info(f"Installing dependencies: {', '.join(missing)}")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", *missing],
                    stdout=subprocess.DEVNULL
                )
                return True
            except subprocess.CalledProcessError:
                logger.error(f"Failed to install dependencies: {missing}")
                return False
        return True
    
    def _check_version_compatibility(self, metadata: PluginMetadata) -> bool:
        """Verify plugin matches core version requirements"""
        try:
            core_req = requirements.Requirement(f"open_llm{metadata.compatible_versions}")
            current_version = requirements.Requirement(f"open_llm=={self.config['version']}")
            return current_version.specifier in core_req.specifier
        except requirements.InvalidRequirement:
            logger.warning(f"Invalid version spec: {metadata.compatible_versions}")
            return False
    
    def execute_llm(self, provider: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM request through specified provider"""
        plugin = self.get_plugin(provider)
        if not plugin:
            raise ValueError(f"Provider {provider} not found or not loaded")
        
        return plugin.execute(input_data)
    
    def batch_complete(self, provider: str, prompts: List[str]) -> List[str]:
        """Execute batch completion through specified provider"""
        plugin = self.get_plugin(provider)
        if not plugin:
            raise ValueError(f"Provider {provider} not found or not loaded")
        
        if not plugin.supports_batching:
            # Fallback to sequential execution
            results = []
            for prompt in prompts:
                result = plugin.execute({"prompt": prompt})
                results.append(result.get("response", result.get("result", "")))
            return results
        
        # Execute as batch
        batch_result = plugin.execute({"prompt": prompts})
        return batch_result.get("responses", batch_result.get("results", []))
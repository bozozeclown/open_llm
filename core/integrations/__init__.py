from importlib import import_module
from pathlib import Path
from typing import Dict, Type
from ..plugin import PluginBase

_PLUGINS: Dict[str, Type[PluginBase]] = {}

def _discover_plugins():
    package_dir = Path(__file__).parent
    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        if module_name in ("__init__", "manager"):
            continue
        
        try:
            module = import_module(f".{module_name}", package=__package__)
            if (plugin_class := getattr(module, "Plugin", None)) and \
               issubclass(plugin_class, PluginBase):
                _PLUGINS[module_name] = plugin_class
        except (ImportError, TypeError) as e:
            import warnings
            warnings.warn(f"Failed to load {module_name}: {str(e)}")

def get_plugin(name: str) -> Type[PluginBase]:
    """Get plugin class by name (e.g., 'ollama')"""
    return _PLUGINS[name]  # Will raise KeyError if not found

def available_plugins() -> Dict[str, Type[PluginBase]]:
    """Return copy of registered plugins"""
    return _PLUGINS.copy()

# Initialize on import
import pkgutil
_discover_plugins()

__all__ = ['get_plugin', 'available_plugins']
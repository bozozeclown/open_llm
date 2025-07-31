import importlib
import inspect
from pathlib import Path
from typing import Dict, Type
from .base_module import BaseModule
from core.orchestrator import CapabilityRouter

class ModuleRegistry:
    def __init__(self):
        self._modules: Dict[str, Type[BaseModule]] = {}
        self._instances: Dict[str, BaseModule] = {}
        self.router = CapabilityRouter()
        
    def discover_modules(self, package="modules"):
        """Automatically discover and register all modules"""
        modules_dir = Path(__file__).parent
        
        for module_file in modules_dir.glob("module_*.py"):
            module_name = module_file.stem
            module = importlib.import_module(f"{package}.{module_name}")
            
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseModule) and 
                    obj != BaseModule):
                    self.register_module(obj)
    
    def register_module(self, module_class: Type[BaseModule]):
        """Register a single module class"""
        instance = module_class()
        self._modules[module_class.MODULE_ID] = module_class
        self._instances[module_class.MODULE_ID] = instance
        self.router.register_module(
            instance,
            module_class.CAPABILITIES,
            module_class.PRIORITY
        )
        return instance
        
    def get_module(self, module_id: str) -> BaseModule:
        return self._instances.get(module_id)
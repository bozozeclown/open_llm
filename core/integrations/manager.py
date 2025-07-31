from typing import Dict, Type
import importlib

class IntegrationManager:
    _integrations = {
        "ollama": "core.integrations.ollama.OllamaIntegration",
        "textgen": "core.integrations.textgen.TextGenIntegration",
        "huggingface": "core.integrations.huggingface.HFIntegration"
    }
    
    @classmethod
    def get_integration(cls, name: str, **kwargs) -> AIModelIntegration:
        """Dynamically load and initialize an integration"""
        if name not in cls._integrations:
            raise ValueError(f"Unknown integration: {name}")
        
        module_path, class_name = cls._integrations[name].rsplit('.', 1)
        module = importlib.import_module(module_path)
        integration_class = getattr(module, class_name)
        return integration_class(**kwargs)
    
    @classmethod
    def list_integrations(cls) -> Dict[str, str]:
        """Get available integration names and their classes"""
        return {
            name: path.split('.')[-1] 
            for name, path in cls._integrations.items()
        }
    
    def get_fallback_integration():
    """Try integrations in order until one works"""
    for name in ['ollama', 'textgen', 'vllm']:
        try:
            integration = cls.get_integration(name)
            if integration.validate():
                return integration
        except:
            continue
    raise RuntimeError("No working integration found")
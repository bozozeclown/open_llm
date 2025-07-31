from abc import ABC, abstractmethod
from typing import Dict, Any
import warnings

class AIModelIntegration(ABC):
    """Base class for all external model integrations"""
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Display name of the integrated model"""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> Dict[str, Any]:
        """List available model variants"""
        pass
    
    def validate(self) -> bool:
        """Check if integration is properly configured"""
        try:
            self.generate("test")
            return True
        except Exception as e:
            warnings.warn(f"Validation failed: {str(e)}")
            return False
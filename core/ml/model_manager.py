# core/ml/model_manager.py
import asyncio
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import aiofiles
import aiohttp
from dataclasses import dataclass
from enum import Enum

class ModelStatus(Enum):
    AVAILABLE = "available"
    LOADING = "loading"
    UPDATING = "updating"
    ERROR = "error"

class ModelType(Enum):
    CODE_COMPLETION = "code_completion"
    REFACTORING = "refactoring"
    MULTIMODAL = "multimodal"
    QUALITY_ANALYSIS = "quality_analysis"

@dataclass
class ModelInfo:
    name: str
    type: ModelType
    version: str
    status: ModelStatus
    path: str
    size_mb: float
    created_at: datetime
    last_used: datetime
    performance_metrics: Dict[str, float]
    metadata: Dict[str, Any]

class ModelManager:
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.model_registry: Dict[str, Dict[str, Any]] = {}
        self._load_model_registry()
    
    def _load_model_registry(self):
        """Load model registry from file"""
        registry_file = self.models_dir / "registry.json"
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                self.model_registry = json.load(f)
        else:
            self.model_registry = self._initialize_registry()
            self._save_registry()
    
    def _initialize_registry(self) -> Dict[str, Dict[str, Any]]:
        """Initialize model registry with default models"""
        return {
            "code_completion": {
                "name": "code-completion",
                "type": ModelType.CODE_COMPLETION.value,
                "current_version": "1.0.0",
                "available_versions": ["1.0.0"],
                "download_url": "https://models.example.com/code_completion",
                "description": "Code completion model"
            },
            "refactoring": {
                "name": "refactoring",
                "type": ModelType.REFACTORING.value,
                "current_version": "1.0.0",
                "available_versions": ["1.0.0"],
                "download_url": "https://models.example.com/refactoring",
                "description": "Code refactoring analysis model"
            },
            "multimodal": {
                "name": "multimodal",
                "type": ModelType.MULTIMODAL.value,
                "current_version": "1.0.0",
                "available_versions": ["1.0.0"],
                "download_url": "https://models.example.com/multimodal",
                "description": "Multimodal code analysis model"
            }
        }
    
    def _save_registry(self):
        """Save model registry to file"""
        registry_file = self.models_dir / "registry.json"
        with open(registry_file, 'w') as f:
            json.dump(self.model_registry, f, indent=2)
    
    async def download_model(self, model_type: ModelType, version: str = None) -> bool:
        """Download a model"""
        if model_type.value not in self.model_registry:
            return False
        
        model_info = self.model_registry[model_type.value]
        download_version = version or model_info["current_version"]
        
        # Check if model already exists
        model_path = self.models_dir / f"{model_type.value}_{download_version}"
        if model_path.exists():
            return True
        
        try:
            # Create model directory
            model_path.mkdir(exist_ok=True)
            
            # Download model files
            download_url = f"{model_info['download_url']}/{download_version}"
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{download_url}/model.bin") as response:
                    if response.status == 200:
                        model_file = model_path / "model.bin"
                        async with aiofiles.open(model_file, 'wb') as f:
                            await f.write(await response.read())
                        
                        # Download metadata
                        async with session.get(f"{download_url}/metadata.json") as meta_response:
                            if meta_response.status == 200:
                                metadata_file = model_path / "metadata.json"
                                async with aiofiles.open(metadata_file, 'w') as f:
                                    await f.write(await meta_response.text())
                        
                        return True
            
            return False
        except Exception as e:
            print(f"Failed to download model: {e}")
            return False
    
    async def load_model(self, model_type: ModelType, version: str = None) -> Optional[ModelInfo]:
        """Load a model into memory"""
        if model_type.value not in self.model_registry:
            return None
        
        model_info = self.model_registry[model_type.value]
        load_version = version or model_info["current_version"]
        
        model_path = self.models_dir / f"{model_type.value}_{load_version}"
        if not model_path.exists():
            # Try
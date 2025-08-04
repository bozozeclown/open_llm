# core/config_loader.py
import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigLoader:
    def __init__(self, base_config_path: str = "./configs/base.yaml"):
        self.base_config_path = base_config_path
        self.base_config = self._load_base_config()
        self.quality_standards = self._load_quality_standards()
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load the base configuration file"""
        try:
            with open(self.base_config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Base configuration file not found: {self.base_config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in base configuration: {e}")
    
    def _load_quality_standards(self) -> Dict[str, Any]:
        """Load quality standards configuration"""
        quality_file = self.base_config.get('languages', {}).get('quality_standards_file', './configs/quality_standards.yaml')
        
        try:
            with open(quality_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to default location
            try:
                with open('./configs/quality_standards.yaml', 'r') as f:
                    return yaml.safe_load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"Quality standards configuration file not found")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in quality standards configuration: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get complete configuration with merged quality standards"""
        config = self.base_config.copy()
        config['quality_standards'] = self.quality_standards.get('quality_standards', {})
        return config
    
    def get_language_standards(self, language: str) -> Dict[str, Any]:
        """Get language-specific quality standards"""
        quality_standards = self.quality_standards.get('quality_standards', {})
        language_specific = quality_standards.get('language_specific', {})
        
        # Return language-specific standards or fall back to generic
        return language_specific.get(language.lower(), language_specific.get('generic', {}))
    
    def get_code_smell_thresholds(self, language: str) -> Dict[str, Any]:
        """Get code smell thresholds for a specific language"""
        quality_standards = self.quality_standards.get('quality_standards', {})
        code_smells = quality_standards.get('code_smells', {})
        
        # Create language-specific thresholds
        thresholds = {}
        for smell, values in code_smells.items():
            if isinstance(values, dict):
                thresholds[smell] = values.get(language.lower(), values.get('generic', values))
            else:
                thresholds[smell] = values
        
        return thresholds
    
    def get_severity_levels(self) -> Dict[str, Any]:
        """Get severity level definitions"""
        quality_standards = self.quality_standards.get('quality_standards', {})
        return quality_standards.get('severity_levels', {})
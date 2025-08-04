# core/config_loader.py
import yaml
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

class ConfigLoader:
    def __init__(self, base_config_path: str = "./configs/base.yaml"):
        self.base_config_path = base_config_path
        self.base_config = self._load_base_config()
        self.quality_standards = self._load_quality_standards()
        self.languages_config = self._load_languages_config()
        self.model_config = self._load_model_config()
        self.security_config = self._load_security_config()
        self.database_config = self._load_database_config()
        self.integration_config = self._load_integration_config()
        self._apply_env_overrides()
    
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
    
    def _load_languages_config(self) -> Dict[str, Any]:
        """Load languages configuration"""
        try:
            with open('./configs/languages.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to basic configuration
            return {
                'languages': {
                    'priority': ['python', 'javascript', 'typescript', 'java', 'csharp', 'c', 'cpp'],
                    'settings': {},
                    'detection': {
                        'extension_map': {
                            '.py': 'python',
                            '.js': 'javascript',
                            '.ts': 'typescript',
                            '.java': 'java',
                            '.cs': 'csharp',
                            '.c': 'c',
                            '.cpp': 'cpp'
                        }
                    }
                }
            }
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in languages configuration: {e}")
    
    def _load_model_config(self) -> Dict[str, Any]:
        """Load model configuration"""
        try:
            with open('./configs/model.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to basic configuration
            return {
                'models': {
                    'default_model': 'codellama',
                    'configurations': {},
                    'selection': {'strategy': 'priority'},
                    'caching': {'enabled': True},
                    'performance': {'batch_size': 1}
                }
            }
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in model configuration: {e}")
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration"""
        try:
            with open('./configs/security.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to basic configuration
            return {
                'security': {
                    'api': {
                        'rate_limiting': {'enabled': True, 'requests_per_minute': 100},
                        'api_key': {'min_length': 16}
                    },
                    'application': {
                        'allowed_hosts': ['localhost', '127.0.0.1'],
                        'cors': {'enabled': True}
                    },
                    'code_analysis': {
                        'banned_patterns': ['eval(', 'exec(', 'system('],
                        'credential_patterns': ['password\\s*=\\s*[\"\\'][^\"\\']+[\"\\']']
                    }
                }
            }
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in security configuration: {e}")
    
    def _load_database_config(self) -> Dict[str, Any]:
        """Load database configuration"""
        try:
            with open('./configs/database.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to basic configuration
            return {
                'database': {
                    'default_type': 'postgresql',
                    'environments': {
                        'development': {
                            'host': 'localhost',
                            'port': 5432,
                            'database': 'openllm',
                            'username': 'user',
                            'password': 'password'
                        },
                        'testing': {
                            'host': 'localhost',
                            'port': 5432,
                            'database': 'openllm_test',
                            'username': 'postgres',
                            'password': 'postgres'
                        }
                    },
                    'redis': {
                        'development': {
                            'host': 'localhost',
                            'port': 6379,
                            'db': 0
                        },
                        'testing': {
                            'host': 'localhost',
                            'port': 6379,
                            'db': 1
                        }
                    }
                }
            }
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in database configuration: {e}")
    
    def _load_integration_config(self) -> Dict[str, Any]:
        """Load integration configuration"""
        try:
            with open('./configs/integration.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to basic configuration
            return {
                'plugins': {
                    'ollama': {'enabled': True, 'config': {'default_model': 'codellama'}},
                    'vllm': {'enabled': True, 'config': {'model': 'codellama/CodeLlama-7b-hf'}}
                },
                'settings': {
                    'default_model': 'codellama',
                    'priority_order': ['vllm', 'ollama']
                }
            }
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in integration configuration: {e}")
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        if 'api' not in self.base_config:
            self.base_config['api'] = {}
        
        # Apply timeout overrides from environment
        if os.getenv('DEFAULT_TIMEOUT'):
            self.base_config['api']['default_timeout'] = int(os.getenv('DEFAULT_TIMEOUT'))
        if os.getenv('ANALYSIS_TIMEOUT'):
            self.base_config['api']['analysis_timeout'] = int(os.getenv('ANALYSIS_TIMEOUT'))
        if os.getenv('MAX_TIMEOUT'):
            self.base_config['api']['max_timeout'] = int(os.getenv('MAX_TIMEOUT'))
        
        # Apply default model override from environment
        if os.getenv('DEFAULT_MODEL'):
            # Update both integration and model configs
            if 'settings' not in self.integration_config:
                self.integration_config['settings'] = {}
            self.integration_config['settings']['default_model'] = os.getenv('DEFAULT_MODEL')
            
            if 'models' not in self.model_config:
                self.model_config['models'] = {}
            self.model_config['models']['default_model'] = os.getenv('DEFAULT_MODEL')
    
    def get_config(self) -> Dict[str, Any]:
        """Get complete configuration with merged standards"""
        config = self.base_config.copy()
        config['quality_standards'] = self.quality_standards.get('quality_standards', {})
        config['models'] = self.model_config.get('models', {})
        config['security'] = self.security_config.get('security', {})
        config['database'] = self.database_config.get('database', {})
        config['integration'] = self.integration_config
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
    
    def get_default_timeout(self) -> int:
        """Get the default API timeout"""
        api_config = self.base_config.get('api', {})
        return api_config.get('default_timeout', 30)
    
    def get_analysis_timeout(self) -> int:
        """Get the timeout for analysis requests"""
        api_config = self.base_config.get('api', {})
        return api_config.get('analysis_timeout', 60)
    
    def get_max_timeout(self) -> int:
        """Get the maximum allowed timeout"""
        api_config = self.base_config.get('api', {})
        return api_config.get('max_timeout', 120)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of all supported languages"""
        return self.languages_config.get('languages', {}).get('priority', [])
    
    def get_language_settings(self, language: str) -> Dict[str, Any]:
        """Get language-specific settings"""
        return self.languages_config.get('languages', {}).get('settings', {}).get(language.lower(), {})
    
    def detect_language_from_file(self, file_path: str) -> Optional[str]:
        """Detect programming language from file path"""
        path = Path(file_path)
        extension_map = self.languages_config.get('languages', {}).get('detection', {}).get('extension_map', {})
        
        # Check file extension
        ext = path.suffix.lower()
        if ext in extension_map:
            return extension_map[ext]
        
        # Check shebang for script files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!'):
                    shebang_patterns = self.languages_config.get('languages', {}).get('detection', {}).get('shebang_patterns', {})
                    for lang, patterns in shebang_patterns.items():
                        for pattern in patterns:
                            if pattern in first_line:
                                return lang
        except (FileNotFoundError, UnicodeDecodeError):
            pass
        
        return None
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration"""
        return self.model_config
    
    def get_default_model(self) -> str:
        """Get default model name from integration config"""
        return self.integration_config.get('settings', {}).get('default_model', 'codellama')
    
    def get_model_configuration(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        configurations = self.model_config.get('models', {}).get('configurations', {})
        
        # Find the model configuration
        for model_family, family_config in configurations.items():
            if model_name.lower().startswith(model_family.lower()):
                # Find the specific variant
                for variant in family_config.get('variants', []):
                    if variant['name'].lower() == model_name.lower():
                        return variant
                # Return the first variant if no specific match
                if family_config.get('variants'):
                    return family_config['variants'][0]
        
        # Return empty dict if not found
        return {}
    
    def get_model_paths(self) -> Dict[str, str]:
        """Get model-related paths"""
        return self.model_config.get('models', {}).get('paths', {})
    
    def get_model_caching_config(self) -> Dict[str, Any]:
        """Get model caching configuration"""
        return self.model_config.get('models', {}).get('caching', {})
    
    def get_model_performance_config(self) -> Dict[str, Any]:
        """Get model performance configuration"""
        return self.model_config.get('models', {}).get('performance', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.security_config.get('security', {})
    
    def get_api_security_config(self) -> Dict[str, Any]:
        """Get API security configuration"""
        return self.security_config.get('security', {}).get('api', {})
    
    def get_application_security_config(self) -> Dict[str, Any]:
        """Get application security configuration"""
        return self.security_config.get('security', {}).get('application', {})
    
    def get_code_analysis_security_config(self) -> Dict[str, Any]:
        """Get code analysis security configuration"""
        return self.security_config.get('security', {}).get('code_analysis', {})
    
    def get_banned_patterns(self) -> List[str]:
        """Get banned code patterns"""
        return self.security_config.get('security', {}).get('code_analysis', {}).get('banned_patterns', [])
    
    def get_credential_patterns(self) -> List[str]:
        """Get credential detection patterns"""
        return self.security_config.get('security', {}).get('code_analysis', {}).get('credential_patterns', [])
    
    def get_js_security_patterns(self) -> List[str]:
        """Get JavaScript-specific security patterns"""
        return self.security_config.get('security', {}).get('code_analysis', {}).get('js_patterns', [])
    
    def get_security_scoring_config(self) -> Dict[str, Any]:
        """Get security scoring configuration"""
        return self.security_config.get('security', {}).get('code_analysis', {}).get('scoring', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.database_config.get('database', {})
    
    def get_database_url(self, environment: str = "development") -> str:
        """Get database URL for specified environment"""
        db_config = self.database_config.get('database', {})
        env_config = db_config.get('environments', {}).get(environment, {})
        
        db_type = db_config.get('default_type', 'postgresql')
        host = env_config.get('host', 'localhost')
        port = env_config.get('port', 5432)
        database = env_config.get('database', 'openllm')
        username = env_config.get('username', 'user')
        password = env_config.get('password', 'password')
        
        return f"{db_type}://{username}:{password}@{host}:{port}/{database}"
    
    def get_redis_config(self, environment: str = "development") -> Dict[str, Any]:
        """Get Redis configuration for specified environment"""
        db_config = self.database_config.get('database', {})
        return db_config.get('redis', {}).get(environment, {})
    
    def get_redis_url(self, environment: str = "development") -> str:
        """Get Redis URL for specified environment"""
        redis_config = self.get_redis_config(environment)
        host = redis_config.get('host', 'localhost')
        port = redis_config.get('port', 6379)
        db = redis_config.get('db', 0)
        password = redis_config.get('password', '')
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"
    
    def get_current_environment(self) -> str:
        """Get current environment from environment variables"""
        return os.getenv('ENVIRONMENT', 'development').lower()
    
    def get_integration_config(self) -> Dict[str, Any]:
        """Get integration configuration"""
        return self.integration_config
    
    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled providers"""
        plugins = self.integration_config.get('plugins', {})
        return [name for name, config in plugins.items() if config.get('enabled', False)]
    
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        return self.integration_config.get('plugins', {}).get(provider_name, {}).get('config', {})
    
    def get_provider_priority(self, provider_name: str) -> int:
        """Get priority for a specific provider"""
        priority_order = self.integration_config.get('settings', {}).get('priority_order', [])
        try:
            return priority_order.index(provider_name)
        except ValueError:
            return len(priority_order)  # Lowest priority
    
    def get_routing_rules(self) -> Dict[str, Any]:
        """Get model routing rules"""
        return self.integration_config.get('routing', {})
    
    def get_provider_capabilities(self, provider_name: str) -> Dict[str, Any]:
        """Get capabilities for a specific provider"""
        return self.integration_config.get('capabilities', {}).get(provider_name, {})
    
    def get_best_provider_for_task(self, task: str, language: str = None) -> Optional[str]:
        """Get the best provider for a specific task and language"""
        routing_rules = self.get_routing_rules()
        enabled_providers = self.get_enabled_providers()
        
        # Check task routing
        task_routing = routing_rules.get('task_routing', {})
        if task in task_routing:
            for provider in task_routing[task]:
                if provider in enabled_providers:
                    return provider
        
        # Check language routing
        if language:
            language_routing = routing_rules.get('language_routing', {})
            if language in language_routing:
                for provider in language_routing[language]:
                    if provider in enabled_providers:
                        return provider
        
        # Return highest priority enabled provider
        priority_order = self.integration_config.get('settings', {}).get('priority_order', [])
        for provider in priority_order:
            if provider in enabled_providers:
                return provider
        
        return None
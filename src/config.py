"""
Configuration Management Module
Loads and validates settings from YAML file
"""

import os
import yaml
from typing import Dict, Any, List
from pathlib import Path


class Config:
    """Configuration manager for the chatbot"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to config file (default: config/settings.yaml)
        """
        if config_path is None:
            # Get project root directory
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "settings.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
    
    def _validate_config(self):
        """Validate required configuration fields"""
        required_sections = ['searxng', 'llm', 'cache', 'query_analysis']
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required config section: {section}")
        
        # Validate SearXNG config
        if 'url' not in self._config['searxng']:
            raise ValueError("SearXNG URL not configured")
        
        # Validate LLM config
        if 'url' not in self._config['llm']:
            raise ValueError("LLM URL not configured")
        
        # Create cache directory if it doesn't exist
        cache_dir = Path(self._config['cache']['directory'])
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory if configured
        if 'logging' in self._config and 'file' in self._config['logging']:
            log_dir = Path(self._config['logging']['file']).parent
            log_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., 'searxng.url')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    @property
    def searxng_url(self) -> str:
        """Get SearXNG URL"""
        return self.get('searxng.url')
    
    @property
    def searxng_timeout(self) -> int:
        """Get SearXNG timeout"""
        return self.get('searxng.timeout', 10)
    
    @property
    def searxng_max_results(self) -> int:
        """Get max search results"""
        return self.get('searxng.max_results', 10)
    
    @property
    def llm_url(self) -> str:
        """Get LLM URL"""
        return self.get('llm.url')
    
    @property
    def llm_model(self) -> str:
        """Get LLM model name"""
        return self.get('llm.model')
    
    @property
    def llm_temperature(self) -> float:
        """Get LLM temperature"""
        return self.get('llm.temperature', 0.7)
    
    @property
    def llm_max_tokens(self) -> int:
        """Get LLM max tokens"""
        return self.get('llm.max_tokens', 2000)
    
    @property
    def cache_enabled(self) -> bool:
        """Check if cache is enabled"""
        return self.get('cache.enabled', True)
    
    @property
    def cache_directory(self) -> Path:
        """Get cache directory path"""
        return Path(self.get('cache.directory', './cache'))
    
    @property
    def search_indicators(self) -> Dict[str, List[str]]:
        """Get search indicator keywords"""
        return self.get('query_analysis.search_indicators', {})
    
    @property
    def min_results(self) -> int:
        """Get minimum required results"""
        return self.get('result_processing.min_results', 2)
    
    def __repr__(self) -> str:
        return f"Config(path={self.config_path})"


# Global config instance
_config_instance = None

def get_config(config_path: str = None) -> Config:
    """
    Get or create global config instance
    
    Args:
        config_path: Path to config file
        
    Returns:
        Config instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_path)
    
    return _config_instance

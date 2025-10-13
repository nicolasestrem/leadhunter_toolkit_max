"""
Configuration loader for Lead Hunter Toolkit
Loads and merges configuration from YAML files and settings.json
"""

import os
import yaml
import json
import copy
from typing import Dict, Any, Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
SETTINGS_PATH = BASE_DIR / "settings.json"
VERTICALS_DIR = BASE_DIR / "presets" / "verticals"

# Security limits
MAX_CONFIG_FILE_SIZE = 10 * 1024 * 1024  # 10MB max for config files
MAX_PRESET_FILE_SIZE = 1 * 1024 * 1024   # 1MB max for preset files


def validate_safe_path(base_dir: Path, filename: str, allowed_extensions: list = None) -> Optional[Path]:
    """
    Validate that a filename is safe and doesn't attempt path traversal

    Args:
        base_dir: Base directory that file must reside within
        filename: Filename to validate (should not contain path separators)
        allowed_extensions: Optional list of allowed file extensions (e.g., ['.yml', '.yaml'])

    Returns:
        Resolved Path object if safe, None if validation fails
    """
    # Reject empty filenames
    if not filename or not filename.strip():
        return None

    # Reject path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return None

    # Reject hidden files (starting with .)
    if filename.startswith('.'):
        return None

    # Check extension if specified
    if allowed_extensions:
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return None

    # Construct the full path
    try:
        full_path = (base_dir / filename).resolve()
    except (ValueError, OSError):
        return None

    # Ensure the resolved path is still within base_dir
    try:
        full_path.relative_to(base_dir.resolve())
    except ValueError:
        # Path is outside base_dir
        return None

    return full_path


def safe_file_size(file_path: Path, max_size: int) -> bool:
    """
    Check if file size is within acceptable limits

    Args:
        file_path: Path to file
        max_size: Maximum allowed size in bytes

    Returns:
        True if file size is acceptable, False otherwise
    """
    try:
        return file_path.stat().st_size <= max_size
    except (OSError, FileNotFoundError):
        return False


class ConfigLoader:
    """Load and manage application configuration with cache invalidation"""

    def __init__(self):
        self._models_config = None
        self._defaults_config = None
        self._settings = None
        self._vertical_cache = {}

        # Track file modification times for cache invalidation
        self._file_mtimes = {}

    def _is_file_modified(self, file_path: Path) -> bool:
        """
        Check if file has been modified since last load

        Args:
            file_path: Path to file to check

        Returns:
            True if file was modified or not seen before, False otherwise
        """
        if not file_path.exists():
            return False

        try:
            current_mtime = file_path.stat().st_mtime
            cached_mtime = self._file_mtimes.get(str(file_path))

            if cached_mtime is None or current_mtime > cached_mtime:
                self._file_mtimes[str(file_path)] = current_mtime
                return True

            return False
        except (OSError, FileNotFoundError):
            return False

    def load_models(self) -> Dict[str, Any]:
        """Load model configuration from models.yml with cache invalidation"""
        models_path = CONFIG_DIR / "models.yml"

        # Reload if file was modified or not cached yet
        if self._models_config is None or self._is_file_modified(models_path):
            if models_path.exists():
                with open(models_path, 'r', encoding='utf-8') as f:
                    self._models_config = yaml.safe_load(f) or {}
            else:
                self._models_config = {}

        return self._models_config

    def load_defaults(self) -> Dict[str, Any]:
        """Load default settings from defaults.yml with cache invalidation"""
        defaults_path = CONFIG_DIR / "defaults.yml"

        # Reload if file was modified or not cached yet
        if self._defaults_config is None or self._is_file_modified(defaults_path):
            if defaults_path.exists():
                with open(defaults_path, 'r', encoding='utf-8') as f:
                    self._defaults_config = yaml.safe_load(f) or {}
            else:
                self._defaults_config = {}

        return self._defaults_config

    def load_settings(self) -> Dict[str, Any]:
        """Load runtime settings from settings.json with cache invalidation"""
        # Reload if file was modified or not cached yet
        if self._settings is None or self._is_file_modified(SETTINGS_PATH):
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            else:
                self._settings = {}

        return self._settings

    def get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific model by name or alias

        Args:
            model_name: Model name or alias (e.g., 'gpt-oss-20b', 'classification')

        Returns:
            Dict with model config or None if not found
        """
        models = self.load_models()

        # Check in regular models
        if 'models' in models and model_name in models['models']:
            return models['models'][model_name]

        # Check in ollama models
        if 'ollama_models' in models and model_name in models['ollama_models']:
            return models['ollama_models'][model_name]

        return None

    def get_default_endpoint(self) -> str:
        """Get default LLM endpoint"""
        models = self.load_models()
        return models.get('default_endpoint', 'https://lm.leophir.com/')

    def load_vertical_preset(self, vertical_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a vertical preset configuration from YAML with security validation

        Args:
            vertical_name: Name of vertical (e.g., 'restaurant', 'retail', 'professional_services')

        Returns:
            Dict with vertical configuration or None if not found/invalid
        """
        if not vertical_name:
            return None

        # Validate path security first
        filename = f"{vertical_name}.yml"
        vertical_path = validate_safe_path(VERTICALS_DIR, filename, allowed_extensions=['.yml', '.yaml'])

        if not vertical_path:
            print(f"Security: Rejected invalid vertical preset name '{vertical_name}'")
            return None

        # Check file exists and size is acceptable
        if not vertical_path.exists():
            return None

        # Check cache and file modification time
        if vertical_name in self._vertical_cache and not self._is_file_modified(vertical_path):
            return self._vertical_cache[vertical_name]

        if not safe_file_size(vertical_path, MAX_PRESET_FILE_SIZE):
            print(f"Security: Vertical preset '{vertical_name}' exceeds size limit")
            return None

        # Load and cache
        try:
            with open(vertical_path, 'r', encoding='utf-8') as f:
                vertical_config = yaml.safe_load(f) or {}
            self._vertical_cache[vertical_name] = vertical_config
            return vertical_config
        except (OSError, IOError) as e:
            print(f"Error reading vertical preset file '{vertical_name}': {e}")
            return None
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in vertical preset '{vertical_name}': {e}")
            return None

    def get_active_vertical(self) -> Optional[str]:
        """
        Get name of currently active vertical preset

        Returns:
            Vertical name or None if no vertical is active
        """
        # Check settings.json first
        settings = self.load_settings()
        if 'active_vertical' in settings:
            return settings['active_vertical']

        # Check defaults.yml
        defaults = self.load_defaults()
        if 'vertical' in defaults and 'active' in defaults['vertical']:
            return defaults['vertical']['active']

        return None

    def apply_vertical_overrides(self, config: Dict[str, Any], vertical: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply vertical preset overrides to configuration

        Args:
            config: Base configuration dict
            vertical: Vertical preset dict

        Returns:
            Modified configuration with vertical overrides applied
        """
        if not vertical:
            return config

        # Override scoring weights
        if 'scoring' in vertical:
            if 'scoring' not in config:
                config['scoring'] = {}
            config['scoring'].update(vertical['scoring'])

        # Store vertical context for later use
        if 'vertical' not in config:
            config['vertical'] = {}

        config['vertical']['name'] = vertical.get('vertical')
        config['vertical']['description'] = vertical.get('description')

        # Store outreach customization
        if 'outreach' in vertical:
            config['vertical']['outreach'] = vertical['outreach']

        # Store audit priorities
        if 'audit' in vertical:
            config['vertical']['audit'] = vertical['audit']

        # Store fit rules
        if 'fit_rules' in vertical:
            config['vertical']['fit_rules'] = vertical['fit_rules']

        # Store quick wins templates
        if 'quick_wins' in vertical:
            config['vertical']['quick_wins'] = vertical['quick_wins']

        # Store keywords for classification
        if 'keywords' in vertical:
            config['vertical']['keywords'] = vertical['keywords']

        return config

    def get_merged_config(self) -> Dict[str, Any]:
        """
        Get merged configuration with precedence:
        1. settings.json (highest priority)
        2. vertical presets (if active)
        3. defaults.yml
        4. models.yml

        Returns:
            Merged configuration dictionary
        """
        # Start with deep copy of defaults to avoid mutating cache
        defaults = self.load_defaults()
        config = copy.deepcopy(defaults)

        # Apply vertical preset overrides if active
        active_vertical = self.get_active_vertical()
        if active_vertical:
            vertical_config = self.load_vertical_preset(active_vertical)
            if vertical_config:
                config = self.apply_vertical_overrides(config, vertical_config)

        # Merge models info
        models = self.load_models()
        config['models'] = models

        # Override with settings.json
        settings = self.load_settings()

        # Merge LLM settings
        if 'llm' not in config:
            config['llm'] = {}

        if 'llm_base' in settings:
            config['llm']['base_url'] = settings['llm_base']
        if 'llm_model' in settings:
            config['llm']['model'] = settings['llm_model']
        if 'llm_temperature' in settings:
            config['llm']['temperature'] = settings['llm_temperature']
        if 'llm_top_k' in settings:
            config['llm']['top_k'] = settings['llm_top_k']
        if 'llm_top_p' in settings:
            config['llm']['top_p'] = settings['llm_top_p']
        if 'llm_max_tokens' in settings:
            config['llm']['max_tokens'] = settings['llm_max_tokens']
        if 'llm_key' in settings:
            config['llm']['api_key'] = settings['llm_key']

        # Merge locale settings
        if 'locale' not in config:
            config['locale'] = {}

        if 'language' in settings:
            config['locale']['language'] = settings['language']
        if 'country' in settings:
            config['locale']['country'] = settings['country']
        if 'city' in settings:
            config['locale']['city'] = settings['city']

        # Merge search settings
        if 'search' not in config:
            config['search'] = {}

        if 'search_engine' in settings:
            config['search']['engine'] = settings['search_engine']
        if 'max_sites' in settings:
            config['search']['max_sites'] = settings['max_sites']
        if 'max_pages' in settings:
            config['search']['max_pages'] = settings['max_pages']
        if 'deep_contact' in settings:
            config['search']['deep_contact'] = settings['deep_contact']

        # Merge network settings
        if 'network' not in config:
            config['network'] = {}

        if 'concurrency' in settings:
            config['network']['concurrency'] = settings['concurrency']
        if 'fetch_timeout' in settings:
            config['network']['fetch_timeout'] = settings['fetch_timeout']

        # Merge extraction settings
        if 'extraction' not in config:
            config['extraction'] = {}

        if 'extract_emails' in settings:
            config['extraction']['emails'] = settings['extract_emails']
        if 'extract_phones' in settings:
            config['extraction']['phones'] = settings['extract_phones']
        if 'extract_social' in settings:
            config['extraction']['social'] = settings['extract_social']

        # Merge scoring settings
        if 'scoring' in settings:
            if 'scoring' not in config:
                config['scoring'] = {}
            config['scoring'].update(settings['scoring'])

        # Merge project setting
        if 'project' in settings:
            if 'export' not in config:
                config['export'] = {}
            config['export']['project'] = settings['project']

        # Merge Google API settings
        if 'google_cse_key' in settings or 'google_cse_cx' in settings:
            if 'google' not in config:
                config['google'] = {}
            if 'cse' not in config['google']:
                config['google']['cse'] = {}
            if 'google_cse_key' in settings:
                config['google']['cse']['api_key'] = settings['google_cse_key']
            if 'google_cse_cx' in settings:
                config['google']['cse']['cx'] = settings['google_cse_cx']

        if 'google_places_api_key' in settings:
            if 'google' not in config:
                config['google'] = {}
            if 'places' not in config['google']:
                config['google']['places'] = {}
            config['google']['places']['api_key'] = settings['google_places_api_key']

        if 'google_places_region' in settings:
            if 'google' not in config:
                config['google'] = {}
            if 'places' not in config['google']:
                config['google']['places'] = {}
            config['google']['places']['region'] = settings['google_places_region']

        if 'google_places_language' in settings:
            if 'google' not in config:
                config['google'] = {}
            if 'places' not in config['google']:
                config['google']['places'] = {}
            config['google']['places']['language'] = settings['google_places_language']

        return config

    def reload(self):
        """Clear cached configs to force reload on next access"""
        self._models_config = None
        self._defaults_config = None
        self._settings = None
        self._vertical_cache = {}


# Global instance
_config_loader = ConfigLoader()


def get_config() -> ConfigLoader:
    """Get global config loader instance"""
    return _config_loader


def reload_config():
    """Reload all configuration from disk"""
    _config_loader.reload()

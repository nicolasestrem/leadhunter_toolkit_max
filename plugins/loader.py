"""
Plugin loader for Lead Hunter Toolkit
Dynamically loads plugins from plugins/ directory with health checking and async loading
"""

import os
import importlib.util
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Callable, Any, Dict, Optional
from logger import get_logger

logger = get_logger(__name__)

PLUGINS_DIR = Path(__file__).parent
LOADED_PLUGINS = []
_plugins_lock = threading.Lock()  # Thread-safe access to LOADED_PLUGINS

# Plugin health tracking
MAX_PLUGIN_ERRORS = 5  # Disable plugin after this many consecutive errors
PLUGIN_HEALTH = {}  # {plugin_name: {'errors': int, 'enabled': bool, 'last_error': str}}
_health_lock = threading.Lock()  # Thread-safe access to PLUGIN_HEALTH


def init_plugin_health(plugin_name: str):
    """
    Initialize health tracking for a plugin (thread-safe)

    Args:
        plugin_name: Name of plugin
    """
    with _health_lock:
        if plugin_name not in PLUGIN_HEALTH:
            PLUGIN_HEALTH[plugin_name] = {
                'errors': 0,
                'enabled': True,
                'last_error': None,
                'total_calls': 0,
                'successful_calls': 0
            }


def record_plugin_error(plugin_name: str, error: str):
    """
    Record a plugin error and disable if threshold exceeded (thread-safe)

    Args:
        plugin_name: Name of plugin
        error: Error message
    """
    if plugin_name not in PLUGIN_HEALTH:
        init_plugin_health(plugin_name)

    with _health_lock:
        health = PLUGIN_HEALTH[plugin_name]
        health['errors'] += 1
        health['last_error'] = error

        if health['errors'] >= MAX_PLUGIN_ERRORS and health['enabled']:
            health['enabled'] = False
            logger.error(
                f"Plugin '{plugin_name}' automatically disabled after {health['errors']} consecutive errors. "
                f"Last error: {error}"
            )


def record_plugin_success(plugin_name: str):
    """
    Record a successful plugin call (resets error counter) (thread-safe)

    Args:
        plugin_name: Name of plugin
    """
    if plugin_name not in PLUGIN_HEALTH:
        init_plugin_health(plugin_name)

    with _health_lock:
        health = PLUGIN_HEALTH[plugin_name]
        health['errors'] = 0  # Reset consecutive error count
        health['successful_calls'] += 1


def is_plugin_enabled(plugin_name: str) -> bool:
    """
    Check if plugin is enabled (thread-safe)

    Args:
        plugin_name: Name of plugin

    Returns:
        True if enabled, False otherwise
    """
    with _health_lock:
        if plugin_name not in PLUGIN_HEALTH:
            return True
        return PLUGIN_HEALTH[plugin_name]['enabled']


def enable_plugin(plugin_name: str):
    """
    Manually re-enable a disabled plugin (thread-safe)

    Args:
        plugin_name: Name of plugin
    """
    with _health_lock:
        if plugin_name in PLUGIN_HEALTH:
            PLUGIN_HEALTH[plugin_name]['enabled'] = True
            PLUGIN_HEALTH[plugin_name]['errors'] = 0
            logger.info(f"Plugin '{plugin_name}' manually re-enabled")


def get_plugin_health_status() -> Dict[str, Dict]:
    """
    Get health status of all plugins (thread-safe)

    Returns:
        Dict mapping plugin names to health status
    """
    with _health_lock:
        return PLUGIN_HEALTH.copy()


def _load_single_plugin(filepath: Path) -> Optional[dict]:
    """
    Load a single plugin from a file path (helper for async loading)

    Args:
        filepath: Path to plugin .py file

    Returns:
        Plugin metadata dict or None if loading failed
    """
    plugin_name = filepath.stem

    try:
        # Load module
        spec = importlib.util.spec_from_file_location(plugin_name, filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Check for register function
            if hasattr(module, 'register'):
                logger.info(f"Loading plugin: {plugin_name}")

                # Call register function
                metadata = module.register()

                if metadata:
                    metadata['name'] = plugin_name
                    metadata['path'] = str(filepath)

                    # Initialize health tracking
                    init_plugin_health(plugin_name)

                    logger.info(f"Plugin loaded: {plugin_name}")
                    return metadata
                else:
                    logger.warning(f"Plugin {plugin_name} register() returned None")
            else:
                logger.warning(f"Plugin {plugin_name} has no register() function")

    except Exception as e:
        logger.error(f"Error loading plugin {plugin_name}: {e}", exc_info=True)

    return None


def load_plugins(async_load: bool = True, max_workers: int = 4) -> List[dict]:
    """
    Load all plugins from plugins/ directory

    Supports both synchronous and asynchronous loading.
    Async loading uses ThreadPoolExecutor to load plugins in parallel.

    Plugins must:
    1. Be .py files in plugins/ directory
    2. Implement a register() function
    3. Return plugin metadata dict

    Args:
        async_load: If True, load plugins asynchronously (default: True)
        max_workers: Max threads for async loading (default: 4)

    Returns:
        List of loaded plugin metadata dicts
    """
    # Find all .py files in plugins directory
    plugin_files = [
        filepath for filepath in PLUGINS_DIR.glob("*.py")
        if filepath.name not in ['__init__.py', 'loader.py']
    ]

    if not plugin_files:
        logger.info("No plugins found to load")
        return []

    plugins = []

    if async_load and len(plugin_files) > 1:
        # Async loading with ThreadPoolExecutor
        logger.info(f"Loading {len(plugin_files)} plugins asynchronously with {max_workers} workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all plugin load tasks
            future_to_file = {
                executor.submit(_load_single_plugin, filepath): filepath
                for filepath in plugin_files
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                filepath = future_to_file[future]
                try:
                    metadata = future.result()
                    if metadata:
                        plugins.append(metadata)
                        # Thread-safe append to LOADED_PLUGINS
                        with _plugins_lock:
                            LOADED_PLUGINS.append(metadata)
                except Exception as e:
                    logger.error(f"Error loading plugin {filepath.stem}: {e}", exc_info=True)
    else:
        # Synchronous loading (fallback or single plugin)
        logger.info(f"Loading {len(plugin_files)} plugins synchronously")

        for filepath in plugin_files:
            metadata = _load_single_plugin(filepath)
            if metadata:
                plugins.append(metadata)
                LOADED_PLUGINS.append(metadata)

    logger.info(f"Loaded {len(plugins)} plugins successfully")

    return plugins


def get_loaded_plugins() -> List[dict]:
    """
    Get list of loaded plugins (thread-safe)

    Returns:
        List of plugin metadata dicts
    """
    with _plugins_lock:
        return LOADED_PLUGINS.copy()


def call_plugin_hook(hook_name: str, *args, **kwargs) -> List[Any]:
    """
    Call a hook on all loaded plugins with health checking (thread-safe)

    Automatically tracks plugin health and disables plugins after repeated failures.
    Disabled plugins are skipped until manually re-enabled.

    Args:
        hook_name: Name of hook function
        *args: Positional arguments for hook
        **kwargs: Keyword arguments for hook

    Returns:
        List of results from plugins that implemented the hook
    """
    results = []

    # Get a thread-safe copy of loaded plugins
    with _plugins_lock:
        plugins_to_call = LOADED_PLUGINS.copy()

    for plugin in plugins_to_call:
        plugin_name = plugin['name']

        # Skip disabled plugins
        if not is_plugin_enabled(plugin_name):
            logger.debug(f"Skipping disabled plugin: {plugin_name}")
            continue

        if 'hooks' in plugin and hook_name in plugin['hooks']:
            hook_fn = plugin['hooks'][hook_name]

            # Update total calls counter (thread-safe)
            with _health_lock:
                if plugin_name in PLUGIN_HEALTH:
                    PLUGIN_HEALTH[plugin_name]['total_calls'] += 1

            try:
                logger.debug(f"Calling {hook_name} on plugin {plugin_name}")
                result = hook_fn(*args, **kwargs)
                results.append(result)

                # Record success (resets error counter)
                record_plugin_success(plugin_name)

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Error calling {hook_name} on plugin {plugin_name}: {error_msg}",
                    exc_info=True
                )

                # Record error (may disable plugin)
                record_plugin_error(plugin_name, error_msg)

    return results

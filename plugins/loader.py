"""
Plugin loader for Lead Hunter Toolkit
Dynamically loads plugins from plugins/ directory with health checking
"""

import os
import importlib.util
from pathlib import Path
from typing import List, Callable, Any, Dict
from logger import get_logger

logger = get_logger(__name__)

PLUGINS_DIR = Path(__file__).parent
LOADED_PLUGINS = []

# Plugin health tracking
MAX_PLUGIN_ERRORS = 5  # Disable plugin after this many consecutive errors
PLUGIN_HEALTH = {}  # {plugin_name: {'errors': int, 'enabled': bool, 'last_error': str}}


def init_plugin_health(plugin_name: str):
    """
    Initialize health tracking for a plugin

    Args:
        plugin_name: Name of plugin
    """
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
    Record a plugin error and disable if threshold exceeded

    Args:
        plugin_name: Name of plugin
        error: Error message
    """
    if plugin_name not in PLUGIN_HEALTH:
        init_plugin_health(plugin_name)

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
    Record a successful plugin call (resets error counter)

    Args:
        plugin_name: Name of plugin
    """
    if plugin_name not in PLUGIN_HEALTH:
        init_plugin_health(plugin_name)

    health = PLUGIN_HEALTH[plugin_name]
    health['errors'] = 0  # Reset consecutive error count
    health['successful_calls'] += 1


def is_plugin_enabled(plugin_name: str) -> bool:
    """
    Check if plugin is enabled

    Args:
        plugin_name: Name of plugin

    Returns:
        True if enabled, False otherwise
    """
    if plugin_name not in PLUGIN_HEALTH:
        return True

    return PLUGIN_HEALTH[plugin_name]['enabled']


def enable_plugin(plugin_name: str):
    """
    Manually re-enable a disabled plugin

    Args:
        plugin_name: Name of plugin
    """
    if plugin_name in PLUGIN_HEALTH:
        PLUGIN_HEALTH[plugin_name]['enabled'] = True
        PLUGIN_HEALTH[plugin_name]['errors'] = 0
        logger.info(f"Plugin '{plugin_name}' manually re-enabled")


def get_plugin_health_status() -> Dict[str, Dict]:
    """
    Get health status of all plugins

    Returns:
        Dict mapping plugin names to health status
    """
    return PLUGIN_HEALTH.copy()


def load_plugins() -> List[dict]:
    """
    Load all plugins from plugins/ directory

    Plugins must:
    1. Be .py files in plugins/ directory
    2. Implement a register() function
    3. Return plugin metadata dict

    Returns:
        List of loaded plugin metadata dicts
    """
    plugins = []

    # Find all .py files in plugins directory
    for filepath in PLUGINS_DIR.glob("*.py"):
        # Skip __init__.py and loader.py
        if filepath.name in ['__init__.py', 'loader.py']:
            continue

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
                        plugins.append(metadata)
                        LOADED_PLUGINS.append(metadata)

                        # Initialize health tracking
                        init_plugin_health(plugin_name)

                        logger.info(f"Plugin loaded: {plugin_name}")
                    else:
                        logger.warning(f"Plugin {plugin_name} register() returned None")
                else:
                    logger.warning(f"Plugin {plugin_name} has no register() function")

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}", exc_info=True)

    logger.info(f"Loaded {len(plugins)} plugins")

    return plugins


def get_loaded_plugins() -> List[dict]:
    """
    Get list of loaded plugins

    Returns:
        List of plugin metadata dicts
    """
    return LOADED_PLUGINS.copy()


def call_plugin_hook(hook_name: str, *args, **kwargs) -> List[Any]:
    """
    Call a hook on all loaded plugins with health checking

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

    for plugin in LOADED_PLUGINS:
        plugin_name = plugin['name']

        # Skip disabled plugins
        if not is_plugin_enabled(plugin_name):
            logger.debug(f"Skipping disabled plugin: {plugin_name}")
            continue

        if 'hooks' in plugin and hook_name in plugin['hooks']:
            hook_fn = plugin['hooks'][hook_name]

            # Update total calls counter
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

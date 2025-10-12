"""
Plugin loader for Lead Hunter Toolkit
Dynamically loads plugins from plugins/ directory
"""

import os
import importlib.util
from pathlib import Path
from typing import List, Callable, Any
from logger import get_logger

logger = get_logger(__name__)

PLUGINS_DIR = Path(__file__).parent
LOADED_PLUGINS = []


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
    Call a hook on all loaded plugins

    Args:
        hook_name: Name of hook function
        *args: Positional arguments for hook
        **kwargs: Keyword arguments for hook

    Returns:
        List of results from plugins that implemented the hook
    """
    results = []

    for plugin in LOADED_PLUGINS:
        if 'hooks' in plugin and hook_name in plugin['hooks']:
            hook_fn = plugin['hooks'][hook_name]

            try:
                logger.debug(f"Calling {hook_name} on plugin {plugin['name']}")
                result = hook_fn(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Error calling {hook_name} on plugin {plugin['name']}: {e}",
                    exc_info=True
                )

    return results

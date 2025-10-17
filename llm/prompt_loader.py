"""
Prompt library loader for Lead Hunter Toolkit
Loads and formats prompts from YAML files
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PROMPT_LIBRARY_DIR = BASE_DIR / "llm" / "prompt_library"


def load_prompt(prompt_name: str) -> Dict[str, Any]:
    """Load a prompt configuration from a YAML file.

    This function locates a prompt file by its name within the 'prompt_library' directory,
    parses its YAML content, and returns it as a dictionary.

    Args:
        prompt_name (str): The name of the prompt file, without the '.yml' extension
                           (e.g., 'classify', 'outreach').

    Returns:
        Dict[str, Any]: A dictionary containing the prompt configuration.

    Raises:
        FileNotFoundError: If the specified prompt file does not exist.
    """
    prompt_path = PROMPT_LIBRARY_DIR / f"{prompt_name}.yml"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config or {}


def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template with the provided variables.

    This function uses Python's string formatting to substitute placeholders in the
    template with their corresponding values from keyword arguments.

    Args:
        template (str): The prompt template string, containing placeholders like {variable}.
        **kwargs: The variables to substitute into the template.

    Returns:
        str: The fully formatted prompt string.
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing template variable: {e}")


def get_classification_prompt(lead_data: Dict[str, Any]) -> tuple[str, str]:
    """Get the formatted classification prompts, including both system and user prompts.

    This function loads the 'classify' prompt template, populates it with lead data,
    and returns the structured prompts ready for use with an LLM.

    Args:
        lead_data (Dict[str, Any]): A dictionary containing the lead data.

    Returns:
        tuple[str, str]: A tuple containing the system prompt and the user prompt.
    """
    config = load_prompt('classify')

    system_prompt = config.get('system_prompt', '')

    # Get user prompt template
    user_template = config.get('user_prompt_template', '')

    # Prepare data for template
    template_data = {
        'company_name': lead_data.get('name', 'Unknown'),
        'website': lead_data.get('website', ''),
        'domain': lead_data.get('domain', ''),
        'city': lead_data.get('city', ''),
        'country': lead_data.get('country', ''),
        'emails': ', '.join(lead_data.get('emails', [])) or 'None',
        'phones': ', '.join(lead_data.get('phones', [])) or 'None',
        'social': ', '.join([f"{k}: {v}" for k, v in lead_data.get('social', {}).items()]) or 'None',
        'content_sample': lead_data.get('content_sample', '')[:500],  # First 500 chars
        'has_https': str(lead_data.get('website', '').startswith('https://')),
        'content_length': len(lead_data.get('content_sample', ''))
    }

    user_prompt = format_prompt(user_template, **template_data)

    return system_prompt, user_prompt


def get_outreach_prompt(lead_data: Dict[str, Any], language: str = 'en', style: str = 'professional') -> tuple[str, str]:
    """Get the formatted outreach prompts.

    Note: The implementation of this function will be completed in the 'outreach' module.

    Args:
        lead_data (Dict[str, Any]): A dictionary of lead data.
        language (str): The target language (e.g., 'en', 'fr', 'de').
        style (str): The desired writing style or voice.

    Returns:
        tuple[str, str]: A tuple of the system and user prompts.
    """
    config = load_prompt('outreach')
    # Implementation will be completed in outreach module
    return "", ""


def get_dossier_prompt(lead_data: Dict[str, Any], pages_content: str) -> tuple[str, str]:
    """Get the formatted prompts for building a dossier.

    Note: The implementation of this function will be completed in the 'dossier' module.

    Args:
        lead_data (Dict[str, Any]): A dictionary of lead data.
        pages_content (str): The aggregated content from crawled pages.

    Returns:
        tuple[str, str]: A tuple of the system and user prompts.
    """
    config = load_prompt('dossier')
    # Implementation will be completed in dossier module
    return "", ""


def get_audit_prompt(page_data: Dict[str, Any]) -> tuple[str, str]:
    """Get the formatted prompts for an audit.

    Note: The implementation of this function will be completed in the 'audit' module.

    Args:
        page_data (Dict[str, Any]): A dictionary of page analysis data.

    Returns:
        tuple[str, str]: A tuple of the system and user prompts.
    """
    config = load_prompt('audit')
    # Implementation will be completed in audit module
    return "", ""

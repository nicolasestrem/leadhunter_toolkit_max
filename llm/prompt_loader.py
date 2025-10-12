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
    """
    Load prompt configuration from YAML file

    Args:
        prompt_name: Name of the prompt file (without .yml extension)
                    e.g., 'classify', 'outreach', 'dossier'

    Returns:
        Dict containing prompt configuration

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_path = PROMPT_LIBRARY_DIR / f"{prompt_name}.yml"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config or {}


def format_prompt(template: str, **kwargs) -> str:
    """
    Format prompt template with provided variables

    Args:
        template: Prompt template string with {variable} placeholders
        **kwargs: Variables to substitute into template

    Returns:
        Formatted prompt string
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing template variable: {e}")


def get_classification_prompt(lead_data: Dict[str, Any]) -> tuple[str, str]:
    """
    Get formatted classification prompts (system + user)

    Args:
        lead_data: Lead data dict with all required fields

    Returns:
        Tuple of (system_prompt, user_prompt)
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
    """
    Get formatted outreach prompts

    Args:
        lead_data: Lead data dict
        language: Target language (en, fr, de)
        style: Writing style/voice

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    config = load_prompt('outreach')
    # Implementation will be completed in outreach module
    return "", ""


def get_dossier_prompt(lead_data: Dict[str, Any], pages_content: str) -> tuple[str, str]:
    """
    Get formatted dossier building prompts

    Args:
        lead_data: Lead data dict
        pages_content: Aggregated content from crawled pages

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    config = load_prompt('dossier')
    # Implementation will be completed in dossier module
    return "", ""


def get_audit_prompt(page_data: Dict[str, Any]) -> tuple[str, str]:
    """
    Get formatted audit prompts

    Args:
        page_data: Page analysis data

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    config = load_prompt('audit')
    # Implementation will be completed in audit module
    return "", ""

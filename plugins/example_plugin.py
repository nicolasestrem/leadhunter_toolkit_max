"""
Example plugin for Lead Hunter Toolkit

This demonstrates the plugin API. Plugins can:
1. Add custom menu items to Streamlit app
2. Hook into workflow events
3. Extend functionality

To create a plugin:
1. Create a .py file in plugins/
2. Implement a register() function that returns metadata
3. Plugin will be auto-loaded on app start
"""

from typing import Dict, Any


def register() -> Dict[str, Any]:
    """Register the plugin with the main application.

    This function is the entry point for the plugin system. It returns a dictionary
    containing the plugin's metadata, including its version, description, and the
    hooks it implements.

    Returns:
        Dict[str, Any]: A dictionary of the plugin's metadata.
    """
    return {
        'version': '1.0.0',
        'description': 'Example plugin demonstrating the plugin API',
        'author': 'Lead Hunter Team',

        # Hooks: Functions called at specific points
        'hooks': {
            'before_classification': before_classification_hook,
            'after_classification': after_classification_hook,
            'before_outreach': before_outreach_hook,
            'after_outreach': after_outreach_hook,
        },

        # Menu items: Add custom UI elements
        'menu_items': [
            {
                'label': 'Example Plugin Action',
                'callback': example_action,
                'icon': '🔌'
            }
        ]
    }


def before_classification_hook(lead_data: dict) -> dict:
    """An example hook that is called before a lead is classified.

    This function provides an opportunity to pre-process or modify the lead data
    before it is sent for classification.

    Args:
        lead_data (dict): The lead data dictionary.

    Returns:
        dict: The (potentially modified) lead data.
    """
    # Example: Pre-process lead data before classification
    # Could add custom fields, normalize data, etc.
    return lead_data


def after_classification_hook(lead_record: dict) -> dict:
    """An example hook that is called after a lead has been classified.

    This function can be used to post-process the lead record, such as by adding
    custom tags based on the classification scores.

    Args:
        lead_record (dict): The LeadRecord dictionary.

    Returns:
        dict: The (potentially modified) lead record.
    """
    # Example: Add a custom tag based on score
    if lead_record.get('score_fit', 0) >= 9:
        if 'tags' not in lead_record:
            lead_record['tags'] = []

        if 'high-fit' not in lead_record['tags']:
            lead_record['tags'].append('high-fit')

    return lead_record


def before_outreach_hook(lead_data: dict, message_type: str) -> dict:
    """An example hook that is called before outreach generation.

    This function can be used to add custom context to the lead data, which can then
    be used in the outreach prompts.

    Args:
        lead_data (dict): The lead data dictionary.
        message_type (str): The type of message being generated (e.g., 'email').

    Returns:
        dict: The (potentially modified) lead data.
    """
    # Example: Add custom context for specific business types
    if lead_data.get('business_type') == 'restaurant':
        lead_data['custom_note'] = 'Focus on online reservations and Google My Business'

    return lead_data


def after_outreach_hook(result_dict: dict, lead_data: dict) -> None:
    """An example hook that is called after outreach has been generated.

    This is an informational hook that can be used for logging, analytics, or
    triggering external actions like updating a CRM.

    Args:
        result_dict (dict): A dictionary representing the outreach result.
        lead_data (dict): The lead data dictionary.
    """
    # Example: Log outreach generation for analytics
    # Could send to analytics service, update CRM, etc.
    pass


def example_action():
    """An example of a menu action that can be triggered from the Streamlit UI."""
    print("Example plugin action triggered!")
    return "Plugin action executed successfully"


# You can add more functions, classes, utilities, etc.
# Only the register() function is required for plugin discovery

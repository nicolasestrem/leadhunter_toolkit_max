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
    """
    Plugin registration function

    Returns:
        Dict with plugin metadata:
        {
            'version': '1.0.0',
            'description': 'Plugin description',
            'hooks': {
                'hook_name': hook_function,
                ...
            },
            'menu_items': [
                {
                    'label': 'Menu Item',
                    'callback': function
                },
                ...
            ]
        }
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
    """
    Called before a lead is classified

    Args:
        lead_data: Lead data dict

    Returns:
        Modified lead_data (or original if no changes)
    """
    # Example: Pre-process lead data before classification
    # Could add custom fields, normalize data, etc.
    return lead_data


def after_classification_hook(lead_record: dict) -> dict:
    """
    Called after a lead is classified

    Args:
        lead_record: LeadRecord dict

    Returns:
        Modified lead_record (or original if no changes)
    """
    # Example: Add a custom tag based on score
    if lead_record.get('score_fit', 0) >= 9:
        if 'tags' not in lead_record:
            lead_record['tags'] = []

        if 'high-fit' not in lead_record['tags']:
            lead_record['tags'].append('high-fit')

    return lead_record


def before_outreach_hook(lead_data: dict, message_type: str) -> dict:
    """
    Called before outreach generation

    Args:
        lead_data: Lead data dict
        message_type: Type of message (email, linkedin, sms)

    Returns:
        Modified lead_data (or original if no changes)
    """
    # Example: Add custom context for specific business types
    if lead_data.get('business_type') == 'restaurant':
        lead_data['custom_note'] = 'Focus on online reservations and Google My Business'

    return lead_data


def after_outreach_hook(result_dict: dict, lead_data: dict) -> None:
    """
    Called after outreach generation

    Args:
        result_dict: Outreach result dict with variants
        lead_data: Lead data dict

    Returns:
        None (informational hook for logging/analytics)
    """
    # Example: Log outreach generation for analytics
    # Could send to analytics service, update CRM, etc.
    pass


def example_action():
    """
    Example menu action

    This would be called when user clicks the menu item in Streamlit
    """
    print("Example plugin action triggered!")
    return "Plugin action executed successfully"


# You can add more functions, classes, utilities, etc.
# Only the register() function is required for plugin discovery

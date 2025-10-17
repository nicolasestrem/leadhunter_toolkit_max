"""
Internationalization (i18n) support
Handles language switching and tone presets
"""

from typing import Dict, Any, Optional

# Supported languages
SUPPORTED_LANGUAGES = ['en', 'fr', 'de']

# Language configurations
LANGUAGE_CONFIGS = {
    'en': {
        'name': 'English',
        'country_code': 'us',
        'date_format': '%m/%d/%Y',
        'time_format': '%I:%M %p',
        'currency_symbol': '$',
        'decimal_separator': '.',
        'thousand_separator': ',',
        'phone_format': '+1-XXX-XXX-XXXX',
    },
    'fr': {
        'name': 'Français',
        'country_code': 'fr',
        'date_format': '%d/%m/%Y',
        'time_format': '%H:%M',
        'currency_symbol': '€',
        'decimal_separator': ',',
        'thousand_separator': ' ',
        'phone_format': '+33 X XX XX XX XX',
    },
    'de': {
        'name': 'Deutsch',
        'country_code': 'de',
        'date_format': '%d.%m.%Y',
        'time_format': '%H:%M',
        'currency_symbol': '€',
        'decimal_separator': ',',
        'thousand_separator': '.',
        'phone_format': '+49 XXX XXXXXXX',
    }
}

# Communication tone presets per language
TONE_PRESETS = {
    'en': {
        'professional': {
            'greeting': 'Dear',
            'closing': 'Best regards',
            'formality': 'formal',
            'description': 'Professional and respectful tone'
        },
        'friendly': {
            'greeting': 'Hi',
            'closing': 'Cheers',
            'formality': 'casual',
            'description': 'Warm and approachable tone'
        },
        'direct': {
            'greeting': 'Hello',
            'closing': 'Thanks',
            'formality': 'neutral',
            'description': 'Direct and efficient tone'
        }
    },
    'fr': {
        'professional': {
            'greeting': 'Madame, Monsieur',
            'closing': 'Cordialement',
            'formality': 'formal',
            'description': 'Ton professionnel et respectueux'
        },
        'friendly': {
            'greeting': 'Bonjour',
            'closing': 'Bien à vous',
            'formality': 'casual',
            'description': 'Ton chaleureux et accessible'
        },
        'direct': {
            'greeting': 'Bonjour',
            'closing': 'Merci',
            'formality': 'neutral',
            'description': 'Ton direct et efficace'
        }
    },
    'de': {
        'professional': {
            'greeting': 'Sehr geehrte Damen und Herren',
            'closing': 'Mit freundlichen Grüßen',
            'formality': 'formal',
            'description': 'Professioneller und respektvoller Ton'
        },
        'friendly': {
            'greeting': 'Hallo',
            'closing': 'Viele Grüße',
            'formality': 'casual',
            'description': 'Warmer und zugänglicher Ton'
        },
        'direct': {
            'greeting': 'Guten Tag',
            'closing': 'Danke',
            'formality': 'neutral',
            'description': 'Direkter und effizienter Ton'
        }
    }
}

# Common UI strings
UI_STRINGS = {
    'en': {
        'email_subject': 'Subject',
        'email_body': 'Body',
        'save': 'Save',
        'export': 'Export',
        'cancel': 'Cancel',
        'delete': 'Delete',
        'edit': 'Edit',
        'search': 'Search',
        'filter': 'Filter',
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'no_results': 'No results found',
        'select_language': 'Select language',
        'select_country': 'Select country',
        'select_city': 'Select city',
    },
    'fr': {
        'email_subject': 'Objet',
        'email_body': 'Corps',
        'save': 'Enregistrer',
        'export': 'Exporter',
        'cancel': 'Annuler',
        'delete': 'Supprimer',
        'edit': 'Modifier',
        'search': 'Rechercher',
        'filter': 'Filtrer',
        'loading': 'Chargement...',
        'error': 'Erreur',
        'success': 'Succès',
        'no_results': 'Aucun résultat trouvé',
        'select_language': 'Sélectionner la langue',
        'select_country': 'Sélectionner le pays',
        'select_city': 'Sélectionner la ville',
    },
    'de': {
        'email_subject': 'Betreff',
        'email_body': 'Nachricht',
        'save': 'Speichern',
        'export': 'Exportieren',
        'cancel': 'Abbrechen',
        'delete': 'Löschen',
        'edit': 'Bearbeiten',
        'search': 'Suchen',
        'filter': 'Filtern',
        'loading': 'Lädt...',
        'error': 'Fehler',
        'success': 'Erfolg',
        'no_results': 'Keine Ergebnisse gefunden',
        'select_language': 'Sprache auswählen',
        'select_country': 'Land auswählen',
        'select_city': 'Stadt auswählen',
    }
}


def get_language_config(language: str) -> Dict[str, Any]:
    """Get the configuration for a specific language.

    This function retrieves the language-specific settings, such as date formats,
    currency symbols, and separators. It falls back to English if the requested
    language is not supported.

    Args:
        language (str): The language code (e.g., 'en', 'fr', 'de').

    Returns:
        Dict[str, Any]: A dictionary containing the language configuration.
    """
    language = language.lower()
    if language not in LANGUAGE_CONFIGS:
        language = 'en'  # Fallback to English

    return LANGUAGE_CONFIGS[language]


def get_tone_preset(language: str, tone: str = 'professional') -> Dict[str, str]:
    """Get the tone preset for a specific language and tone.

    This function provides the appropriate greetings, closings, and formality levels
    for a given communication style. It defaults to English and a professional tone
    if the requested language or tone is not available.

    Args:
        language (str): The language code (e.g., 'en', 'fr', 'de').
        tone (str): The name of the tone (e.g., 'professional', 'friendly').

    Returns:
        Dict[str, str]: A dictionary containing the tone preset.
    """
    language = language.lower()
    if language not in TONE_PRESETS:
        language = 'en'

    if tone not in TONE_PRESETS[language]:
        tone = 'professional'

    return TONE_PRESETS[language][tone]


def get_available_tones(language: str) -> Dict[str, Dict[str, str]]:
    """Get all available tones for a given language.

    Args:
        language (str): The language code.

    Returns:
        Dict[str, Dict[str, str]]: A dictionary where keys are tone names and values
                                   are the corresponding tone presets.
    """
    language = language.lower()
    if language not in TONE_PRESETS:
        language = 'en'

    return TONE_PRESETS[language]


def translate_string(key: str, language: str) -> str:
    """Translate a UI string using a key and a target language.

    This function looks up a string in the UI_STRINGS dictionary. If a translation
    is not found, it returns the key itself as a fallback.

    Args:
        key (str): The key of the string to translate.
        language (str): The target language.

    Returns:
        str: The translated string, or the key if no translation is found.
    """
    language = language.lower()
    if language not in UI_STRINGS:
        language = 'en'

    return UI_STRINGS[language].get(key, key)


def format_message(
    template: str,
    language: str,
    tone: str = 'professional',
    **kwargs
) -> str:
    """Format a message template with language and tone-specific elements.

    This function injects tone-specific greetings and closings into the template
    before formatting it with the provided keyword arguments.

    Args:
        template (str): The message template.
        language (str): The target language.
        tone (str): The communication tone.
        **kwargs: The variables to substitute into the template.

    Returns:
        str: The formatted message.
    """
    tone_preset = get_tone_preset(language, tone)

    # Add tone-specific variables to kwargs
    kwargs['greeting'] = tone_preset['greeting']
    kwargs['closing'] = tone_preset['closing']

    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing template variable: {e}")


def get_language_name(language_code: str) -> str:
    """Get the display name for a given language code.

    Args:
        language_code (str): The language code (e.g., 'en', 'fr', 'de').

    Returns:
        str: The display name of the language.
    """
    config = get_language_config(language_code)
    return config.get('name', language_code.upper())


def is_language_supported(language_code: str) -> bool:
    """Check if a language is supported by the application.

    Args:
        language_code (str): The language code to check.

    Returns:
        bool: True if the language is supported, False otherwise.
    """
    return language_code.lower() in SUPPORTED_LANGUAGES


def get_default_language() -> str:
    """Get the default language code for the application.

    Returns:
        str: The default language code, which is 'en'.
    """
    return 'en'

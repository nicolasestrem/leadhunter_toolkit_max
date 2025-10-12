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
    """
    Get configuration for a language

    Args:
        language: Language code (en, fr, de)

    Returns:
        Language configuration dict
    """
    language = language.lower()
    if language not in LANGUAGE_CONFIGS:
        language = 'en'  # Fallback to English

    return LANGUAGE_CONFIGS[language]


def get_tone_preset(language: str, tone: str = 'professional') -> Dict[str, str]:
    """
    Get tone preset for a language

    Args:
        language: Language code (en, fr, de)
        tone: Tone name (professional, friendly, direct)

    Returns:
        Tone preset dict
    """
    language = language.lower()
    if language not in TONE_PRESETS:
        language = 'en'

    if tone not in TONE_PRESETS[language]:
        tone = 'professional'

    return TONE_PRESETS[language][tone]


def get_available_tones(language: str) -> Dict[str, Dict[str, str]]:
    """
    Get all available tones for a language

    Args:
        language: Language code

    Returns:
        Dict of tone name to tone preset
    """
    language = language.lower()
    if language not in TONE_PRESETS:
        language = 'en'

    return TONE_PRESETS[language]


def translate_string(key: str, language: str) -> str:
    """
    Translate a UI string

    Args:
        key: String key
        language: Target language

    Returns:
        Translated string or key if not found
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
    """
    Format a message with language and tone

    Args:
        template: Message template
        language: Target language
        tone: Communication tone
        **kwargs: Template variables

    Returns:
        Formatted message
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
    """
    Get display name for language code

    Args:
        language_code: Language code (en, fr, de)

    Returns:
        Display name of language
    """
    config = get_language_config(language_code)
    return config.get('name', language_code.upper())


def is_language_supported(language_code: str) -> bool:
    """
    Check if language is supported

    Args:
        language_code: Language code to check

    Returns:
        True if supported, False otherwise
    """
    return language_code.lower() in SUPPORTED_LANGUAGES


def get_default_language() -> str:
    """
    Get default language code

    Returns:
        Default language code (en)
    """
    return 'en'

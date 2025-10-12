"""
Locale-specific formatting functions
Handles phone numbers, currency, dates, and other locale-specific formats
"""

import re
from datetime import datetime
from typing import Optional, Dict
from locale.i18n import get_language_config


def format_phone(phone: str, country: str = 'de') -> str:
    """
    Format phone number according to country conventions

    Args:
        phone: Raw phone number
        country: Country code (de, fr, us, etc.)

    Returns:
        Formatted phone number
    """
    # Remove all non-digit characters for processing
    digits = re.sub(r'\D', '', phone)

    country = country.lower()

    # Country-specific formatting
    if country == 'de':
        # German format: +49 XXX XXXXXXX or +49 XX XXXXXXXX
        if digits.startswith('49'):
            digits = digits[2:]  # Remove country code
            if len(digits) >= 10:
                return f"+49 {digits[:3]} {digits[3:]}"
            elif len(digits) >= 9:
                return f"+49 {digits[:2]} {digits[2:]}"
        elif digits.startswith('0'):
            # Domestic format
            if len(digits) >= 10:
                return f"+49 {digits[1:4]} {digits[4:]}"
            elif len(digits) >= 9:
                return f"+49 {digits[1:3]} {digits[3:]}"

    elif country == 'fr':
        # French format: +33 X XX XX XX XX
        if digits.startswith('33'):
            digits = digits[2:]  # Remove country code
            if len(digits) == 9:
                return f"+33 {digits[0]} {digits[1:3]} {digits[3:5]} {digits[5:7]} {digits[7:9]}"
        elif digits.startswith('0'):
            # Domestic format
            digits = digits[1:]  # Remove leading 0
            if len(digits) == 9:
                return f"+33 {digits[0]} {digits[1:3]} {digits[3:5]} {digits[5:7]} {digits[7:9]}"

    elif country in ['us', 'en']:
        # US/English format: +1 (XXX) XXX-XXXX
        if digits.startswith('1'):
            digits = digits[1:]  # Remove country code
        if len(digits) == 10:
            return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    # Fallback: international format with country code
    if len(digits) > 6:
        return f"+{digits}"

    return phone  # Return original if can't format


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to E.164 format (+XXXXXXXXXXX)

    Args:
        phone: Input phone number

    Returns:
        Normalized phone number
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)

    # Add + if not present
    if not digits.startswith('+'):
        digits = '+' + digits

    return digits


def format_currency(amount: float, language: str = 'en') -> str:
    """
    Format currency according to language conventions

    Args:
        amount: Amount to format
        language: Language code (en, fr, de)

    Returns:
        Formatted currency string
    """
    config = get_language_config(language)

    symbol = config.get('currency_symbol', '€')
    decimal_sep = config.get('decimal_separator', '.')
    thousand_sep = config.get('thousand_separator', ',')

    # Format number with appropriate separators
    whole = int(amount)
    decimal = int((amount - whole) * 100)

    # Add thousand separators
    whole_str = f"{whole:,}".replace(',', thousand_sep)

    # Build final string
    if language == 'en':
        # Symbol before amount: $1,234.56
        return f"{symbol}{whole_str}{decimal_sep}{decimal:02d}"
    else:
        # Symbol after amount: 1.234,56 €
        return f"{whole_str}{decimal_sep}{decimal:02d} {symbol}"


def format_date(
    date: datetime,
    language: str = 'en',
    include_time: bool = False
) -> str:
    """
    Format date according to language conventions

    Args:
        date: Datetime object to format
        language: Language code (en, fr, de)
        include_time: Whether to include time

    Returns:
        Formatted date string
    """
    config = get_language_config(language)

    date_format = config.get('date_format', '%Y-%m-%d')
    time_format = config.get('time_format', '%H:%M')

    if include_time:
        return date.strftime(f"{date_format} {time_format}")
    else:
        return date.strftime(date_format)


def format_address(
    street: str,
    city: str,
    postal_code: str,
    country: str,
    language: str = 'en'
) -> str:
    """
    Format address according to country conventions

    Args:
        street: Street address
        city: City name
        postal_code: Postal/ZIP code
        country: Country code
        language: Language code for formatting

    Returns:
        Formatted address string
    """
    country = country.lower()

    if country == 'de':
        # German format: Street, Postal Code City
        return f"{street}\n{postal_code} {city}\nDeutschland"

    elif country == 'fr':
        # French format: Street, Postal Code City
        return f"{street}\n{postal_code} {city}\nFrance"

    elif country in ['us', 'en']:
        # US format: Street, City, State ZIP
        return f"{street}\n{city}\nUSA"

    else:
        # Generic format
        return f"{street}\n{postal_code} {city}\n{country.upper()}"


def format_number(number: float, language: str = 'en', decimals: int = 2) -> str:
    """
    Format number according to language conventions

    Args:
        number: Number to format
        language: Language code (en, fr, de)
        decimals: Number of decimal places

    Returns:
        Formatted number string
    """
    config = get_language_config(language)

    decimal_sep = config.get('decimal_separator', '.')
    thousand_sep = config.get('thousand_separator', ',')

    # Split into whole and decimal parts
    whole = int(number)
    decimal = int((number - whole) * (10 ** decimals))

    # Format whole part with thousand separators
    whole_str = f"{whole:,}".replace(',', thousand_sep)

    # Build final string
    if decimals > 0:
        return f"{whole_str}{decimal_sep}{decimal:0{decimals}d}"
    else:
        return whole_str


def format_percentage(value: float, language: str = 'en', decimals: int = 1) -> str:
    """
    Format percentage according to language conventions

    Args:
        value: Percentage value (0-100)
        language: Language code
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    num_str = format_number(value, language, decimals)

    if language in ['fr', 'de']:
        return f"{num_str} %"  # Space before %
    else:
        return f"{num_str}%"  # No space


def parse_phone(phone_str: str) -> Optional[Dict[str, str]]:
    """
    Parse phone number into components

    Args:
        phone_str: Phone number string

    Returns:
        Dict with country_code, area_code, number or None
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone_str)

    if not digits:
        return None

    # Try to parse as international format
    if len(digits) >= 10:
        # Assume first 1-3 digits are country code
        if len(digits) >= 11:  # Likely has country code
            return {
                'country_code': digits[:2],
                'area_code': digits[2:5] if len(digits) > 9 else digits[2:4],
                'number': digits[5:] if len(digits) > 9 else digits[4:],
                'full': digits
            }
        else:  # Likely no country code
            return {
                'country_code': '',
                'area_code': digits[:3],
                'number': digits[3:],
                'full': digits
            }

    return None


def format_business_hours(
    open_time: str,
    close_time: str,
    language: str = 'en'
) -> str:
    """
    Format business hours according to language conventions

    Args:
        open_time: Opening time (e.g., "09:00")
        close_time: Closing time (e.g., "17:00")
        language: Language code

    Returns:
        Formatted business hours string
    """
    if language == 'de':
        return f"{open_time} - {close_time} Uhr"
    elif language == 'fr':
        return f"{open_time} - {close_time}"
    else:  # English
        # Convert to 12-hour format
        try:
            open_dt = datetime.strptime(open_time, '%H:%M')
            close_dt = datetime.strptime(close_time, '%H:%M')
            return f"{open_dt.strftime('%I:%M %p')} - {close_dt.strftime('%I:%M %p')}"
        except:
            return f"{open_time} - {close_time}"

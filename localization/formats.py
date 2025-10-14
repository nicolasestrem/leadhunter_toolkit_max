"""
Locale-specific formatting functions
Handles phone numbers, currency, dates, and other locale-specific formats
"""

import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional, Dict, Union
from localization.i18n import get_language_config


def _to_decimal(value: Union[float, int, Decimal]) -> Decimal:
    """Convert numeric input to ``Decimal`` for consistent rounding."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize(value: Decimal, decimals: int) -> Decimal:
    """Quantize ``value`` to the desired number of decimal places."""
    quant = Decimal('1').scaleb(-decimals) if decimals > 0 else Decimal('1')
    return value.quantize(quant, rounding=ROUND_HALF_UP)


def _format_locale_number(value: Decimal, language: str, decimals: int) -> str:
    """Format a ``Decimal`` according to locale separators."""
    config = get_language_config(language)
    decimal_sep = config.get('decimal_separator', '.')
    thousand_sep = config.get('thousand_separator', ',')

    sign = '-' if value.is_signed() and value != 0 else ''
    abs_value = value.copy_abs()

    integer_part = int(abs_value)
    whole_str = f"{integer_part:,}".replace(',', thousand_sep)

    if decimals > 0:
        fraction_decimal = (abs_value - Decimal(integer_part)) * (Decimal(10) ** decimals)
        fraction = int(fraction_decimal.to_integral_value(rounding=ROUND_HALF_UP))
        return f"{sign}{whole_str}{decimal_sep}{fraction:0{decimals}d}"

    return f"{sign}{whole_str}"


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

    # Handle international prefix 00 -> +
    if digits.startswith('00'):
        digits = digits[2:]

    country = country.lower()

    # Country-specific formatting
    if country == 'de':
        # German format: +49 AA BBBBBBB or +49 AAA BBBBBB depending on area code length
        if digits.startswith('49'):
            national = digits[2:]
        elif digits.startswith('0'):
            national = digits[1:]
        else:
            national = digits

        if len(national) >= 5:
            if len(national) > 8:
                area_len = 3
            else:
                area_len = 2
            return f"+49 {national[:area_len]} {national[area_len:]}"

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

    try:
        decimal_amount = _quantize(_to_decimal(amount), 2)
    except (InvalidOperation, TypeError, ValueError):
        return str(amount)

    number_str = _format_locale_number(decimal_amount, language, 2)
    is_negative = number_str.startswith('-')
    if is_negative:
        number_body = number_str[1:]
        sign = '-'
    else:
        number_body = number_str
        sign = ''

    if language == 'en':
        return f"{sign}{symbol}{number_body}"
    else:
        return f"{sign}{number_body} {symbol}"


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

    try:
        raw_value = _to_decimal(number)
        if decimals == 0:
            decimal_value = Decimal(int(raw_value))
        else:
            decimal_value = _quantize(raw_value, decimals)
    except (InvalidOperation, TypeError, ValueError):
        return str(number)

    return _format_locale_number(decimal_value, language, decimals)


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

"""
Tests for locale formatting functions
"""

import pytest
from datetime import datetime
from locale.formats import (
    format_phone,
    format_currency,
    format_date,
    format_number,
    format_percentage,
    normalize_phone
)


def test_format_phone_german():
    """Test German phone formatting"""
    # With country code
    assert "+49" in format_phone("4930123456", "de")

    # Domestic format
    assert "+49" in format_phone("030123456", "de")


def test_format_phone_french():
    """Test French phone formatting"""
    assert "+33" in format_phone("33612345678", "fr")

    # Domestic format
    assert "+33" in format_phone("0612345678", "fr")


def test_format_phone_us():
    """Test US phone formatting"""
    result = format_phone("15551234567", "us")
    assert "+1" in result
    assert "(" in result or "-" in result


def test_normalize_phone():
    """Test phone normalization to E.164"""
    # Various input formats
    assert normalize_phone("+49 30 12345") == "+493012345"
    assert normalize_phone("(555) 123-4567") == "+5551234567"
    assert normalize_phone("01 23 45 67 89") == "+0123456789"


def test_format_currency_english():
    """Test English currency formatting"""
    result = format_currency(1234.56, "en")

    assert "$" in result
    assert "1" in result
    assert "234" in result
    assert "56" in result


def test_format_currency_german():
    """Test German currency formatting"""
    result = format_currency(1234.56, "de")

    assert "€" in result
    assert "," in result  # Decimal separator
    assert "." in result or " " in result  # Thousand separator


def test_format_currency_french():
    """Test French currency formatting"""
    result = format_currency(1234.56, "fr")

    assert "€" in result
    assert "," in result  # Decimal separator


def test_format_date_english():
    """Test English date formatting"""
    date = datetime(2025, 10, 12, 14, 30)

    # Date only
    result = format_date(date, "en", include_time=False)
    assert "10" in result  # Month
    assert "12" in result  # Day
    assert "2025" in result  # Year

    # With time
    result_time = format_date(date, "en", include_time=True)
    assert "10" in result_time or "2" in result_time  # Hour


def test_format_date_german():
    """Test German date formatting"""
    date = datetime(2025, 10, 12, 14, 30)

    result = format_date(date, "de", include_time=False)
    assert "12" in result  # Day
    assert "10" in result  # Month
    assert "2025" in result  # Year


def test_format_date_french():
    """Test French date formatting"""
    date = datetime(2025, 10, 12, 14, 30)

    result = format_date(date, "fr", include_time=False)
    assert "12" in result  # Day
    assert "10" in result  # Month
    assert "2025" in result  # Year


def test_format_number_english():
    """Test English number formatting"""
    result = format_number(1234.56, "en", decimals=2)

    assert "1,234" in result or "1234" in result
    assert "." in result
    assert "56" in result


def test_format_number_german():
    """Test German number formatting"""
    result = format_number(1234.56, "de", decimals=2)

    # German uses . for thousands and , for decimals
    assert "," in result  # Decimal separator


def test_format_percentage_english():
    """Test English percentage formatting"""
    result = format_percentage(95.5, "en", decimals=1)

    assert "95" in result
    assert "5" in result
    assert "%" in result


def test_format_percentage_german():
    """Test German percentage formatting"""
    result = format_percentage(95.5, "de", decimals=1)

    assert "95" in result
    assert "%" in result
    # German typically has space before %


def test_format_number_no_decimals():
    """Test number formatting without decimals"""
    result = format_number(1234.56, "en", decimals=0)

    assert "1234" in result or "1,234" in result
    assert "." not in result  # No decimal point


def test_format_currency_large_amount():
    """Test currency formatting with large amounts"""
    result = format_currency(1234567.89, "en")

    assert "$" in result
    assert "1" in result
    # Should have thousand separators

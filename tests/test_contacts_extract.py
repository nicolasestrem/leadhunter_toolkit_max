"""
Tests for contact extraction from markdown
"""

import pytest
from leads.contacts_extract import (
    extract_emails,
    extract_phones,
    extract_social_links,
    extract_company_name,
    extract_contacts_from_markdown,
    merge_contact_info
)


def test_extract_emails(sample_markdown_content):
    """Test email extraction from markdown"""
    emails = extract_emails(sample_markdown_content)

    assert len(emails) == 2
    assert 'info@test-restaurant.de' in emails
    assert 'reservations@test-restaurant.de' in emails


def test_extract_phones(sample_markdown_content):
    """Test phone extraction from markdown"""
    phones = extract_phones(sample_markdown_content)

    assert len(phones) >= 1
    # Phone should be extracted in some format
    assert any('+49' in phone or '030' in phone for phone in phones)


def test_extract_social_links(sample_markdown_content):
    """Test social media link extraction"""
    social = extract_social_links(sample_markdown_content)

    assert 'facebook' in social
    assert 'testrestaurant' in social['facebook']

    assert 'instagram' in social
    assert 'testrestaurant' in social['instagram']

    assert 'twitter' in social
    assert 'testrestaurant' in social['twitter']


def test_extract_company_name(sample_markdown_content):
    """Test company name extraction from H1"""
    name = extract_company_name(sample_markdown_content)

    assert name == 'Test Restaurant Berlin'


def test_extract_contacts_full(sample_markdown_content):
    """Test full contact extraction"""
    contacts = extract_contacts_from_markdown(sample_markdown_content)

    assert 'emails' in contacts
    assert 'phones' in contacts
    assert 'social' in contacts
    assert 'company_name' in contacts
    assert 'address' in contacts

    assert len(contacts['emails']) >= 2
    assert len(contacts['phones']) >= 1
    assert len(contacts['social']) >= 2
    assert contacts['company_name'] == 'Test Restaurant Berlin'


def test_extract_emails_no_emails():
    """Test email extraction with no emails present"""
    text = "This is just plain text with no emails."
    emails = extract_emails(text)

    assert emails == []


def test_extract_phones_various_formats():
    """Test phone extraction with various formats"""
    text = """
    Phone formats:
    +49 30 12345678
    (555) 123-4567
    555-123-4567
    +1-555-123-4567
    """
    phones = extract_phones(text)

    assert len(phones) >= 3


def test_extract_social_links_no_links():
    """Test social extraction with no links"""
    text = "This text has no social media links."
    social = extract_social_links(text)

    assert social == {}


def test_extract_social_links_url_formats():
    """Test social extraction with various URL formats"""
    text = """
    Follow us:
    https://www.facebook.com/mycompany
    https://instagram.com/mycompany
    https://linkedin.com/company/mycompany
    https://twitter.com/mycompany
    """
    social = extract_social_links(text)

    assert 'facebook' in social
    assert 'instagram' in social
    assert 'linkedin' in social
    assert 'twitter' in social


def test_merge_contact_info():
    """Test merging two contact info dicts"""
    existing = {
        'emails': ['old@example.com'],
        'phones': ['+49 30 111111'],
        'social': {'facebook': 'https://facebook.com/old'},
        'company_name': 'Old Company'
    }

    new = {
        'emails': ['new@example.com', 'old@example.com'],  # One duplicate
        'phones': ['+49 30 222222'],
        'social': {'instagram': 'https://instagram.com/new'},
        'address': 'New Address 123'
    }

    merged = merge_contact_info(existing, new)

    # Should have both emails (deduplicated)
    assert len(merged['emails']) == 2
    assert 'old@example.com' in merged['emails']
    assert 'new@example.com' in merged['emails']

    # Should have both phones
    assert len(merged['phones']) == 2

    # Should have both social links
    assert 'facebook' in merged['social']
    assert 'instagram' in merged['social']

    # Should keep existing company name
    assert merged['company_name'] == 'Old Company'

    # Should add new address
    assert merged['address'] == 'New Address 123'


def test_merge_contact_info_override_empty():
    """Test that merge replaces empty values"""
    existing = {
        'company_name': '',
        'address': ''
    }

    new = {
        'company_name': 'New Company',
        'address': 'New Address'
    }

    merged = merge_contact_info(existing, new)

    assert merged['company_name'] == 'New Company'
    assert merged['address'] == 'New Address'

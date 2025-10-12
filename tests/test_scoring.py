"""
Tests for enhanced scoring system
"""

import pytest
from models import Lead, Social
from leads.classify_score import (
    calculate_quality_score,
    calculate_priority_score
)


def test_calculate_quality_score_complete_lead():
    """Test quality score with complete lead data"""
    lead_data = {
        'name': 'Test Company',
        'emails': ['info@test.com', 'sales@test.com'],
        'phones': ['+49 30 12345', '+49 30 67890'],
        'social': {
            'facebook': 'https://facebook.com/test',
            'instagram': 'https://instagram.com/test',
            'linkedin': 'https://linkedin.com/company/test'
        },
        'address': '123 Test St, Berlin',
        'city': 'Berlin',
        'website': 'https://test.com'
    }

    score = calculate_quality_score(lead_data)

    # Should have high quality score
    assert score >= 8.0
    assert score <= 10.0


def test_calculate_quality_score_minimal_lead():
    """Test quality score with minimal lead data"""
    lead_data = {
        'emails': ['info@test.com'],
        'website': 'http://test.com'
    }

    score = calculate_quality_score(lead_data)

    # Should have low quality score
    assert score >= 2.0
    assert score <= 4.0


def test_calculate_quality_score_no_https():
    """Test quality score penalizes HTTP sites"""
    lead_data_https = {
        'name': 'Test',
        'emails': ['test@test.com'],
        'website': 'https://test.com'
    }

    lead_data_http = {
        'name': 'Test',
        'emails': ['test@test.com'],
        'website': 'http://test.com'
    }

    score_https = calculate_quality_score(lead_data_https)
    score_http = calculate_quality_score(lead_data_http)

    assert score_https > score_http


def test_calculate_priority_score_high_priority():
    """Test priority calculation for high-value lead"""
    priority = calculate_priority_score(
        quality_score=9.0,
        fit_score=9.0,
        quality_signals=['Complete contact', 'Professional design', 'Social active'],
        issue_flags=[]
    )

    # Should be high priority
    assert priority >= 7.0
    assert priority <= 10.0


def test_calculate_priority_score_with_issues():
    """Test that issues reduce priority score"""
    priority_no_issues = calculate_priority_score(
        quality_score=8.0,
        fit_score=8.0,
        quality_signals=['Complete contact'],
        issue_flags=[]
    )

    priority_with_issues = calculate_priority_score(
        quality_score=8.0,
        fit_score=8.0,
        quality_signals=['Complete contact'],
        issue_flags=['No SSL', 'Thin content', 'Poor mobile']
    )

    assert priority_no_issues > priority_with_issues


def test_calculate_priority_score_quality_signals_bonus():
    """Test that quality signals increase priority"""
    priority_few_signals = calculate_priority_score(
        quality_score=7.0,
        fit_score=7.0,
        quality_signals=['Complete contact'],
        issue_flags=[]
    )

    priority_many_signals = calculate_priority_score(
        quality_score=7.0,
        fit_score=7.0,
        quality_signals=['Complete contact', 'Professional design', 'Social active', 'Good SEO'],
        issue_flags=[]
    )

    assert priority_many_signals > priority_few_signals


def test_calculate_priority_score_bounds():
    """Test that priority score stays within 0-10 range"""
    # Try to create extreme scores
    priority_max = calculate_priority_score(
        quality_score=10.0,
        fit_score=10.0,
        quality_signals=['sig1', 'sig2', 'sig3', 'sig4', 'sig5'],
        issue_flags=[]
    )

    priority_min = calculate_priority_score(
        quality_score=0.0,
        fit_score=0.0,
        quality_signals=[],
        issue_flags=['issue1', 'issue2', 'issue3', 'issue4', 'issue5']
    )

    assert 0.0 <= priority_max <= 10.0
    assert 0.0 <= priority_min <= 10.0


def test_quality_score_email_weighting():
    """Test email count affects quality score appropriately"""
    score_no_email = calculate_quality_score({'emails': []})
    score_one_email = calculate_quality_score({'emails': ['test@test.com']})
    score_two_emails = calculate_quality_score({'emails': ['test1@test.com', 'test2@test.com']})

    assert score_no_email < score_one_email < score_two_emails


def test_quality_score_phone_weighting():
    """Test phone count affects quality score"""
    score_no_phone = calculate_quality_score({'phones': []})
    score_one_phone = calculate_quality_score({'phones': ['+49 30 12345']})
    score_two_phones = calculate_quality_score({'phones': ['+49 30 12345', '+49 30 67890']})

    assert score_no_phone < score_one_phone < score_two_phones


def test_quality_score_social_weighting():
    """Test social media count affects quality score"""
    score_no_social = calculate_quality_score({'social': {}})
    score_one_social = calculate_quality_score({'social': {'facebook': 'https://facebook.com/test'}})
    score_three_social = calculate_quality_score({
        'social': {
            'facebook': 'https://facebook.com/test',
            'instagram': 'https://instagram.com/test',
            'linkedin': 'https://linkedin.com/company/test'
        }
    })

    assert score_no_social < score_one_social < score_three_social

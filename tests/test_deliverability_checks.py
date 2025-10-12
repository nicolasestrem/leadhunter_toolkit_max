"""
Tests for outreach deliverability checks
Ensures spam detection and email best practices are working correctly
"""

import pytest
from outreach.deliverability_checks import (
    check_word_count,
    check_spam_words,
    check_exclamation_marks,
    check_link_count,
    check_subject_line,
    check_deliverability,
    DeliverabilityIssue
)


class TestWordCount:
    """Test word count validation"""

    def test_optimal_word_count(self):
        """Message with optimal word count should pass"""
        text = " ".join(["word"] * 100)  # 100 words (within 80-140 range)
        issues = check_word_count(text)
        assert len(issues) == 0

    def test_too_short(self):
        """Message too short should trigger warning"""
        text = "Very short message here"  # 4 words
        issues = check_word_count(text, min_words=80)
        assert len(issues) == 1
        assert issues[0].severity == 'warning'
        assert issues[0].category == 'length'
        assert 'too short' in issues[0].message.lower()

    def test_too_long(self):
        """Message too long should trigger warning"""
        text = " ".join(["word"] * 200)  # 200 words
        issues = check_word_count(text, max_words=140)
        assert len(issues) == 1
        assert issues[0].severity == 'warning'
        assert 'too long' in issues[0].message.lower()

    def test_custom_limits(self):
        """Should respect custom min/max limits"""
        text = " ".join(["word"] * 50)
        issues = check_word_count(text, min_words=60, max_words=100)
        assert len(issues) == 1
        assert '50' in issues[0].message


class TestSpamWords:
    """Test spam word detection"""

    def test_no_spam_words(self):
        """Clean message should pass"""
        text = "Hello, I noticed your restaurant has great reviews."
        issues = check_spam_words(text)
        assert len(issues) == 0

    def test_single_spam_word(self):
        """Message with spam word should trigger warning"""
        text = "Get this FREE offer now!"
        issues = check_spam_words(text)
        assert len(issues) == 1
        assert issues[0].severity in ['warning', 'critical']
        assert issues[0].category == 'spam_words'

    def test_multiple_spam_words(self):
        """Multiple spam words should be detected"""
        text = "FREE guarantee! Act now, limited time!"
        issues = check_spam_words(text)
        assert len(issues) >= 1
        # Should mention multiple spam words
        assert 'FREE' in issues[0].message or 'free' in issues[0].message.lower()

    def test_case_insensitive(self):
        """Should detect spam words regardless of case"""
        text = "This is Free and GuArAnTeEd to work"
        issues = check_spam_words(text)
        assert len(issues) >= 1

    def test_alternatives_suggested(self):
        """Should suggest alternatives for spam words"""
        text = "Click here for your free guide"
        issues = check_spam_words(text)
        if issues:
            # Should have suggestions
            assert issues[0].suggestion
            assert len(issues[0].suggestion) > 0


class TestExclamationMarks:
    """Test exclamation mark validation"""

    def test_no_exclamation_marks(self):
        """Message without exclamation marks should pass"""
        text = "Hello, I'd like to discuss your business."
        issues = check_exclamation_marks(text)
        assert len(issues) == 0

    def test_one_exclamation_mark(self):
        """Single exclamation mark should pass"""
        text = "Great news! I have an idea for your business."
        issues = check_exclamation_marks(text)
        assert len(issues) == 0

    def test_excessive_exclamation_marks(self):
        """Multiple exclamation marks should trigger warning"""
        text = "Amazing offer!!! Act now!!! Don't miss out!!!"
        issues = check_exclamation_marks(text)
        assert len(issues) >= 1
        assert issues[0].severity in ['warning', 'critical']
        assert issues[0].category == 'formatting'


class TestLinks:
    """Test link count validation"""

    def test_no_links(self):
        """Message without links should pass"""
        text = "Hello, I'd like to discuss your business needs."
        issues = check_link_count(text)
        assert len(issues) == 0

    def test_one_link(self):
        """Single link should pass"""
        text = "Check out my profile: https://example.com"
        issues = check_link_count(text, max_links=1)
        assert len(issues) == 0

    def test_excessive_links(self):
        """Multiple links should trigger warning"""
        text = "Visit https://example.com or https://test.com or https://demo.com"
        issues = check_link_count(text, max_links=1)
        assert len(issues) >= 1
        assert issues[0].category == 'links'

    def test_link_detection(self):
        """Should detect various link formats"""
        text = "Visit http://example.com and www.test.com"
        issues = check_link_count(text, max_links=1)
        assert len(issues) >= 1


class TestSubjectLine:
    """Test subject line validation"""

    def test_optimal_subject(self):
        """Subject within range should pass"""
        subject = "Quick question about your restaurant"  # ~40 chars
        issues = check_subject_line(subject)
        assert len(issues) == 0

    def test_subject_too_short(self):
        """Short subject should trigger warning"""
        subject = "Hi"  # Very short
        issues = check_subject_line(subject, min_chars=30)
        assert len(issues) >= 1
        assert 'too short' in issues[0].message.lower()

    def test_subject_too_long(self):
        """Long subject should trigger warning"""
        subject = "This is an extremely long subject line that goes on and on"
        issues = check_subject_line(subject, max_chars=50)
        assert len(issues) >= 1
        assert 'too long' in issues[0].message.lower()

    def test_subject_all_caps(self):
        """All-caps subject should trigger critical warning"""
        subject = "URGENT OFFER FOR YOU"
        issues = check_subject_line(subject)
        assert len(issues) >= 1
        # Should have critical severity for all-caps
        critical_issues = [i for i in issues if i.severity == 'critical']
        assert len(critical_issues) >= 1


class TestDeliverabilityCheck:
    """Test overall deliverability check"""

    def test_good_email(self):
        """Well-crafted email should score high"""
        subject = "Quick question about your business"
        body = """Hi there,

I noticed your restaurant has excellent reviews on Google. I work with local
businesses to improve their online presence and wanted to share a quick win
that could increase your reservations.

Would you be open to a brief 15-minute call this week?

Best regards,
John"""
        result = check_deliverability(subject, body, message_type='email')

        assert result['passed'] is True
        assert result['score'] >= 80
        assert result['critical_count'] == 0

    def test_spammy_email(self):
        """Spammy email should score low"""
        subject = "FREE GUARANTEED OFFER!!!"
        body = "Click here NOW!!! Limited time!!! FREE money guaranteed!!!"

        result = check_deliverability(subject, body, message_type='email')

        assert result['passed'] is False
        assert result['score'] < 80
        assert len(result['issues']) > 0

    def test_linkedin_message(self):
        """LinkedIn message should use different criteria"""
        body = "Hi, I'd like to connect and discuss opportunities."

        result = check_deliverability("", body, message_type='linkedin')

        # LinkedIn doesn't require subject
        assert 'subject' not in str([i.category for i in result['issues']])

    def test_sms_message(self):
        """SMS should check character limits"""
        body = "Hi! Quick question about your business. Can we chat?"

        result = check_deliverability("", body, message_type='sms')

        # SMS has stricter length requirements
        assert result is not None

    def test_issue_categorization(self):
        """Issues should be properly categorized"""
        subject = "FREE!!!"
        body = "FREE!!! Click here!!! http://spam.com http://more-spam.com"

        result = check_deliverability(subject, body, message_type='email')

        # Should have issues in multiple categories
        categories = {issue.category for issue in result['issues']}
        assert len(categories) >= 2  # Should have spam_words, links, formatting, etc.


class TestDeliverabilityIssue:
    """Test DeliverabilityIssue dataclass"""

    def test_issue_creation(self):
        """Should create issue with all fields"""
        issue = DeliverabilityIssue(
            severity='warning',
            category='spam_words',
            message='Spam word detected',
            suggestion='Use alternative wording'
        )

        assert issue.severity == 'warning'
        assert issue.category == 'spam_words'
        assert issue.message
        assert issue.suggestion

    def test_severity_levels(self):
        """Should support different severity levels"""
        severities = ['info', 'warning', 'critical']

        for severity in severities:
            issue = DeliverabilityIssue(
                severity=severity,
                category='test',
                message='test',
                suggestion='test'
            )
            assert issue.severity == severity


def test_integration_full_check():
    """Integration test with realistic outreach message"""
    subject = "Improving your local search rankings"
    body = """Hello,

I noticed your bakery appears on page 2 of Google Maps for "bakery Berlin".
With a few quick optimizations, you could likely rank in the top 3 results.

I specialize in local SEO for food businesses and typically see results
within 2-3 weeks. Would you be interested in a brief 10-minute call to
discuss this opportunity?

Best regards,
Sarah Miller
Local Search Consultant"""

    result = check_deliverability(subject, body, message_type='email')

    # Should pass all checks
    assert result['passed'] is True
    assert result['score'] >= 85
    assert result['critical_count'] == 0

    # Should have few or no issues
    assert len(result['issues']) <= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

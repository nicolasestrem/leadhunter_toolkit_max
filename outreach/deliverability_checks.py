"""
Email deliverability checks
Ensures outreach messages follow best practices for inbox delivery
"""

import re
from typing import List, Dict
from dataclasses import dataclass

# Spam trigger words (common spam indicators)
SPAM_WORDS = {
    'free', 'guarantee', 'guaranteed', 'no obligation', 'risk-free',
    'act now', 'limited time', 'urgent', 'hurry', 'click here',
    'buy now', 'order now', 'call now', 'apply now',
    'winner', 'congratulations', 'you have been selected',
    'cash bonus', 'extra income', 'work from home',
    'weight loss', 'lose weight', 'viagra', 'casino',
    '100% free', 'FREE', 'CLICK HERE'
}

# Safe alternative phrases
SPAM_ALTERNATIVES = {
    'free': 'complimentary',
    'guarantee': 'confident',
    'guaranteed': 'likely to see',
    'click here': 'view details',
    'urgent': 'timely',
    'hurry': 'soon',
    'act now': 'respond soon'
}


@dataclass
class DeliverabilityIssue:
    """Represents a deliverability issue"""
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'spam_words', 'length', 'links', 'formatting'
    message: str
    suggestion: str


def check_word_count(text: str, min_words: int = 80, max_words: int = 140) -> List[DeliverabilityIssue]:
    """
    Check if message word count is within acceptable range

    Args:
        text: Message text
        min_words: Minimum word count
        max_words: Maximum word count

    Returns:
        List of issues found
    """
    issues = []
    words = text.split()
    word_count = len(words)

    if word_count < min_words:
        issues.append(DeliverabilityIssue(
            severity='warning',
            category='length',
            message=f'Message too short ({word_count} words, minimum {min_words})',
            suggestion=f'Add more context and personalization. Current: {word_count}, target: {min_words}-{max_words} words'
        ))
    elif word_count > max_words:
        issues.append(DeliverabilityIssue(
            severity='warning',
            category='length',
            message=f'Message too long ({word_count} words, maximum {max_words})',
            suggestion=f'Shorten message for better engagement. Current: {word_count}, target: {min_words}-{max_words} words'
        ))

    return issues


def check_spam_words(text: str) -> List[DeliverabilityIssue]:
    """
    Check for spam trigger words

    Args:
        text: Message text

    Returns:
        List of issues found
    """
    issues = []
    text_lower = text.lower()

    found_spam_words = []
    for spam_word in SPAM_WORDS:
        if spam_word in text_lower:
            found_spam_words.append(spam_word)

    if found_spam_words:
        alternatives = []
        for word in found_spam_words[:3]:  # Show alternatives for first 3
            if word.lower() in SPAM_ALTERNATIVES:
                alternatives.append(f"'{word}' → '{SPAM_ALTERNATIVES[word.lower()]}'")

        issues.append(DeliverabilityIssue(
            severity='critical' if len(found_spam_words) > 2 else 'warning',
            category='spam_words',
            message=f'Spam trigger words found: {", ".join(found_spam_words)}',
            suggestion=f'Remove or replace spam words. Examples: {", ".join(alternatives)}' if alternatives else 'Remove spam words'
        ))

    return issues


def check_link_count(text: str, max_links: int = 1) -> List[DeliverabilityIssue]:
    """
    Check number of links in message

    Args:
        text: Message text
        max_links: Maximum allowed links

    Returns:
        List of issues found
    """
    issues = []

    # Count URLs (http/https, www., and bare domains)
    # Pattern matches: http://example.com, https://example.com, www.example.com
    url_pattern = re.compile(r'(?:https?://|www\.)\S+')
    urls = url_pattern.findall(text)
    link_count = len(urls)

    if link_count > max_links:
        issues.append(DeliverabilityIssue(
            severity='warning',
            category='links',
            message=f'Too many links ({link_count}, maximum {max_links})',
            suggestion=f'Reduce links to {max_links}. Multiple links can trigger spam filters.'
        ))

    return issues


def check_subject_line(subject: str, min_chars: int = 30, max_chars: int = 60) -> List[DeliverabilityIssue]:
    """
    Check subject line quality

    Args:
        subject: Email subject line
        min_chars: Minimum character count (default: 30)
        max_chars: Maximum character count (default: 60)

    Returns:
        List of issues found
    """
    issues = []

    if not subject:
        issues.append(DeliverabilityIssue(
            severity='critical',
            category='formatting',
            message='Missing subject line',
            suggestion=f'Add a compelling subject line ({min_chars}-{max_chars} characters)'
        ))
        return issues

    subject_len = len(subject)

    # Check length
    if subject_len < min_chars:
        issues.append(DeliverabilityIssue(
            severity='warning',
            category='formatting',
            message=f'Subject line too short ({subject_len} chars)',
            suggestion=f'Aim for {min_chars}-{max_chars} characters for optimal engagement'
        ))
    elif subject_len > max_chars:
        issues.append(DeliverabilityIssue(
            severity='warning',
            category='formatting',
            message=f'Subject line too long ({subject_len} chars, may be truncated)',
            suggestion=f'Keep subject under {max_chars} characters for mobile display'
        ))

    # Check for spam indicators
    if subject.isupper():
        issues.append(DeliverabilityIssue(
            severity='warning',
            category='spam_words',
            message='Subject line is all caps',
            suggestion='Use normal capitalization. ALL CAPS triggers spam filters.'
        ))

    if subject.count('!') > 1:
        issues.append(DeliverabilityIssue(
            severity='warning',
            category='spam_words',
            message='Too many exclamation marks in subject',
            suggestion='Use maximum 1 exclamation mark'
        ))

    return issues


def check_personalization(text: str) -> List[DeliverabilityIssue]:
    """
    Check for personalization elements

    Args:
        text: Message text

    Returns:
        List of issues found
    """
    issues = []

    # Check for generic greetings
    generic_greetings = ['dear sir/madam', 'to whom it may concern', 'hello there']
    text_lower = text.lower()

    has_generic = any(greeting in text_lower for greeting in generic_greetings)

    if has_generic:
        issues.append(DeliverabilityIssue(
            severity='warning',
            category='formatting',
            message='Generic greeting detected',
            suggestion='Use specific name or company name for better personalization'
        ))

    return issues


def check_exclamation_marks(text: str) -> List[DeliverabilityIssue]:
    """
    Check for excessive exclamation marks

    Args:
        text: Message text

    Returns:
        List of issues found
    """
    issues = []

    exclamation_count = text.count('!')

    if exclamation_count > 3:
        issues.append(DeliverabilityIssue(
            severity='warning',
            category='spam_words',
            message=f'Too many exclamation marks ({exclamation_count})',
            suggestion='Limit to 1-2 exclamation marks. Excessive use triggers spam filters.'
        ))

    return issues


def check_deliverability(
    subject: str,
    body: str,
    message_type: str = 'email'
) -> Dict[str, any]:
    """
    Run all deliverability checks on a message

    Args:
        subject: Subject line (for email)
        body: Message body
        message_type: Type of message (email, linkedin, sms)

    Returns:
        Dict with issues and overall score
    """
    all_issues = []

    # Email-specific checks
    if message_type == 'email':
        all_issues.extend(check_subject_line(subject))
        all_issues.extend(check_word_count(body, min_words=80, max_words=140))
        all_issues.extend(check_link_count(body, max_links=1))

    # LinkedIn checks
    elif message_type == 'linkedin':
        # LinkedIn has 300 char limit
        if len(body) > 300:
            all_issues.append(DeliverabilityIssue(
                severity='critical',
                category='length',
                message=f'Message too long for LinkedIn ({len(body)} chars, max 300)',
                suggestion='Shorten to 300 characters'
            ))
        all_issues.extend(check_link_count(body, max_links=0))

    # SMS/WhatsApp checks
    elif message_type in ['sms', 'whatsapp']:
        if len(body) > 160:
            all_issues.append(DeliverabilityIssue(
                severity='critical',
                category='length',
                message=f'Message too long for SMS ({len(body)} chars, max 160)',
                suggestion='Shorten to 160 characters'
            ))

    # Common checks for all types
    all_issues.extend(check_spam_words(body))
    all_issues.extend(check_personalization(body))
    all_issues.extend(check_exclamation_marks(body))

    # Calculate deliverability score (0-100)
    critical_count = len([i for i in all_issues if i.severity == 'critical'])
    warning_count = len([i for i in all_issues if i.severity == 'warning'])

    score = 100 - (critical_count * 20) - (warning_count * 5)
    score = max(0, min(100, score))  # Clamp to 0-100

    return {
        'score': score,
        'issues': all_issues,
        'critical_count': critical_count,
        'warning_count': warning_count,
        'passed': score >= 80
    }


def format_deliverability_report(check_result: Dict[str, any]) -> str:
    """
    Format deliverability check result as readable report

    Args:
        check_result: Result from check_deliverability()

    Returns:
        Formatted report string
    """
    score = check_result['score']
    issues = check_result['issues']

    report = f"**Deliverability Score: {score}/100**\n\n"

    if score >= 90:
        report += "✅ Excellent - Message should deliver well\n\n"
    elif score >= 80:
        report += "⚠️ Good - Minor improvements recommended\n\n"
    elif score >= 60:
        report += "⚠️ Fair - Several issues to fix\n\n"
    else:
        report += "❌ Poor - High risk of spam filtering\n\n"

    if issues:
        report += "**Issues Found:**\n\n"

        # Group by severity
        critical = [i for i in issues if i.severity == 'critical']
        warnings = [i for i in issues if i.severity == 'warning']

        if critical:
            report += "🔴 **Critical Issues:**\n"
            for issue in critical:
                report += f"- {issue.message}\n"
                report += f"  💡 {issue.suggestion}\n\n"

        if warnings:
            report += "🟡 **Warnings:**\n"
            for issue in warnings:
                report += f"- {issue.message}\n"
                report += f"  💡 {issue.suggestion}\n\n"
    else:
        report += "✅ No issues found!\n"

    return report

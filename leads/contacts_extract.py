"""
Contact extraction from markdown content
Extracts emails, phones, and social media links from markdown text
"""

import re
from typing import Dict, List, Set
from logger import get_logger

logger = get_logger(__name__)

# Regex patterns for extraction
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# Phone patterns - support international formats
PHONE_PATTERNS = [
    # +XX XXX XXXXXXX or +XX XXX XXX XXXX
    re.compile(r'\+\d{1,3}\s?\d{2,3}\s?\d{3,4}\s?\d{3,4}'),
    # (XXX) XXX-XXXX
    re.compile(r'\(\d{3}\)\s?\d{3}[-\s]?\d{4}'),
    # XXX-XXX-XXXX or XXX.XXX.XXXX
    re.compile(r'\d{3}[-.\s]\d{3}[-.\s]\d{4}'),
    # +XX-XXX-XXXXXXX
    re.compile(r'\+\d{1,3}[-\s]?\d{2,3}[-\s]?\d{3,4}[-\s]?\d{3,4}'),
]

# Social media patterns
SOCIAL_PATTERNS = {
    'facebook': [
        re.compile(r'https?://(?:www\.)?facebook\.com/[\w.-]+', re.I),
        re.compile(r'facebook\.com/([\w.-]+)', re.I),
        re.compile(r'fb\.com/([\w.-]+)', re.I),
    ],
    'instagram': [
        re.compile(r'https?://(?:www\.)?instagram\.com/[\w.-]+', re.I),
        re.compile(r'instagram\.com/([\w.-]+)', re.I),
        re.compile(r'@([\w.-]+)\s+(?:on\s+)?instagram', re.I),
    ],
    'linkedin': [
        re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[\w-]+', re.I),
        re.compile(r'linkedin\.com/(?:company|in)/([\w-]+)', re.I),
    ],
    'twitter': [
        re.compile(r'https?://(?:www\.)?(?:twitter|x)\.com/[\w]+', re.I),
        re.compile(r'(?:twitter|x)\.com/([\w]+)', re.I),
        re.compile(r'@([\w]+)\s+(?:on\s+)?(?:twitter|x)', re.I),
    ],
    'youtube': [
        re.compile(r'https?://(?:www\.)?youtube\.com/(?:c|channel|user)/[\w-]+', re.I),
        re.compile(r'youtube\.com/(?:c|channel|user)/([\w-]+)', re.I),
    ],
}


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text

    Args:
        text: Input text (markdown)

    Returns:
        List of unique email addresses
    """
    emails = EMAIL_PATTERN.findall(text)
    # Deduplicate and sort
    return sorted(list(set(emails)))


def extract_phones(text: str) -> List[str]:
    """
    Extract phone numbers from text

    Args:
        text: Input text (markdown)

    Returns:
        List of unique phone numbers
    """
    phones: Set[str] = set()

    for pattern in PHONE_PATTERNS:
        matches = pattern.findall(text)
        phones.update(matches)

    # Clean up phone numbers
    cleaned = []
    for phone in phones:
        # Basic cleaning - remove extra spaces
        phone_clean = phone.strip()
        if phone_clean:
            cleaned.append(phone_clean)

    return sorted(list(set(cleaned)))


def extract_social_links(text: str) -> Dict[str, str]:
    """
    Extract social media links from text

    Args:
        text: Input text (markdown)

    Returns:
        Dict mapping platform names to URLs
    """
    social = {}

    for platform, patterns in SOCIAL_PATTERNS.items():
        for pattern in patterns:
            matches = pattern.findall(text)
            if matches:
                # Take the first match
                match = matches[0]
                # If it's a full URL, use it; otherwise construct it
                if match.startswith('http'):
                    social[platform] = match
                else:
                    # Construct URL from username
                    if platform == 'facebook':
                        social[platform] = f"https://facebook.com/{match}"
                    elif platform == 'instagram':
                        social[platform] = f"https://instagram.com/{match}"
                    elif platform == 'linkedin':
                        social[platform] = f"https://linkedin.com/company/{match}"
                    elif platform == 'twitter':
                        social[platform] = f"https://twitter.com/{match}"
                    elif platform == 'youtube':
                        social[platform] = f"https://youtube.com/c/{match}"
                break  # Stop after first match for this platform

    return social


def extract_company_name(text: str) -> str:
    """
    Extract company name from markdown

    Looks for:
    1. First H1 heading
    2. Title-like patterns in first few lines

    Args:
        text: Input markdown text

    Returns:
        Company name or empty string
    """
    lines = text.split('\n')

    # Look for H1 heading
    for line in lines[:20]:  # Check first 20 lines
        if line.strip().startswith('# '):
            name = line.strip()[2:].strip()
            if name and not name.lower() in ['home', 'about', 'contact', 'welcome']:
                return name

    # Look for title-like patterns
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if len(line) > 5 and len(line) < 100:
            # Skip common non-title patterns
            if not any(skip in line.lower() for skip in ['http', 'welcome', 'copyright', '©']):
                # If line is mostly title case or uppercase, could be a name
                if line[0].isupper():
                    return line

    return ""


def extract_address(text: str) -> str:
    """
    Extract physical address from text

    Looks for address-like patterns near keywords like:
    - Address, Adresse, Anschrift
    - Location, Standort
    - Visit us, Find us

    Args:
        text: Input markdown text

    Returns:
        Address string or empty string
    """
    # Keywords that indicate address information
    address_keywords = [
        'address', 'adresse', 'anschrift', 'location', 'standort',
        'visit us', 'find us', 'besuchen sie uns'
    ]

    lines = text.split('\n')

    for i, line in enumerate(lines):
        line_lower = line.lower()

        # Check if line contains address keyword
        if any(keyword in line_lower for keyword in address_keywords):
            # Check next few lines for address pattern
            for j in range(i, min(i + 5, len(lines))):
                potential_address = lines[j].strip()

                # Remove markdown formatting
                potential_address = re.sub(r'[*_#`\[\]]', '', potential_address)
                potential_address = potential_address.strip()

                # Check if it looks like an address (has numbers and commas/street indicators)
                if (re.search(r'\d+', potential_address) and
                    len(potential_address) > 10 and
                    len(potential_address) < 200):
                    return potential_address

    return ""


def extract_contacts_from_markdown(markdown: str) -> Dict[str, any]:
    """
    Extract all contact information from markdown text

    Args:
        markdown: Input markdown text

    Returns:
        Dict with extracted contact information:
        {
            'emails': List[str],
            'phones': List[str],
            'social': Dict[str, str],
            'company_name': str,
            'address': str
        }
    """
    logger.debug("Extracting contacts from markdown")

    result = {
        'emails': extract_emails(markdown),
        'phones': extract_phones(markdown),
        'social': extract_social_links(markdown),
        'company_name': extract_company_name(markdown),
        'address': extract_address(markdown)
    }

    logger.info(
        f"Extracted: {len(result['emails'])} emails, "
        f"{len(result['phones'])} phones, "
        f"{len(result['social'])} social links"
    )

    return result


def merge_contact_info(existing: Dict[str, any], new: Dict[str, any]) -> Dict[str, any]:
    """
    Merge two contact info dicts, deduplicating and combining

    Args:
        existing: Existing contact info dict
        new: New contact info dict to merge

    Returns:
        Merged contact info dict
    """
    merged = existing.copy()

    # Merge emails (deduplicate)
    if 'emails' in new and new['emails']:
        existing_emails = set(merged.get('emails', []))
        existing_emails.update(new['emails'])
        merged['emails'] = sorted(list(existing_emails))

    # Merge phones (deduplicate)
    if 'phones' in new and new['phones']:
        existing_phones = set(merged.get('phones', []))
        existing_phones.update(new['phones'])
        merged['phones'] = sorted(list(existing_phones))

    # Merge social (prefer non-empty values)
    if 'social' in new and new['social']:
        if 'social' not in merged:
            merged['social'] = {}
        for platform, url in new['social'].items():
            if url:  # Only update if new value is non-empty
                merged['social'][platform] = url

    # Prefer non-empty company name
    if 'company_name' in new and new['company_name']:
        if not merged.get('company_name'):
            merged['company_name'] = new['company_name']

    # Prefer non-empty address
    if 'address' in new and new['address']:
        if not merged.get('address'):
            merged['address'] = new['address']

    return merged

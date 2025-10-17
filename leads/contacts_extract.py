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
        re.compile(r'instagram\s*[:\-]?\s*@([\w.-]+)', re.I),
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
    """Extract email addresses from a given text.

    This function uses a regular expression to find all occurrences of email addresses
    within a string. It then returns a deduplicated and sorted list of the findings.

    Args:
        text (str): The input text, which may be in markdown format.

    Returns:
        List[str]: A sorted list of unique email addresses found in the text.
    """
    emails = EMAIL_PATTERN.findall(text)
    # Deduplicate and sort
    return sorted(list(set(emails)))


def extract_phones(text: str) -> List[str]:
    """Extract phone numbers from a given text.

    This function applies a series of regular expression patterns to identify various
    phone number formats, including international ones. The extracted numbers are
    cleaned, deduplicated, and returned in a sorted list.

    Args:
        text (str): The input text, which may be in markdown format.

    Returns:
        List[str]: A sorted list of unique phone numbers.
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
    """Extract social media links from a given text.

    This function identifies links to various social media platforms (Facebook, Instagram,
    LinkedIn, Twitter, YouTube) and returns them in a dictionary. It's designed to
    capture the first link found for each platform.

    Args:
        text (str): The input text, which may be in markdown format.

    Returns:
        Dict[str, str]: A dictionary mapping platform names to their corresponding URLs.
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
    """Extract a company name from markdown text.

    This function employs a heuristic approach by first searching for a Level 1 markdown
    heading (H1). If not found, it looks for title-like patterns in the initial lines
    of the text.

    Args:
        text (str): The input markdown text.

    Returns:
        str: The extracted company name, or an empty string if not found.
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
    """Extract a physical address from a given text.

    This function searches for address-like patterns in proximity to specific keywords
    (e.g., 'Address', 'Location'). It is designed to identify and return the first
    plausible address it finds.

    Args:
        text (str): The input markdown text.

    Returns:
        str: The extracted address, or an empty string if none is found.
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
    """Extract all contact information from a markdown text.

    This function acts as a facade, orchestrating calls to the individual extraction
    functions (for emails, phones, social links, etc.) and consolidating the results
    into a single dictionary.

    Args:
        markdown (str): The input markdown text.

    Returns:
        Dict[str, any]: A dictionary containing all the extracted contact information.
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
    """Merge two contact information dictionaries.

    This function intelligently combines two contact dictionaries, deduplicating list-based
    fields (like emails and phones) and prioritizing non-empty values for single-value
    fields (like company name and address).

    Args:
        existing (Dict[str, any]): The existing contact information dictionary.
        new (Dict[str, any]): The new contact information to merge.

    Returns:
        Dict[str, any]: The merged contact information dictionary.
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

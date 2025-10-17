"""Structured data parsing utilities for contact extraction.

This module provides utilities for extracting contact information from
structured data formats commonly found in web pages, including JSON-LD
and microdata. It focuses on Schema.org structured data that contains
business and organization information.

Classes:
    StructuredExtraction: Container for extracted structured data
    
Functions:
    parse_structured_contacts: Main function to extract structured contact data
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

from selectolax.parser import HTMLParser, Node

from logger import get_logger
from utils_html import collect_social

logger = get_logger(__name__)

_SCHEMA_CONTACT_TYPES = {
    "organization",
    "localbusiness",
    "corporation",
    "ngo",
    "nonprofit",
    "governmentorganization",
    "educationalorganization",
    "medicalorganization",
    "foodestablishment",
    "restaurant",
    "cafe",
    "store",
    "shop",
    "hotel",
    "lodgingbusiness",
    "travelagency",
    "professionalservice",
    "accountingservice",
    "attorney",
    "legalservice",
    "dentist",
    "medicalclinic",
    "hospital",
    "realestateagent",
    "homeandconstructionbusiness",
    "roofingcontractor",
    "plumber",
    "electrician",
    "hvacbusiness",
    "automotivebusiness",
    "barorpub",
    "beautysalon",
    "daycare",
    "childcare",
}


@dataclass
class StructuredExtraction:
    """Container for contact information extracted from structured data.
    
    This class holds all the contact information that can be extracted
    from structured data sources like JSON-LD and microdata.
    
    Attributes:
        names: Set of organization/business names
        emails: Set of email addresses
        phones: Set of phone numbers
        social: Dictionary mapping social platform names to URLs
        addresses: List of physical addresses
        cities: Set of city names
        countries: Set of country names
    """
    names: Set[str] = field(default_factory=set)
    emails: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    social: Dict[str, str] = field(default_factory=dict)
    addresses: List[str] = field(default_factory=list)
    cities: Set[str] = field(default_factory=set)
    countries: Set[str] = field(default_factory=set)


def parse_structured_contacts(tree: HTMLParser, *, base_url: str) -> StructuredExtraction:
    """Parse structured contact data from an HTML document.
    
    This function extracts contact information from both JSON-LD and microdata
    structured data formats found in the HTML. It focuses on Schema.org
    vocabulary for business and organization data.
    
    Args:
        tree: Parsed HTML tree using selectolax
        base_url: Base URL for resolving relative URLs
        
    Returns:
        StructuredExtraction object containing all found contact information
    """
    items = list(_iter_schema_items(tree))
    extraction = StructuredExtraction()
    social_urls: Set[str] = set()

    for item in items:
        _harvest_schema_item(item, extraction, social_urls)

    if social_urls:
        social = collect_social(list(social_urls))
        extraction.social.update(social)

    return extraction


def _harvest_schema_item(item: Dict, extraction: StructuredExtraction, social_urls: Set[str]) -> None:
    """Extract contact information from a single structured data item.
    
    Args:
        item: Dictionary representing a structured data item
        extraction: StructuredExtraction object to populate
        social_urls: Set to collect social media URLs for processing
    """
    names = _ensure_list(item.get("name")) + _ensure_list(item.get("legalName"))
    for name in names:
        text = _clean_text(name)
        if text:
            extraction.names.add(text)

    for email in _ensure_list(item.get("email")):
        text = _clean_text(email)
        if text:
            extraction.emails.add(text)

    for telephone in _ensure_list(item.get("telephone")) + _ensure_list(item.get("phone")):
        text = _clean_text(telephone)
        if text:
            extraction.phones.add(text)

    for contact_point in _ensure_list(item.get("contactPoint")):
        if isinstance(contact_point, dict):
            for email in _ensure_list(contact_point.get("email")):
                text = _clean_text(email)
                if text:
                    extraction.emails.add(text)
            for phone in _ensure_list(contact_point.get("telephone")):
                text = _clean_text(phone)
                if text:
                    extraction.phones.add(text)
            social_urls.update(
                _ensure_list(contact_point.get("sameAs")) + _ensure_list(contact_point.get("url"))
            )
        else:
            text = _clean_text(contact_point)
            if text and "@" in text:
                extraction.emails.add(text)

    address_data = item.get("address")
    for address in _ensure_list(address_data):
        address_text, city, country = _normalize_address(address)
        if address_text and address_text not in extraction.addresses:
            extraction.addresses.append(address_text)
        if city:
            extraction.cities.add(city)
        if country:
            extraction.countries.add(country)

    for city in _ensure_list(item.get("addressLocality")) + _ensure_list(item.get("city")):
        text = _clean_text(city)
        if text:
            extraction.cities.add(text)

    for country in _ensure_list(item.get("addressCountry")):
        text = _clean_text(country)
        if text:
            extraction.countries.add(text)

    social_urls.update(_ensure_list(item.get("sameAs")))


def _iter_schema_items(tree: HTMLParser) -> Iterable[Dict]:
    """Iterate over all structured data items in the HTML document.
    
    Args:
        tree: Parsed HTML tree
        
    Yields:
        Dictionary representations of structured data items
    """
    yield from _extract_json_ld(tree)
    yield from _extract_microdata(tree)


def _extract_json_ld(tree: HTMLParser) -> Iterable[Dict]:
    """Extract JSON-LD structured data from script tags.
    
    Args:
        tree: Parsed HTML tree
        
    Yields:
        Dictionary representations of JSON-LD items
    """
    for node in tree.css('script[type="application/ld+json"]'):
        raw = node.text(strip=True)
        if not raw:
            continue
        data = _safe_json_loads(raw)
        if data is None:
            continue
        for item in _flatten_ld_payload(data):
            if _is_relevant_schema(item):
                yield item


def _safe_json_loads(raw: str) -> Optional[Dict]:
    """Safely parse JSON with fallback handling for malformed JSON.
    
    Args:
        raw: Raw JSON string
        
    Returns:
        Parsed JSON dictionary or None if parsing fails
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        stripped = raw.strip().rstrip(';')
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            logger.debug("Failed to parse JSON-LD block", exc_info=True)
            return None


def _flatten_ld_payload(payload) -> List[Dict]:
    """Flatten JSON-LD payload structure to extract individual items.
    
    Args:
        payload: JSON-LD payload (can be dict, list, or nested structure)
        
    Returns:
        List of individual structured data items
    """
    items: List[Dict] = []
    if isinstance(payload, list):
        for element in payload:
            items.extend(_flatten_ld_payload(element))
    elif isinstance(payload, dict):
        graph = payload.get("@graph")
        if graph:
            items.extend(_flatten_ld_payload(graph))
        else:
            items.append(payload)
    return items


def _extract_microdata(tree: HTMLParser) -> Iterable[Dict]:
    """Extract microdata from HTML elements with itemscope attribute.
    
    Args:
        tree: Parsed HTML tree
        
    Yields:
        Dictionary representations of microdata items
    """
    for node in tree.css('[itemscope]'):
        item = _parse_microdata_scope(node)
        if item and _is_relevant_schema(item):
            yield item


def _parse_microdata_scope(node: Node) -> Dict:
    """Parse a microdata itemscope into a dictionary.
    
    Args:
        node: HTML node with itemscope attribute
        
    Returns:
        Dictionary representation of the microdata item
    """
    item: Dict[str, object] = {}
    types = _split_types(node.attributes.get("itemtype"))
    if types:
        item["@type"] = types

    properties: Dict[str, List[object]] = {}

    def add_property(name: str, value: object) -> None:
        """Add a property value to the properties dictionary."""
        if not name:
            return
        properties.setdefault(name, []).append(value)

    def walk(current: Node) -> None:
        """Recursively walk the DOM tree to extract microdata properties."""
        for child in _iter_children(current):
            if child.tag == "-comment":
                continue
            child_itemprop = child.attributes.get("itemprop")
            if child.attributes.get("itemscope"):
                if child_itemprop:
                    add_property(child_itemprop, _parse_microdata_scope(child))
                continue
            if child_itemprop:
                add_property(child_itemprop, _microdata_value(child))
            walk(child)

    walk(node)

    for name, values in properties.items():
        collapsed = _collapse_values(values)
        if collapsed is not None:
            item[name] = collapsed

    return item


def _microdata_value(node: Node) -> Optional[str]:
    """Extract the value from a microdata property node.
    
    Args:
        node: HTML node with itemprop attribute
        
    Returns:
        Extracted value string or None
    """
    for attr in ("content", "href", "src", "data"):
        if attr in node.attributes:
            value = node.attributes.get(attr)
            if value:
                cleaned = value.strip()
                if attr == "href" and cleaned.lower().startswith("mailto:"):
                    cleaned = cleaned.split("mailto:", 1)[1]
                    cleaned = cleaned.split("?", 1)[0]
                return cleaned
    text = node.text(separator=" ", strip=True)
    return text or None


def _iter_children(node: Node):
    """Iterate over child nodes of an HTML node.
    
    Args:
        node: Parent HTML node
        
    Yields:
        Child nodes
    """
    child = node.child
    while child is not None:
        yield child
        child = child.next


def _collapse_values(values: List[object]):
    """Collapse a list of values into a single value or list.
    
    Args:
        values: List of values to collapse
        
    Returns:
        Single value if only one non-empty value, list if multiple, None if empty
    """
    filtered = [value for value in values if value not in (None, "")]
    if not filtered:
        return None
    if len(filtered) == 1:
        return filtered[0]
    return filtered


def _ensure_list(value) -> List:
    """Ensure a value is a list.
    
    Args:
        value: Value to convert to list
        
    Returns:
        List containing the value(s)
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _split_types(raw: Optional[str]) -> List[str]:
    """Split microdata itemtype string into individual types.
    
    Args:
        raw: Raw itemtype string
        
    Returns:
        List of individual type strings
    """
    if not raw:
        return []
    return [part.strip() for part in raw.split() if part.strip()]


def _clean_text(value) -> Optional[str]:
    """Clean and normalize text values from structured data.
    
    Args:
        value: Value to clean (can be string, dict, or other type)
        
    Returns:
        Cleaned text string or None
    """
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("name", "@id", "url"):
            if key in value and value[key]:
                return str(value[key]).strip()
        return None
    return str(value).strip()


def _normalize_address(address) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Normalize address data from structured data.
    
    Args:
        address: Address data (can be dict or string)
        
    Returns:
        Tuple of (address_text, city, country)
    """
    if isinstance(address, dict):
        parts = []
        for key in (
            "streetAddress",
            "postOfficeBoxNumber",
            "addressLocality",
            "addressRegion",
            "postalCode",
            "addressCountry",
        ):
            value = address.get(key)
            cleaned = _clean_text(value)
            if cleaned:
                parts.append(cleaned)
        address_text = ", ".join(dict.fromkeys(parts)) if parts else None
        city = _clean_text(address.get("addressLocality"))
        country = _clean_text(address.get("addressCountry"))
        return address_text, city, country
    cleaned = _clean_text(address)
    return cleaned, None, None


def _is_relevant_schema(item: Dict) -> bool:
    """Check if a structured data item is relevant for contact extraction.
    
    Args:
        item: Structured data item dictionary
        
    Returns:
        True if the item contains relevant business/organization data
    """
    types = item.get("@type")
    if not types:
        return False
    normalized = types if isinstance(types, list) else [types]
    for type_value in normalized:
        type_name = str(type_value or "").lower()
        if not type_name:
            continue
        if "schema.org" in type_name:
            type_name = type_name.rsplit("/", 1)[-1]
        type_name = type_name.strip()
        if not type_name:
            continue
        if (
            type_name in _SCHEMA_CONTACT_TYPES
            or "organization" in type_name
            or "business" in type_name
        ):
            return True
    return False
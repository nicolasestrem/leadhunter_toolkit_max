"""Structured data parsing utilities for contact extraction."""

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
    names: Set[str] = field(default_factory=set)
    emails: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    social: Dict[str, str] = field(default_factory=dict)
    addresses: List[str] = field(default_factory=list)
    cities: Set[str] = field(default_factory=set)
    countries: Set[str] = field(default_factory=set)


def parse_structured_contacts(tree: HTMLParser, *, base_url: str) -> StructuredExtraction:
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
    yield from _extract_json_ld(tree)
    yield from _extract_microdata(tree)


def _extract_json_ld(tree: HTMLParser) -> Iterable[Dict]:
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
    for node in tree.css('[itemscope]'):
        item = _parse_microdata_scope(node)
        if item and _is_relevant_schema(item):
            yield item


def _parse_microdata_scope(node: Node) -> Dict:
    item: Dict[str, object] = {}
    types = _split_types(node.attributes.get("itemtype"))
    if types:
        item["@type"] = types

    properties: Dict[str, List[object]] = {}

    def add_property(name: str, value: object) -> None:
        if not name:
            return
        properties.setdefault(name, []).append(value)

    def walk(current: Node) -> None:
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
    child = node.child
    while child is not None:
        yield child
        child = child.next


def _collapse_values(values: List[object]):
    filtered = [value for value in values if value not in (None, "")]
    if not filtered:
        return None
    if len(filtered) == 1:
        return filtered[0]
    return filtered


def _ensure_list(value) -> List:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _split_types(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split() if part.strip()]


def _clean_text(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("name", "@id", "url"):
            if key in value and value[key]:
                return str(value[key]).strip()
        return None
    return str(value).strip()


def _normalize_address(address) -> Tuple[Optional[str], Optional[str], Optional[str]]:
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

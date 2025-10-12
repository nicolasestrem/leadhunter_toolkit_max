"""
Page auditor - extends existing seo_audit.py with LLM-powered insights
"""

import json
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from llm.adapter import LLMAdapter
from logger import get_logger

logger = get_logger(__name__)

BASE_DIR = Path(__file__).parent.parent
PROMPT_LIBRARY_DIR = BASE_DIR / "llm" / "prompt_library"


@dataclass
class AuditIssue:
    """Represents an audit issue"""
    category: str  # meta, headings, content, images, links, technical
    severity: str  # critical, high, medium, low
    title: str
    description: str
    recommendation: str


@dataclass
class QuickWinTask:
    """Represents a quick win task"""
    title: str
    action: str
    impact: str
    effort: str  # 5 mins, 15 mins, 1 hour


@dataclass
class PageAudit:
    """Complete page audit result"""
    url: str
    score: int  # 0-100
    grade: str  # A, B, C, D, F
    issues: List[AuditIssue]
    strengths: List[str]
    quick_wins: List[QuickWinTask]
    content_score: int
    technical_score: int
    seo_score: int
    generated_at: datetime = field(default_factory=datetime.now)


def load_audit_prompt_config() -> Dict:
    """Load audit prompt configuration from YAML"""
    prompt_path = PROMPT_LIBRARY_DIR / "audit.yml"

    with open(prompt_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def extract_page_metrics(html_content: str, url: str) -> Dict:
    """
    Extract basic metrics from HTML content

    Args:
        html_content: HTML content
        url: Page URL

    Returns:
        Dict with metrics
    """
    from selectolax.parser import HTMLParser

    metrics = {
        'url': url,
        'has_https': url.startswith('https://'),
        'word_count': 0,
        'has_h1': False,
        'page_title': '',
        'image_count': 0,
        'link_count': 0
    }

    try:
        parser = HTMLParser(html_content)

        # Title
        title_tag = parser.css_first('title')
        if title_tag:
            metrics['page_title'] = title_tag.text().strip()

        # H1
        h1 = parser.css_first('h1')
        if h1:
            metrics['has_h1'] = True

        # Word count (approximate from body text)
        body = parser.css_first('body')
        if body:
            text = body.text()
            metrics['word_count'] = len(text.split())

        # Images
        images = parser.css('img')
        metrics['image_count'] = len(images)

        # Links
        links = parser.css('a')
        metrics['link_count'] = len(links)

    except Exception as e:
        logger.error(f"Error extracting page metrics: {e}")

    return metrics


def format_audit_prompt(url: str, html_content: str) -> tuple[str, str]:
    """
    Format audit prompts (system + user)

    Args:
        url: Page URL
        html_content: HTML content

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    config = load_audit_prompt_config()

    # Extract metrics
    metrics = extract_page_metrics(html_content, url)

    # System prompt
    system_prompt = config.get('system_prompt', '')

    # User prompt template
    user_template = config.get('user_prompt_template', '')

    # Truncate HTML if too long
    max_html_chars = 10000
    html_sample = html_content[:max_html_chars]
    if len(html_content) > max_html_chars:
        html_sample += "\n... [truncated]"

    # Format user prompt
    user_prompt = user_template.format(
        url=url,
        page_title=metrics.get('page_title', 'Unknown'),
        domain=url.split('/')[2] if '/' in url else url,
        html_content=html_sample,
        word_count=metrics.get('word_count', 0),
        has_https=metrics.get('has_https', False),
        has_h1=metrics.get('has_h1', False),
        image_count=metrics.get('image_count', 0),
        link_count=metrics.get('link_count', 0)
    )

    return system_prompt, user_prompt


def parse_audit_response(response: str, url: str) -> PageAudit:
    """
    Parse LLM response into PageAudit object

    Args:
        response: LLM JSON response
        url: Page URL

    Returns:
        PageAudit object
    """
    try:
        # Clean response
        response_clean = response.strip()
        if response_clean.startswith('```json'):
            response_clean = response_clean[7:]
        elif response_clean.startswith('```'):
            response_clean = response_clean[3:]
        if response_clean.endswith('```'):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()

        # Parse JSON
        data = json.loads(response_clean)

        # Parse issues
        issues = []
        for issue_data in data.get('issues', []):
            issues.append(AuditIssue(
                category=issue_data.get('category', 'other'),
                severity=issue_data.get('severity', 'medium'),
                title=issue_data.get('title', ''),
                description=issue_data.get('description', ''),
                recommendation=issue_data.get('recommendation', '')
            ))

        # Parse quick wins
        quick_wins = []
        for qw_data in data.get('quick_wins', []):
            quick_wins.append(QuickWinTask(
                title=qw_data.get('title', ''),
                action=qw_data.get('action', ''),
                impact=qw_data.get('impact', ''),
                effort=qw_data.get('effort', '15 mins')
            ))

        # Create audit
        audit = PageAudit(
            url=url,
            score=data.get('score', 50),
            grade=data.get('grade', 'C'),
            issues=issues,
            strengths=data.get('strengths', []),
            quick_wins=quick_wins,
            content_score=data.get('content_score', 50),
            technical_score=data.get('technical_score', 50),
            seo_score=data.get('seo_score', 50)
        )

        return audit

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse audit response: {e}")
        logger.error(f"Response was: {response[:500]}")

        # Return minimal audit
        return PageAudit(
            url=url,
            score=0,
            grade='F',
            issues=[AuditIssue(
                category='technical',
                severity='critical',
                title='Audit Failed',
                description='Failed to parse LLM response',
                recommendation='Try again or check LLM configuration'
            )],
            strengths=[],
            quick_wins=[],
            content_score=0,
            technical_score=0,
            seo_score=0
        )


def audit_page(
    url: str,
    html_content: str,
    llm_adapter: Optional[LLMAdapter] = None,
    use_llm: bool = True
) -> PageAudit:
    """
    Audit a web page

    Args:
        url: Page URL
        html_content: HTML content
        llm_adapter: Optional LLM adapter for enhanced analysis
        use_llm: Whether to use LLM (if False, basic metrics only)

    Returns:
        PageAudit object
    """
    logger.info(f"Auditing page: {url}")

    if not use_llm or not llm_adapter:
        # Return basic audit without LLM
        metrics = extract_page_metrics(html_content, url)

        # Calculate basic score
        score = 50
        if metrics['has_https']:
            score += 10
        if metrics['has_h1']:
            score += 10
        if metrics['word_count'] >= 300:
            score += 10
        if metrics['page_title'] and len(metrics['page_title']) <= 60:
            score += 10

        return PageAudit(
            url=url,
            score=score,
            grade='C',
            issues=[],
            strengths=['Basic metrics collected'],
            quick_wins=[],
            content_score=score,
            technical_score=score,
            seo_score=score
        )

    # Get prompts
    system_prompt, user_prompt = format_audit_prompt(url, html_content)

    # Call LLM
    logger.debug(f"Calling LLM for page audit")
    response = llm_adapter.chat_with_system(
        user_message=user_prompt,
        system_message=system_prompt,
        temperature=0.1  # Low temp for consistent analysis
    )

    # Parse response
    audit = parse_audit_response(response, url)
    logger.info(f"Audit complete: score={audit.score}, grade={audit.grade}, issues={len(audit.issues)}")

    return audit

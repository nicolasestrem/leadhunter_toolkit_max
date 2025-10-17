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
    """Represents a single issue identified during a page audit.

    Attributes:
        category (str): The category of the issue (e.g., 'meta', 'content').
        severity (str): The severity of the issue ('critical', 'high', 'medium', 'low').
        title (str): A concise title for the issue.
        description (str): A detailed description of the issue.
        recommendation (str): A suggested action to resolve the issue.
    """
    category: str
    severity: str
    title: str
    description: str
    recommendation: str


@dataclass
class QuickWinTask:
    """Represents an actionable quick win task derived from an audit.

    Attributes:
        title (str): The title of the quick win task.
        action (str): The specific action to be performed.
        impact (str): The expected positive impact of the action.
        effort (str): The estimated effort required (e.g., '5 mins', '1 hour').
    """
    title: str
    action: str
    impact: str
    effort: str


@dataclass
class PageAudit:
    """Represents the complete result of a page audit.

    This data class is the main container for all the findings of a page audit, including
    scores, issues, strengths, and quick wins.

    Attributes:
        url (str): The URL of the audited page.
        score (int): The overall audit score (0-100).
        grade (str): The letter grade corresponding to the score (A, B, C, D, F).
        issues (List[AuditIssue]): A list of identified issues.
        strengths (List[str]): A list of the page's strengths.
        quick_wins (List[QuickWinTask]): A list of actionable quick win tasks.
        content_score (int): The score for the content category.
        technical_score (int): The score for the technical category.
        seo_score (int): The score for the SEO category.
        generated_at (datetime): The timestamp of when the audit was generated.
    """
    url: str
    score: int
    grade: str
    issues: List[AuditIssue]
    strengths: List[str]
    quick_wins: List[QuickWinTask]
    content_score: int
    technical_score: int
    seo_score: int
    generated_at: datetime = field(default_factory=datetime.now)


def load_audit_prompt_config() -> Dict:
    """Load the audit prompt configuration from its YAML file.

    This function is responsible for reading and parsing the 'audit.yml' file, which
    contains the templates and settings for performing a page audit.

    Returns:
        Dict: A dictionary containing the audit prompt configuration.
    """
    prompt_path = PROMPT_LIBRARY_DIR / "audit.yml"

    with open(prompt_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def extract_page_metrics(html_content: str, url: str) -> Dict:
    """Extract basic SEO and content metrics from the HTML of a page.

    This function parses the HTML to gather important metrics like word count, title tag,
    image count, and the presence of an H1 tag.

    Args:
        html_content (str): The HTML content of the page.
        url (str): The URL of the page.

    Returns:
        Dict: A dictionary containing the extracted metrics.
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
    """Format the audit prompts, including both system and user prompts.

    This function assembles the prompts for the LLM by combining the extracted page
    metrics and HTML content with the templates from the audit prompt configuration.

    Args:
        url (str): The URL of the page.
        html_content (str): The HTML content of the page.

    Returns:
        tuple[str, str]: A tuple containing the system and user prompts.
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
    """Parse the LLM's response into a PageAudit object.

    This function is designed to robustly handle the JSON output from the LLM, including
    cleaning the response and parsing it into the structured PageAudit data class.

    Args:
        response (str): The JSON response from the LLM.
        url (str): The URL of the audited page.

    Returns:
        PageAudit: A complete PageAudit object.
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
        # Log response with Unicode escape to avoid encoding errors
        try:
            logger.error(f"Response was: {response[:500]}")
        except Exception:
            logger.error(f"Response was: {response[:500].encode('unicode-escape').decode('ascii')}")

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
    """Audit a web page, with an option for LLM-enhanced analysis.

    This is the main function for auditing a page. It can perform a basic audit using
    extracted metrics or a more comprehensive one by leveraging an LLM for deeper insights.

    Args:
        url (str): The URL of the page to audit.
        html_content (str): The HTML content of the page.
        llm_adapter (Optional[LLMAdapter]): An optional LLM adapter for enhanced analysis.
        use_llm (bool): If True, use the LLM; otherwise, perform a basic audit.

    Returns:
        PageAudit: The result of the page audit.
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

    # Call LLM with increased max_tokens for full audit response
    logger.debug(f"Calling LLM for page audit")
    response = llm_adapter.chat_with_system(
        user_message=user_prompt,
        system_message=system_prompt,
        temperature=0.1,  # Low temp for consistent analysis
        max_tokens=4096  # High token limit to avoid truncating audit JSON
    )

    # Parse response
    audit = parse_audit_response(response, url)
    logger.info(f"Audit complete: score={audit.score}, grade={audit.grade}, issues={len(audit.issues)}")

    return audit

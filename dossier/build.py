"""
Dossier builder
Creates comprehensive RAG-based dossiers from crawled pages
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
class QuickWin:
    """Represents a 48-hour quick win"""
    title: str
    action: str
    impact: str
    effort: str  # low, medium
    priority: int  # 1-5


@dataclass
class Issue:
    """Represents a detected issue"""
    category: str  # technical, content, seo, ux
    severity: str  # critical, high, medium, low
    description: str
    source: str  # URL where issue was found


@dataclass
class DigitalPresence:
    """Digital presence analysis"""
    website_quality: str
    social_activity: str
    online_reputation: str


@dataclass
class Signals:
    """Business signals"""
    positive: List[str] = field(default_factory=list)
    growth: List[str] = field(default_factory=list)
    pain: List[str] = field(default_factory=list)


@dataclass
class Dossier:
    """Complete lead dossier"""
    company_name: str
    website: str
    generated_at: datetime

    # Core sections
    company_overview: str
    services_products: List[str]
    digital_presence: DigitalPresence
    signals: Signals
    issues: List[Issue]
    quick_wins: List[QuickWin]

    # Metadata
    pages_analyzed: int
    sources: List[str] = field(default_factory=list)


def load_dossier_prompt_config() -> Dict:
    """Load dossier prompt configuration from YAML"""
    prompt_path = PROMPT_LIBRARY_DIR / "dossier.yml"

    with open(prompt_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def prepare_pages_content(
    pages: List[Dict[str, str]],
    max_per_page: int = 5000,
    max_total: int = 15000,
    priority_keywords: List[str] = None
) -> tuple[str, int]:
    """
    Prepare and aggregate page content for LLM

    Args:
        pages: List of dicts with 'url' and 'content' keys
        max_per_page: Max characters per page
        max_total: Max total characters
        priority_keywords: Keywords to prioritize pages (home, about, contact, etc.)

    Returns:
        Tuple of (formatted_content, page_count)
    """
    if priority_keywords is None:
        priority_keywords = ['home', 'index', 'about', 'contact', 'services', 'products']

    # Sort pages by priority
    def page_priority(page):
        url_lower = page.get('url', '').lower()
        for i, keyword in enumerate(priority_keywords):
            if keyword in url_lower:
                return i
        return len(priority_keywords)

    sorted_pages = sorted(pages, key=page_priority)

    # Build aggregated content
    formatted = ""
    total_chars = 0
    included_count = 0

    for page in sorted_pages:
        url = page.get('url', 'unknown')
        content = page.get('content', '')

        # Truncate if needed
        if len(content) > max_per_page:
            content = content[:max_per_page] + "... [truncated]"

        # Check if adding this would exceed total limit
        page_block = f"\n---\n**Page**: {url}\n**Content**:\n{content}\n"

        if total_chars + len(page_block) > max_total:
            logger.warning(f"Reached max content limit, skipping remaining pages")
            break

        formatted += page_block
        total_chars += len(page_block)
        included_count += 1

    return formatted, included_count


def format_dossier_prompt(
    lead_data: Dict,
    pages: List[Dict[str, str]]
) -> tuple[str, str]:
    """
    Format dossier prompts (system + user)

    Args:
        lead_data: Lead data dict
        pages: List of page dicts with url and content

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    config = load_dossier_prompt_config()

    # Prepare pages content
    pages_content, page_count = prepare_pages_content(
        pages,
        max_per_page=config.get('max_content_per_page', 5000),
        max_total=config.get('max_total_content', 15000),
        priority_keywords=config.get('priority_pages', [])
    )

    # System prompt
    system_prompt = config.get('system_prompt', '')

    # User prompt template
    user_template = config.get('user_prompt_template', '')

    # Format social links
    social = lead_data.get('social', {})
    if isinstance(social, dict):
        social_links = ', '.join([f"{k}: {v}" for k, v in social.items() if v])
    else:
        social_links = 'None'

    # Format user prompt
    user_prompt = user_template.format(
        company_name=lead_data.get('name', 'Unknown'),
        website=lead_data.get('website', ''),
        business_type=lead_data.get('business_type', 'business'),
        city=lead_data.get('city', ''),
        country=lead_data.get('country', ''),
        emails=', '.join(lead_data.get('emails', [])) or 'None',
        phones=', '.join(lead_data.get('phones', [])) or 'None',
        social_links=social_links,
        score_quality=lead_data.get('score_quality', 0),
        score_fit=lead_data.get('score_fit', 0),
        issue_flags=', '.join(lead_data.get('issue_flags', [])) or 'None',
        quality_signals=', '.join(lead_data.get('quality_signals', [])) or 'None',
        page_count=page_count,
        pages_content=pages_content
    )

    return system_prompt, user_prompt


def parse_dossier_response(response: str, lead_data: Dict, pages: List[Dict]) -> Dossier:
    """
    Parse LLM response into Dossier object

    Args:
        response: LLM JSON response
        lead_data: Lead data dict
        pages: Pages analyzed

    Returns:
        Dossier object
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

        # Parse digital presence
        dp_data = data.get('digital_presence', {})
        digital_presence = DigitalPresence(
            website_quality=dp_data.get('website_quality', 'Not assessed'),
            social_activity=dp_data.get('social_activity', 'Not assessed'),
            online_reputation=dp_data.get('online_reputation', 'Not assessed')
        )

        # Parse signals
        signals_data = data.get('signals', {})
        signals = Signals(
            positive=signals_data.get('positive', []),
            growth=signals_data.get('growth', []),
            pain=signals_data.get('pain', [])
        )

        # Parse issues
        issues = []
        for issue_data in data.get('issues', []):
            issues.append(Issue(
                category=issue_data.get('category', 'other'),
                severity=issue_data.get('severity', 'medium'),
                description=issue_data.get('description', ''),
                source=issue_data.get('source', '')
            ))

        # Parse quick wins
        quick_wins = []
        for qw_data in data.get('quick_wins', []):
            quick_wins.append(QuickWin(
                title=qw_data.get('title', ''),
                action=qw_data.get('action', ''),
                impact=qw_data.get('impact', ''),
                effort=qw_data.get('effort', 'medium'),
                priority=qw_data.get('priority', 5)
            ))

        # Sort quick wins by priority
        quick_wins.sort(key=lambda x: x.priority)

        # Create dossier
        dossier = Dossier(
            company_name=lead_data.get('name', 'Unknown'),
            website=lead_data.get('website', ''),
            generated_at=datetime.now(),
            company_overview=data.get('company_overview', ''),
            services_products=data.get('services_products', []),
            digital_presence=digital_presence,
            signals=signals,
            issues=issues,
            quick_wins=quick_wins,
            pages_analyzed=len(pages),
            sources=[p.get('url', '') for p in pages]
        )

        return dossier

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse dossier response: {e}")
        logger.error(f"Response was: {response[:500]}")

        # Return minimal dossier
        return Dossier(
            company_name=lead_data.get('name', 'Unknown'),
            website=lead_data.get('website', ''),
            generated_at=datetime.now(),
            company_overview="Failed to generate dossier - LLM response parsing error",
            services_products=[],
            digital_presence=DigitalPresence(
                website_quality="Not assessed",
                social_activity="Not assessed",
                online_reputation="Not assessed"
            ),
            signals=Signals(),
            issues=[],
            quick_wins=[],
            pages_analyzed=len(pages),
            sources=[p.get('url', '') for p in pages]
        )


def build_dossier(
    lead_data: Dict,
    pages: List[Dict[str, str]],
    llm_adapter: LLMAdapter,
    output_dir: Optional[Path] = None
) -> Dossier:
    """
    Build comprehensive dossier for a lead

    Args:
        lead_data: Lead data dict (should include LeadRecord fields)
        pages: List of page dicts with 'url' and 'content' keys
        llm_adapter: Configured LLM adapter
        output_dir: Optional output directory for saving dossier

    Returns:
        Dossier object
    """
    logger.info(f"Building dossier for {lead_data.get('name', 'Unknown')}")

    if not pages:
        logger.warning("No pages provided for dossier building")
        return Dossier(
            company_name=lead_data.get('name', 'Unknown'),
            website=lead_data.get('website', ''),
            generated_at=datetime.now(),
            company_overview="No pages available for analysis",
            services_products=[],
            digital_presence=DigitalPresence(
                website_quality="Not assessed - no pages",
                social_activity="Not assessed",
                online_reputation="Not assessed"
            ),
            signals=Signals(),
            issues=[],
            quick_wins=[],
            pages_analyzed=0,
            sources=[]
        )

    # Get prompts
    system_prompt, user_prompt = format_dossier_prompt(lead_data, pages)

    # Call LLM
    logger.debug(f"Calling LLM to analyze {len(pages)} pages")
    response = llm_adapter.chat_with_system(
        user_message=user_prompt,
        system_message=system_prompt,
        temperature=0.2  # Lower temp for factual output
    )

    # Parse response
    dossier = parse_dossier_response(response, lead_data, pages)
    logger.info(f"Dossier built: {len(dossier.quick_wins)} quick wins, {len(dossier.issues)} issues")

    # Save to file if output_dir provided
    if output_dir:
        save_dossier(dossier, output_dir)

    return dossier


def save_dossier(dossier: Dossier, output_dir: Path) -> tuple[Path, Path]:
    """
    Save dossier to markdown and JSON files

    Args:
        dossier: Dossier to save
        output_dir: Output directory

    Returns:
        Tuple of (markdown_path, json_path)
    """
    # Create slug from company name
    slug = dossier.company_name.replace(' ', '_').replace('.', '_').lower()

    # Create filenames
    timestamp = dossier.generated_at.strftime('%Y%m%d_%H%M%S')
    md_filename = f"{slug}_dossier_{timestamp}.md"
    json_filename = f"{slug}_sources_{timestamp}.json"

    md_path = output_dir / md_filename
    json_path = output_dir / json_filename

    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build markdown content
    md_content = f"# Dossier: {dossier.company_name}\n\n"
    md_content += f"**Website**: {dossier.website}\n"
    md_content += f"**Generated**: {dossier.generated_at.strftime('%Y-%m-%d %H:%M')}\n"
    md_content += f"**Pages Analyzed**: {dossier.pages_analyzed}\n\n"
    md_content += "---\n\n"

    # Company overview
    md_content += "## Company Overview\n\n"
    md_content += f"{dossier.company_overview}\n\n"

    # Services/Products
    md_content += "## Services & Products\n\n"
    for service in dossier.services_products:
        md_content += f"- {service}\n"
    md_content += "\n"

    # Digital presence
    md_content += "## Digital Presence Analysis\n\n"
    md_content += f"**Website Quality**: {dossier.digital_presence.website_quality}\n\n"
    md_content += f"**Social Media Activity**: {dossier.digital_presence.social_activity}\n\n"
    md_content += f"**Online Reputation**: {dossier.digital_presence.online_reputation}\n\n"

    # Signals
    md_content += "## Signals & Opportunities\n\n"

    if dossier.signals.positive:
        md_content += "### ✅ Positive Signals\n\n"
        for signal in dossier.signals.positive:
            md_content += f"- {signal}\n"
        md_content += "\n"

    if dossier.signals.growth:
        md_content += "### 📈 Growth Signals\n\n"
        for signal in dossier.signals.growth:
            md_content += f"- {signal}\n"
        md_content += "\n"

    if dossier.signals.pain:
        md_content += "### ⚠️ Pain Signals\n\n"
        for signal in dossier.signals.pain:
            md_content += f"- {signal}\n"
        md_content += "\n"

    # Issues
    if dossier.issues:
        md_content += "## Issues Detected\n\n"

        # Group by severity
        critical = [i for i in dossier.issues if i.severity == 'critical']
        high = [i for i in dossier.issues if i.severity == 'high']
        medium = [i for i in dossier.issues if i.severity == 'medium']
        low = [i for i in dossier.issues if i.severity == 'low']

        if critical:
            md_content += "### 🔴 Critical Issues\n\n"
            for issue in critical:
                md_content += f"- **{issue.category.upper()}**: {issue.description}\n"
                md_content += f"  - Source: {issue.source}\n"
            md_content += "\n"

        if high:
            md_content += "### 🟠 High Priority Issues\n\n"
            for issue in high:
                md_content += f"- **{issue.category.upper()}**: {issue.description}\n"
                md_content += f"  - Source: {issue.source}\n"
            md_content += "\n"

        if medium:
            md_content += "### 🟡 Medium Priority Issues\n\n"
            for issue in medium:
                md_content += f"- **{issue.category.upper()}**: {issue.description}\n"
                md_content += f"  - Source: {issue.source}\n"
            md_content += "\n"

        if low:
            md_content += "### 🟢 Low Priority Issues\n\n"
            for issue in low:
                md_content += f"- **{issue.category.upper()}**: {issue.description}\n"
                md_content += f"  - Source: {issue.source}\n"
            md_content += "\n"

    # Quick wins
    md_content += "## 48-Hour Quick Wins\n\n"
    for i, win in enumerate(dossier.quick_wins, 1):
        md_content += f"### {i}. {win.title}\n\n"
        md_content += f"**Action**: {win.action}\n\n"
        md_content += f"**Expected Impact**: {win.impact}\n\n"
        md_content += f"**Effort**: {win.effort.title()}\n\n"
        md_content += f"**Priority**: {win.priority}/5\n\n"
        md_content += "---\n\n"

    # Sources
    md_content += "## Sources\n\n"
    for source in dossier.sources:
        md_content += f"- {source}\n"

    # Write markdown file
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # Write sources JSON
    sources_data = {
        'company_name': dossier.company_name,
        'website': dossier.website,
        'generated_at': dossier.generated_at.isoformat(),
        'sources': dossier.sources
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(sources_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved dossier to {md_path}")
    logger.info(f"Saved sources to {json_path}")

    return md_path, json_path

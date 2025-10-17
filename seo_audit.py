"""
SEO Content Audit Module
Analyzes web pages for SEO quality with LLM scoring
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from selectolax.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import re
from logger import get_logger

logger = get_logger(__name__)


@dataclass
class SEOAuditResult:
    """A data class for the result of an SEO content audit.

    Attributes:
        url (str): The URL of the audited page.
        title (Optional[str]): The title of the page.
        title_length (int): The length of the title.
        meta_description (Optional[str]): The meta description of the page.
        meta_description_length (int): The length of the meta description.
        meta_keywords (Optional[str]): The meta keywords of the page.
        canonical_url (Optional[str]): The canonical URL of the page.
        og_tags (Dict[str, str]): A dictionary of Open Graph tags.
        twitter_tags (Dict[str, str]): A dictionary of Twitter card tags.
        h1_tags (List[str]): A list of H1 tags.
        h2_tags (List[str]): A list of H2 tags.
        h3_tags (List[str]): A list of H3 tags.
        heading_structure (Dict[str, int]): A dictionary representing the heading structure.
        total_images (int): The total number of images on the page.
        images_with_alt (int): The number of images with alt text.
        images_without_alt (int): The number of images without alt text.
        image_alt_coverage (float): The percentage of images with alt text.
        image_details (List[Dict[str, str]]): A list of dictionaries with details about each image.
        total_links (int): The total number of links on the page.
        internal_links (int): The number of internal links.
        external_links (int): The number of external links.
        nofollow_links (int): The number of nofollow links.
        broken_links_suspected (int): The number of suspected broken links.
        word_count (int): The word count of the page.
        paragraph_count (int): The number of paragraphs on the page.
        avg_paragraph_length (float): The average length of paragraphs.
        schema_types (List[str]): A list of schema.org types found on the page.
        issues (List[str]): A list of SEO issues found on the page.
        llm_score (Optional[float]): The content quality score from the LLM.
        llm_feedback (Optional[str]): The feedback on content quality from the LLM.
        seo_score (float): The overall SEO score (0-100).
    """
    url: str
    title: Optional[str] = None
    title_length: int = 0
    meta_description: Optional[str] = None
    meta_description_length: int = 0
    meta_keywords: Optional[str] = None
    canonical_url: Optional[str] = None
    og_tags: Dict[str, str] = field(default_factory=dict)
    twitter_tags: Dict[str, str] = field(default_factory=dict)

    # Headings
    h1_tags: List[str] = field(default_factory=list)
    h2_tags: List[str] = field(default_factory=list)
    h3_tags: List[str] = field(default_factory=list)
    heading_structure: Dict[str, int] = field(default_factory=dict)

    # Images
    total_images: int = 0
    images_with_alt: int = 0
    images_without_alt: int = 0
    image_alt_coverage: float = 0.0
    image_details: List[Dict[str, str]] = field(default_factory=list)

    # Links
    total_links: int = 0
    internal_links: int = 0
    external_links: int = 0
    nofollow_links: int = 0
    broken_links_suspected: int = 0

    # Content
    word_count: int = 0
    paragraph_count: int = 0
    avg_paragraph_length: float = 0.0

    # Schema.org
    schema_types: List[str] = field(default_factory=list)

    # Issues
    issues: List[str] = field(default_factory=list)

    # LLM Score
    llm_score: Optional[float] = None
    llm_feedback: Optional[str] = None

    # Overall score (0-100)
    seo_score: float = 0.0


class SEOAuditor:
    """A class for performing SEO content audits on web pages."""

    def __init__(self, llm_client=None):
        """Initializes the SEOAuditor.

        Args:
            llm_client: An optional LLMClient instance for content scoring.
        """
        self.llm_client = llm_client

    def audit_url(self, url: str, html: str) -> SEOAuditResult:
        """Perform a comprehensive SEO audit on a given URL and its HTML content.

        Args:
            url (str): The URL being audited.
            html (str): The HTML content of the page.

        Returns:
            SEOAuditResult: An object containing all the audit metrics.
        """
        result = SEOAuditResult(url=url)

        try:
            tree = HTMLParser(html)

            # Audit meta tags
            self._audit_meta_tags(tree, result)

            # Audit headings
            self._audit_headings(tree, result)

            # Audit images
            self._audit_images(tree, url, result)

            # Audit links
            self._audit_links(tree, url, result)

            # Audit content
            self._audit_content(tree, result)

            # Audit structured data
            self._audit_schema(tree, result)

            # Calculate technical SEO score
            result.seo_score = self._calculate_seo_score(result)

            # LLM scoring if available
            if self.llm_client:
                self._llm_score_content(tree, result)

        except Exception as e:
            logger.error(f"Error auditing {url}: {e}")
            result.issues.append(f"Audit error: {str(e)}")

        return result

    def _audit_meta_tags(self, tree: HTMLParser, result: SEOAuditResult):
        """Audit the meta tags of the page.

        Args:
            tree (HTMLParser): The parsed HTML tree.
            result (SEOAuditResult): The audit result object to populate.
        """
        # Title
        title_tag = tree.css_first("title")
        if title_tag:
            result.title = title_tag.text(strip=True)
            result.title_length = len(result.title)

            if result.title_length == 0:
                result.issues.append("Empty title tag")
            elif result.title_length < 30:
                result.issues.append(f"Title too short ({result.title_length} chars, recommend 50-60)")
            elif result.title_length > 60:
                result.issues.append(f"Title too long ({result.title_length} chars, may be truncated)")
        else:
            result.issues.append("Missing title tag")

        # Meta tags
        for meta in tree.css("meta"):
            name = meta.attributes.get("name", "").lower()
            prop = meta.attributes.get("property", "").lower()
            content = meta.attributes.get("content", "")

            # Description
            if name == "description":
                result.meta_description = content
                result.meta_description_length = len(content)

                if result.meta_description_length == 0:
                    result.issues.append("Empty meta description")
                elif result.meta_description_length < 120:
                    result.issues.append(f"Meta description too short ({result.meta_description_length} chars, recommend 150-160)")
                elif result.meta_description_length > 160:
                    result.issues.append(f"Meta description too long ({result.meta_description_length} chars)")

            # Keywords
            elif name == "keywords":
                result.meta_keywords = content

            # Open Graph
            elif prop.startswith("og:"):
                result.og_tags[prop] = content

            # Twitter
            elif name.startswith("twitter:"):
                result.twitter_tags[name] = content

        if not result.meta_description:
            result.issues.append("Missing meta description")

        # Canonical
        canonical = tree.css_first('link[rel="canonical"]')
        if canonical:
            result.canonical_url = canonical.attributes.get("href")

    def _audit_headings(self, tree: HTMLParser, result: SEOAuditResult):
        """Audit the heading structure of the page.

        Args:
            tree (HTMLParser): The parsed HTML tree.
            result (SEOAuditResult): The audit result object to populate.
        """
        result.h1_tags = [h.text(strip=True) for h in tree.css("h1")]
        result.h2_tags = [h.text(strip=True) for h in tree.css("h2")]
        result.h3_tags = [h.text(strip=True) for h in tree.css("h3")]

        result.heading_structure = {
            "h1": len(result.h1_tags),
            "h2": len(result.h2_tags),
            "h3": len(result.h3_tags),
            "h4": len(tree.css("h4")),
            "h5": len(tree.css("h5")),
            "h6": len(tree.css("h6"))
        }

        # Check H1
        if len(result.h1_tags) == 0:
            result.issues.append("Missing H1 tag")
        elif len(result.h1_tags) > 1:
            result.issues.append(f"Multiple H1 tags found ({len(result.h1_tags)}, recommend 1)")

        # Check heading hierarchy
        if result.heading_structure["h1"] > 0 and result.heading_structure["h2"] == 0:
            if result.heading_structure["h3"] > 0:
                result.issues.append("H3 tags present without H2 (poor hierarchy)")

    def _audit_images(self, tree: HTMLParser, base_url: str, result: SEOAuditResult):
        """Audit the images and their alt attributes on the page.

        Args:
            tree (HTMLParser): The parsed HTML tree.
            base_url (str): The base URL for resolving relative image paths.
            result (SEOAuditResult): The audit result object to populate.
        """
        images = tree.css("img")
        result.total_images = len(images)

        for img in images:
            src = img.attributes.get("src", "")
            alt = img.attributes.get("alt", "")

            img_info = {
                "src": urljoin(base_url, src),
                "alt": alt,
                "has_alt": bool(alt)
            }
            result.image_details.append(img_info)

            if alt:
                result.images_with_alt += 1
            else:
                result.images_without_alt += 1

        if result.total_images > 0:
            result.image_alt_coverage = (result.images_with_alt / result.total_images) * 100

            if result.image_alt_coverage < 80:
                result.issues.append(
                    f"Low image alt coverage ({result.image_alt_coverage:.1f}%, {result.images_without_alt} missing)"
                )

    def _audit_links(self, tree: HTMLParser, base_url: str, result: SEOAuditResult):
        """Audit the internal and external links on the page.

        Args:
            tree (HTMLParser): The parsed HTML tree.
            base_url (str): The base URL for identifying internal links.
            result (SEOAuditResult): The audit result object to populate.
        """
        base_domain = urlparse(base_url).netloc
        links = tree.css("a[href]")

        result.total_links = len(links)

        for link in links:
            href = link.attributes.get("href", "")
            rel = link.attributes.get("rel", "")

            # Skip anchors and javascript
            if href.startswith("#") or href.startswith("javascript:"):
                continue

            # Full URL
            full_url = urljoin(base_url, href)
            link_domain = urlparse(full_url).netloc

            # Internal vs external
            if link_domain == base_domain or not link_domain:
                result.internal_links += 1
            else:
                result.external_links += 1

            # Nofollow
            if "nofollow" in rel:
                result.nofollow_links += 1

        if result.total_links == 0:
            result.issues.append("No links found on page")
        elif result.internal_links == 0:
            result.issues.append("No internal links found")

    def _audit_content(self, tree: HTMLParser, result: SEOAuditResult):
        """Audit the textual content of the page.

        Args:
            tree (HTMLParser): The parsed HTML tree.
            result (SEOAuditResult): The audit result object to populate.
        """
        # Get visible text
        text = tree.text(separator=" ", strip=True)

        # Word count
        words = re.findall(r'\b\w+\b', text)
        result.word_count = len(words)

        # Paragraphs
        paragraphs = tree.css("p")
        result.paragraph_count = len(paragraphs)

        if result.paragraph_count > 0:
            para_lengths = [len(re.findall(r'\b\w+\b', p.text())) for p in paragraphs]
            result.avg_paragraph_length = sum(para_lengths) / len(para_lengths)

        # Content quality checks
        if result.word_count < 300:
            result.issues.append(f"Thin content ({result.word_count} words, recommend 300+)")

        if result.paragraph_count == 0:
            result.issues.append("No paragraphs found")

    def _audit_schema(self, tree: HTMLParser, result: SEOAuditResult):
        """Audit the structured data (schema.org) on the page.

        Args:
            tree (HTMLParser): The parsed HTML tree.
            result (SEOAuditResult): The audit result object to populate.
        """
        # JSON-LD
        for script in tree.css('script[type="application/ld+json"]'):
            try:
                import json
                data = json.loads(script.text())
                schema_type = data.get("@type", "Unknown")
                result.schema_types.append(schema_type)
            except:
                pass

        # Microdata
        for elem in tree.css("[itemtype]"):
            itemtype = elem.attributes.get("itemtype", "")
            if "schema.org" in itemtype:
                schema_name = itemtype.split("/")[-1]
                result.schema_types.append(schema_name)

    def _calculate_seo_score(self, result: SEOAuditResult) -> float:
        """Calculate the technical SEO score based on the audit results.

        Args:
            result (SEOAuditResult): The audit result object.

        Returns:
            float: The calculated SEO score (0-100).
        """
        score = 0.0

        # Title (15 points)
        if result.title and 50 <= result.title_length <= 60:
            score += 15
        elif result.title and 30 <= result.title_length < 70:
            score += 10
        elif result.title:
            score += 5

        # Meta description (15 points)
        if result.meta_description and 150 <= result.meta_description_length <= 160:
            score += 15
        elif result.meta_description and 120 <= result.meta_description_length < 180:
            score += 10
        elif result.meta_description:
            score += 5

        # H1 (10 points)
        if len(result.h1_tags) == 1:
            score += 10
        elif len(result.h1_tags) > 0:
            score += 5

        # Image alt coverage (10 points)
        if result.image_alt_coverage >= 90:
            score += 10
        elif result.image_alt_coverage >= 70:
            score += 7
        elif result.image_alt_coverage >= 50:
            score += 4

        # Content length (15 points)
        if result.word_count >= 1000:
            score += 15
        elif result.word_count >= 500:
            score += 10
        elif result.word_count >= 300:
            score += 7
        elif result.word_count >= 100:
            score += 3

        # Heading structure (10 points)
        if result.heading_structure["h2"] > 0:
            score += 5
        if result.heading_structure["h3"] > 0:
            score += 3
        if result.heading_structure["h1"] == 1 and result.heading_structure["h2"] > 0:
            score += 2

        # Links (10 points)
        if result.internal_links > 5:
            score += 5
        elif result.internal_links > 0:
            score += 3

        if result.external_links > 0:
            score += 3
        elif result.total_links > 0:
            score += 2

        # Schema (5 points)
        if len(result.schema_types) > 0:
            score += 5

        # Penalties for issues (max -20)
        penalty = min(len(result.issues) * 2, 20)
        score -= penalty

        return max(0, min(100, score))

    def _llm_score_content(self, tree: HTMLParser, result: SEOAuditResult):
        """Use an LLM to score the quality of the page's content.

        Args:
            tree (HTMLParser): The parsed HTML tree.
            result (SEOAuditResult): The audit result object to populate.
        """
        if not self.llm_client:
            return

        try:
            # Extract main content
            text = tree.text(separator="\n", strip=True)[:2000]  # Limit for LLM context

            prompt = f"""Analyze this web page content and provide a quality score from 0-100 and brief feedback.

Title: {result.title}
Meta Description: {result.meta_description}
Word Count: {result.word_count}

Content Preview:
{text}

Provide:
1. A quality score (0-100) based on clarity, value, engagement, and SEO-friendliness
2. 2-3 bullet points of specific feedback

Format:
SCORE: [number]
FEEDBACK:
- [point 1]
- [point 2]
"""

            response = self.llm_client.summarize_leads([], prompt)

            # Parse response
            if "SCORE:" in response:
                score_line = [line for line in response.split("\n") if "SCORE:" in line][0]
                score_str = re.findall(r'\d+', score_line)
                if score_str:
                    result.llm_score = float(score_str[0])

            # Extract feedback
            if "FEEDBACK:" in response:
                feedback_start = response.index("FEEDBACK:")
                result.llm_feedback = response[feedback_start:].strip()

        except Exception as e:
            logger.error(f"LLM scoring error: {e}")
            result.issues.append(f"LLM scoring failed: {str(e)}")

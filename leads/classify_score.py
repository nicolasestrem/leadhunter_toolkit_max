"""
Lead classification and scoring system
Combines heuristic scoring with LLM-based classification
"""

import json
from typing import Dict, Any, Optional
from models import LeadRecord, Lead, Social
from llm.adapter import LLMAdapter
from llm.prompt_loader import get_classification_prompt
from logger import get_logger

logger = get_logger(__name__)


def calculate_quality_score(lead_data: Dict[str, Any]) -> float:
    """
    Calculate data quality score based on completeness

    Args:
        lead_data: Lead data dict

    Returns:
        Quality score (0-10)
    """
    score = 0.0

    # Email presence and count (0-3 points)
    emails = lead_data.get('emails', [])
    if len(emails) >= 2:
        score += 3.0
    elif len(emails) == 1:
        score += 2.0

    # Phone presence and count (0-2 points)
    phones = lead_data.get('phones', [])
    if len(phones) >= 2:
        score += 2.0
    elif len(phones) == 1:
        score += 1.5

    # Social media presence (0-2 points)
    social = lead_data.get('social', {})
    if isinstance(social, dict):
        social_count = len([v for v in social.values() if v])
        if social_count >= 3:
            score += 2.0
        elif social_count == 2:
            score += 1.5
        elif social_count == 1:
            score += 1.0

    # Address/location (0-1 point)
    if lead_data.get('address') or lead_data.get('city'):
        score += 1.0

    # Company name (0-1 point)
    if lead_data.get('name'):
        score += 1.0

    # HTTPS (0-1 point)
    website = lead_data.get('website', '')
    if website.startswith('https://'):
        score += 1.0

    return min(score, 10.0)


def calculate_priority_score(
    quality_score: float,
    fit_score: float,
    quality_signals: list,
    issue_flags: list
) -> float:
    """
    Calculate overall priority score

    Formula: (quality_score * 0.3 + fit_score * 0.5) - (num_issues * 0.5) + (num_signals * 0.3)

    Args:
        quality_score: Data quality score (0-10)
        fit_score: SMB fit score from LLM (0-10)
        quality_signals: List of positive signals
        issue_flags: List of issues

    Returns:
        Priority score (0-10)
    """
    # Base score from quality and fit
    base_score = (quality_score * 0.3) + (fit_score * 0.5)

    # Penalties for issues
    issue_penalty = len(issue_flags) * 0.5

    # Bonuses for quality signals
    signal_bonus = len(quality_signals) * 0.3

    # Calculate final score
    priority = base_score - issue_penalty + signal_bonus

    # Clamp to 0-10 range
    return max(0.0, min(priority, 10.0))


def classify_with_llm(
    lead_data: Dict[str, Any],
    llm_adapter: LLMAdapter
) -> Dict[str, Any]:
    """
    Classify lead using LLM

    Args:
        lead_data: Lead data dict
        llm_adapter: Configured LLM adapter

    Returns:
        Dict with classification results:
        {
            'business_type': str,
            'issue_flags': List[str],
            'quality_signals': List[str],
            'fit_score': float,
            'notes': str
        }
    """
    try:
        logger.debug(f"Classifying lead: {lead_data.get('name', 'Unknown')}")

        # Get prompts
        system_prompt, user_prompt = get_classification_prompt(lead_data)

        # Call LLM
        response = llm_adapter.chat_with_system(
            user_message=user_prompt,
            system_message=system_prompt,
            temperature=0.1  # Low temp for consistent classification
        )

        logger.debug(f"LLM response: {response[:200]}...")

        # Parse JSON response
        # Try to extract JSON from response (might be wrapped in markdown)
        response_clean = response.strip()

        # Remove markdown code blocks if present
        if response_clean.startswith('```json'):
            response_clean = response_clean[7:]
        elif response_clean.startswith('```'):
            response_clean = response_clean[3:]

        if response_clean.endswith('```'):
            response_clean = response_clean[:-3]

        response_clean = response_clean.strip()

        # Parse JSON
        classification = json.loads(response_clean)

        logger.info(f"Classification successful: type={classification.get('business_type')}, fit={classification.get('fit_score')}")

        return classification

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response was: {response}")
        # Return default classification
        return {
            'business_type': 'other',
            'issue_flags': [],
            'quality_signals': [],
            'fit_score': 5.0,
            'notes': 'Classification failed - could not parse LLM response'
        }

    except Exception as e:
        logger.error(f"Error during LLM classification: {e}", exc_info=True)
        # Return default classification
        return {
            'business_type': 'other',
            'issue_flags': [],
            'quality_signals': [],
            'fit_score': 5.0,
            'notes': f'Classification failed: {str(e)}'
        }


def classify_and_score_lead(
    lead: Lead,
    llm_adapter: LLMAdapter,
    content_sample: str = "",
    use_llm: bool = True
) -> LeadRecord:
    """
    Classify and score a lead with enhanced metrics

    Args:
        lead: Input Lead object
        llm_adapter: Configured LLM adapter
        content_sample: Sample of page content for LLM analysis
        use_llm: Whether to use LLM classification (if False, only heuristics)

    Returns:
        Enhanced LeadRecord with classification and scores
    """
    logger.debug(f"Classifying and scoring lead: {lead.name or lead.domain}")

    # Convert to dict for processing
    lead_data = lead.dict()
    lead_data['content_sample'] = content_sample

    # Calculate quality score (heuristic)
    quality_score = calculate_quality_score(lead_data)

    # LLM classification
    if use_llm and llm_adapter:
        classification = classify_with_llm(lead_data, llm_adapter)
    else:
        # Use heuristics only
        classification = {
            'business_type': lead.tags[0] if lead.tags else 'other',
            'issue_flags': [],
            'quality_signals': [],
            'fit_score': quality_score * 0.7,  # Derive from quality
            'notes': 'Heuristic classification only'
        }

    # Calculate priority score
    priority_score = calculate_priority_score(
        quality_score=quality_score,
        fit_score=classification.get('fit_score', 5.0),
        quality_signals=classification.get('quality_signals', []),
        issue_flags=classification.get('issue_flags', [])
    )

    # Create LeadRecord
    record = LeadRecord.from_lead(lead)
    record.score_quality = quality_score
    record.score_fit = classification.get('fit_score', 5.0)
    record.score_priority = priority_score
    record.business_type = classification.get('business_type', 'other')
    record.issue_flags = classification.get('issue_flags', [])
    record.quality_signals = classification.get('quality_signals', [])
    record.content_sample = content_sample[:500]

    # Update notes with LLM insights
    if classification.get('notes'):
        if record.notes:
            record.notes = f"{record.notes}\n\n{classification['notes']}"
        else:
            record.notes = classification['notes']

    # Update legacy score for backward compatibility
    record.score = priority_score

    logger.info(
        f"Scoring complete: quality={quality_score:.1f}, "
        f"fit={record.score_fit:.1f}, priority={priority_score:.1f}"
    )

    return record


def batch_classify_and_score(
    leads: list[Lead],
    llm_adapter: LLMAdapter,
    content_samples: Optional[Dict[str, str]] = None,
    use_llm: bool = True
) -> list[LeadRecord]:
    """
    Classify and score multiple leads

    Args:
        leads: List of Lead objects
        llm_adapter: Configured LLM adapter
        content_samples: Optional dict mapping domain to content sample
        use_llm: Whether to use LLM classification

    Returns:
        List of LeadRecord objects
    """
    logger.info(f"Batch processing {len(leads)} leads")

    content_samples = content_samples or {}
    records = []

    for lead in leads:
        content = content_samples.get(lead.domain, "")
        record = classify_and_score_lead(lead, llm_adapter, content, use_llm)
        records.append(record)

    logger.info(f"Batch processing complete: {len(records)} records created")

    return records

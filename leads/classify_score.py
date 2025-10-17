"""
Lead classification and scoring system
Combines heuristic scoring with LLM-based classification
"""

import json
from typing import Dict, Any, Optional
from models import LeadRecord, Lead, Social
from llm.adapter import LLMAdapter
from llm.prompt_loader import get_classification_prompt
from config.loader import ConfigLoader
from logger import get_logger

# Import plugin system
try:
    from plugins import call_plugin_hook
    PLUGINS_AVAILABLE = True
except ImportError:
    PLUGINS_AVAILABLE = False
    call_plugin_hook = lambda *args, **kwargs: []

logger = get_logger(__name__)


def calculate_quality_score(lead_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> float:
    """Calculate the data quality score based on the completeness of the lead data.

    This function assesses the quality of a lead by checking for the presence and count
    of important contact information like emails, phone numbers, and social media links.
    It applies configurable weights for each attribute, which can be influenced by
    vertical-specific presets.

    Args:
        lead_data (Dict[str, Any]): The lead data dictionary.
        config (Optional[Dict[str, Any]]): An optional configuration dictionary with
                                            scoring weights. If not provided, it is
                                            loaded automatically.

    Returns:
        float: The calculated quality score, ranging from 0 to 10.
    """
    # Load config if not provided
    if config is None:
        config_loader = ConfigLoader()
        config = config_loader.get_merged_config()

    # Get scoring weights from config (includes vertical overrides)
    scoring_config = config.get('scoring', {})
    email_weight = scoring_config.get('email_weight', 3.0)
    phone_weight = scoring_config.get('phone_weight', 2.0)
    social_weight = scoring_config.get('social_weight', 2.0)

    score = 0.0

    # Email presence and count
    emails = {
        email.strip().lower()
        for email in lead_data.get('emails', [])
        if isinstance(email, str) and email.strip()
    }
    if emails:
        score += min(len(emails), 3) * email_weight

    # Phone presence and count
    phones = {
        phone.strip()
        for phone in lead_data.get('phones', [])
        if isinstance(phone, str) and phone.strip()
    }
    if phones:
        score += min(len(phones), 2) * phone_weight

    # Social media presence
    social = lead_data.get('social', {})
    if isinstance(social, dict):
        social_count = len({v for v in social.values() if v})
        if social_count:
            score += min(social_count, 3) * social_weight

    # Address/location (0-1 point)
    if lead_data.get('address'):
        score += 0.6
    if lead_data.get('city'):
        score += 0.4

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
    """Calculate the overall priority score for a lead.

    This score is a composite metric derived from the quality score, the fit score (from LLM),
    and adjustments based on the number of positive signals and identified issues. The
    formula is: (quality_score * 0.3 + fit_score * 0.5) - (num_issues * 0.5) + (num_signals * 0.3).

    Args:
        quality_score (float): The data quality score (0-10).
        fit_score (float): The SMB fit score from the LLM (0-10).
        quality_signals (list): A list of positive signals.
        issue_flags (list): A list of identified issues.

    Returns:
        float: The final priority score, clamped between 0 and 10.
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
    """Classify a lead using a Large Language Model.

    This function sends the lead data to an LLM to obtain a detailed classification,
    which includes the business type, issue flags, quality signals, and a fit score.
    It is designed to handle potential JSON parsing errors from the LLM's response.

    Args:
        lead_data (Dict[str, Any]): The lead data dictionary.
        llm_adapter (LLMAdapter): A configured instance of the LLM adapter.

    Returns:
        Dict[str, Any]: A dictionary with the classification results.
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
    """Classify and score a lead with enhanced metrics.

    This function serves as the main orchestrator for processing a single lead. It combines
    heuristic scoring with LLM-based classification to produce a comprehensive LeadRecord.
    It also integrates with a plugin system to allow for extensible, custom processing hooks.

    Args:
        lead (Lead): The input Lead object.
        llm_adapter (LLMAdapter): A configured LLM adapter.
        content_sample (str): A sample of page content for LLM analysis.
        use_llm (bool): If True, use the LLM for classification; otherwise, use only heuristics.

    Returns:
        LeadRecord: An enhanced LeadRecord with classification and scores.
    """
    logger.debug(f"Classifying and scoring lead: {lead.name or lead.domain}")

    # Convert to dict for processing
    lead_data = lead.dict()
    lead_data['content_sample'] = content_sample

    # Call before_classification hook
    if PLUGINS_AVAILABLE:
        try:
            logger.debug("Calling before_classification hook")
            call_plugin_hook('before_classification', lead_data)
        except Exception as e:
            logger.warning(f"Error in before_classification hook: {e}")

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

    # Call after_classification hook (allow plugins to modify record)
    if PLUGINS_AVAILABLE:
        try:
            logger.debug("Calling after_classification hook")
            record_dict = record.dict()
            hook_results = call_plugin_hook('after_classification', record_dict)

            # If any plugin returned modified data, use the last one
            if hook_results and hook_results[-1]:
                modified = hook_results[-1]
                # Update record with modifications
                for key, value in modified.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                logger.debug("Applied plugin modifications to lead record")
        except Exception as e:
            logger.warning(f"Error in after_classification hook: {e}")

    return record


def batch_classify_and_score(
    leads: list[Lead],
    llm_adapter: LLMAdapter,
    content_samples: Optional[Dict[str, str]] = None,
    use_llm: bool = True
) -> list[LeadRecord]:
    """Classify and score multiple leads in a batch.

    This function is designed for efficient processing of a list of leads. It iterates
    through the leads, applying the 'classify_and_score_lead' function to each one.

    Args:
        leads (list[Lead]): A list of Lead objects.
        llm_adapter (LLMAdapter): A configured LLM adapter.
        content_samples (Optional[Dict[str, str]]): A dictionary mapping a domain to its content sample.
        use_llm (bool): If True, use the LLM for classification.

    Returns:
        list[LeadRecord]: A list of processed LeadRecord objects.
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

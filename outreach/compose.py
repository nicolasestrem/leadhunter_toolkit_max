"""
Outreach message composer
Generates personalized outreach drafts using LLM
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml
from llm.adapter import LLMAdapter
from localization.i18n import get_tone_preset, get_language_name
from outreach.deliverability_checks import check_deliverability, format_deliverability_report
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

BASE_DIR = Path(__file__).parent.parent
PROMPT_LIBRARY_DIR = BASE_DIR / "llm" / "prompt_library"


@dataclass
class OutreachVariant:
    """Single outreach message variant"""
    angle: str  # problem-focused, opportunity-focused, quick-win
    subject: str  # Subject line (email only)
    body: str  # Message body
    cta: str  # Call to action
    tone_used: str  # professional, friendly, direct
    personalization_notes: str  # Notes on personalization
    deliverability_score: int = 0
    deliverability_issues: List = None


@dataclass
class OutreachResult:
    """Result of outreach generation"""
    variants: List[OutreachVariant]
    message_type: str  # email, linkedin, sms
    language: str
    generated_at: datetime
    lead_name: str
    deliverability_passed: bool


def load_outreach_prompt_config() -> Dict:
    """Load outreach prompt configuration from YAML"""
    prompt_path = PROMPT_LIBRARY_DIR / "outreach.yml"

    with open(prompt_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def _build_vertical_context(vertical: Dict) -> str:
    """
    Build vertical-specific context string for outreach prompts

    Args:
        vertical: Vertical config dict from merged config

    Returns:
        Formatted context string or empty string if no vertical active
    """
    if not vertical or 'name' not in vertical:
        return ""

    outreach = vertical.get('outreach', {})
    if not outreach:
        return ""

    context_lines = ["**Your Context** (optimized for {}):\n".format(
        vertical.get('description', vertical.get('name', 'this vertical'))
    )]

    # Focus areas
    focus_areas = outreach.get('focus_areas', [])
    if focus_areas:
        context_lines.append("  - **Focus areas**: {}".format(
            ', '.join(focus_areas)
        ))

    # Value propositions
    value_props = outreach.get('value_props', [])
    if value_props:
        context_lines.append("  - **Value propositions**:")
        for prop in value_props:
            context_lines.append(f"    • {prop}")

    # Typical issues
    typical_issues = outreach.get('typical_issues', [])
    if typical_issues:
        context_lines.append("  - **Common issues to address**:")
        for issue in typical_issues:
            context_lines.append(f"    • {issue}")

    # Add default engagement info
    context_lines.append("  - **Typical engagement**: 2-5k EUR for first project, no long-term contracts")

    return '\n'.join(context_lines)


def format_outreach_prompt(
    lead_data: Dict,
    dossier_summary: str,
    message_type: str,
    language: str,
    tone: str = 'professional'
) -> tuple[str, str]:
    """
    Format outreach prompts (system + user)
    Applies vertical preset context if active

    Args:
        lead_data: Lead data dict
        dossier_summary: Summary from dossier
        message_type: email, linkedin, sms
        language: Target language
        tone: Communication tone

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    config = load_outreach_prompt_config()

    # Load merged config to get vertical context
    config_loader = ConfigLoader()
    merged_config = config_loader.get_merged_config()
    vertical_context = merged_config.get('vertical', {})

    # Get tone preset
    tone_preset = get_tone_preset(language, tone)
    language_name = get_language_name(language)

    # Get all tone presets for the language
    tones = config.get('tones', {}).get(language, {})

    # Format system prompt
    system_template = config.get('system_prompt_template', '')
    system_prompt = system_template.format(
        language=language,
        language_name=language_name,
        tone_description=tone_preset.get('description', ''),
        formality=tone_preset.get('formality', 'neutral'),
        professional_greeting=tones.get('professional', {}).get('greeting', 'Dear'),
        friendly_greeting=tones.get('friendly', {}).get('greeting', 'Hi'),
        direct_greeting=tones.get('direct', {}).get('greeting', 'Hello')
    )

    # Build vertical-specific context string
    your_context = _build_vertical_context(vertical_context)
    if your_context:
        logger.debug(
            f"Applying vertical context for '{vertical_context.get('name')}' "
            f"({vertical_context.get('description')})"
        )

    # Format user prompt
    user_template = config.get('user_prompt_template', '')
    user_prompt = user_template.format(
        company_name=lead_data.get('name', 'Unknown'),
        business_type=lead_data.get('business_type', 'business'),
        website=lead_data.get('website', ''),
        city=lead_data.get('city', ''),
        country=lead_data.get('country', ''),
        emails=', '.join(lead_data.get('emails', [])) or 'None',
        phones=', '.join(lead_data.get('phones', [])) or 'None',
        score_quality=lead_data.get('score_quality', 0),
        score_fit=lead_data.get('score_fit', 0),
        issue_flags=', '.join(lead_data.get('issue_flags', [])) or 'None',
        quality_signals=', '.join(lead_data.get('quality_signals', [])) or 'None',
        dossier_summary=dossier_summary or 'No dossier available yet',
        message_type=message_type
    )

    # Inject vertical context by replacing the "Your Context" section
    if your_context:
        # Replace the default context in the template
        default_context = """**Your Context**:
  - Your service: SMB digital consulting (quick-win SEO, web improvements, local marketing)
  - Your value prop: Tangible results in 48h, no long-term contracts
  - Typical engagement: 2-5k EUR for first project"""

        user_prompt = user_prompt.replace(default_context, your_context)

    return system_prompt, user_prompt


def parse_llm_outreach_response(response: str) -> List[OutreachVariant]:
    """
    Parse LLM response into OutreachVariant objects

    Args:
        response: LLM JSON response

    Returns:
        List of OutreachVariant objects
    """
    try:
        # Clean response (remove markdown code blocks if present)
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

        variants = []
        for variant_data in data.get('variants', []):
            variant = OutreachVariant(
                angle=variant_data.get('angle', 'unknown'),
                subject=variant_data.get('subject', ''),
                body=variant_data.get('body', ''),
                cta=variant_data.get('cta', ''),
                tone_used=variant_data.get('tone_used', 'professional'),
                personalization_notes=variant_data.get('personalization_notes', '')
            )
            variants.append(variant)

        return variants

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response: {e}")
        logger.error(f"Response was: {response[:500]}")
        # Return a single default variant
        return [OutreachVariant(
            angle='unknown',
            subject='Follow up',
            body='Error generating outreach message. Please try again.',
            cta='Reply to this message',
            tone_used='professional',
            personalization_notes='Failed to parse LLM response'
        )]


def compose_outreach(
    lead_data: Dict,
    llm_adapter: LLMAdapter,
    dossier_summary: str = "",
    message_type: str = 'email',
    language: str = 'en',
    tone: str = 'professional',
    output_dir: Optional[Path] = None
) -> OutreachResult:
    """
    Compose personalized outreach messages

    Args:
        lead_data: Lead data dict (should include LeadRecord fields)
        llm_adapter: Configured LLM adapter
        dossier_summary: Optional dossier summary for context
        message_type: Type of message (email, linkedin, sms)
        language: Target language (en, fr, de)
        tone: Communication tone (professional, friendly, direct)
        output_dir: Optional output directory for saving drafts

    Returns:
        OutreachResult with variants
    """
    logger.info(f"Composing {message_type} outreach for {lead_data.get('name', 'Unknown')}")

    # Call before_outreach hook (allow plugins to modify lead_data)
    if PLUGINS_AVAILABLE:
        try:
            logger.debug("Calling before_outreach hook")
            hook_results = call_plugin_hook('before_outreach', lead_data, message_type)

            # If any plugin returned modified data, use the last one
            if hook_results and hook_results[-1]:
                lead_data = hook_results[-1]
                logger.debug("Applied plugin modifications to lead data")
        except Exception as e:
            logger.warning(f"Error in before_outreach hook: {e}")

    # Get prompts
    system_prompt, user_prompt = format_outreach_prompt(
        lead_data=lead_data,
        dossier_summary=dossier_summary,
        message_type=message_type,
        language=language,
        tone=tone
    )

    # Call LLM
    logger.debug(f"Calling LLM with temperature=0.7 for creative outreach")
    response = llm_adapter.chat_with_system(
        user_message=user_prompt,
        system_message=system_prompt,
        temperature=0.7  # Higher temp for creative writing
    )

    # Parse response
    variants = parse_llm_outreach_response(response)
    logger.info(f"Generated {len(variants)} outreach variants")

    # Check deliverability for each variant
    all_passed = True
    for variant in variants:
        check_result = check_deliverability(
            subject=variant.subject,
            body=variant.body,
            message_type=message_type
        )
        variant.deliverability_score = check_result['score']
        variant.deliverability_issues = check_result['issues']

        if not check_result['passed']:
            all_passed = False
            logger.warning(
                f"Variant '{variant.angle}' failed deliverability check "
                f"(score: {variant.deliverability_score}/100)"
            )

    # Create result
    result = OutreachResult(
        variants=variants,
        message_type=message_type,
        language=language,
        generated_at=datetime.now(),
        lead_name=lead_data.get('name', 'Unknown'),
        deliverability_passed=all_passed
    )

    # Call after_outreach hook (allow plugins to modify or log results)
    if PLUGINS_AVAILABLE:
        try:
            logger.debug("Calling after_outreach hook")
            # Convert result to dict for plugins
            result_dict = {
                'variants': [
                    {
                        'angle': v.angle,
                        'subject': v.subject,
                        'body': v.body,
                        'cta': v.cta,
                        'tone_used': v.tone_used,
                        'deliverability_score': v.deliverability_score
                    }
                    for v in variants
                ],
                'message_type': message_type,
                'language': language,
                'lead_name': lead_data.get('name', 'Unknown')
            }
            call_plugin_hook('after_outreach', result_dict, lead_data)
        except Exception as e:
            logger.warning(f"Error in after_outreach hook: {e}")

    # Save to file if output_dir provided
    if output_dir:
        save_outreach_drafts(result, lead_data, output_dir)

    return result


def save_outreach_drafts(
    result: OutreachResult,
    lead_data: Dict,
    output_dir: Path
) -> Path:
    """
    Save outreach drafts to markdown file

    Args:
        result: OutreachResult to save
        lead_data: Lead data
        output_dir: Output directory

    Returns:
        Path to saved file
    """
    # Create slug from lead name/domain
    slug = lead_data.get('domain', lead_data.get('name', 'unknown'))
    slug = slug.replace('.', '_').replace(' ', '_').lower()

    # Create filename
    timestamp = result.generated_at.strftime('%Y%m%d_%H%M%S')
    filename = f"{slug}_outreach_{result.message_type}_{timestamp}.md"
    filepath = output_dir / filename

    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build markdown content
    content = f"# Outreach Drafts: {result.lead_name}\n\n"
    content += f"**Generated**: {result.generated_at.strftime('%Y-%m-%d %H:%M')}\n"
    content += f"**Type**: {result.message_type}\n"
    content += f"**Language**: {result.language}\n"
    content += f"**Deliverability**: {'✅ Passed' if result.deliverability_passed else '⚠️ Issues detected'}\n\n"

    content += "---\n\n"

    # Add each variant
    for i, variant in enumerate(result.variants, 1):
        content += f"## Variant {i}: {variant.angle.replace('-', ' ').title()}\n\n"

        if variant.subject:
            content += f"**Subject**: {variant.subject}\n\n"

        content += f"**Body**:\n\n{variant.body}\n\n"
        content += f"**CTA**: {variant.cta}\n\n"
        content += f"**Tone**: {variant.tone_used}\n\n"
        content += f"**Personalization**: {variant.personalization_notes}\n\n"

        # Add deliverability info
        content += f"**Deliverability Score**: {variant.deliverability_score}/100\n\n"

        if variant.deliverability_issues:
            from outreach.deliverability_checks import format_deliverability_report
            report = format_deliverability_report({
                'score': variant.deliverability_score,
                'issues': variant.deliverability_issues,
                'critical_count': len([i for i in variant.deliverability_issues if i.severity == 'critical']),
                'warning_count': len([i for i in variant.deliverability_issues if i.severity == 'warning']),
                'passed': variant.deliverability_score >= 80
            })
            content += f"{report}\n\n"

        content += "---\n\n"

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Saved outreach drafts to {filepath}")

    return filepath


def format_outreach_for_display(variant: OutreachVariant, message_type: str) -> str:
    """
    Format outreach variant for display in UI

    Args:
        variant: OutreachVariant to format
        message_type: Type of message

    Returns:
        Formatted string for display
    """
    output = f"**{variant.angle.replace('-', ' ').title()}** ({variant.tone_used})\n\n"

    if message_type == 'email' and variant.subject:
        output += f"📧 **Subject**: {variant.subject}\n\n"

    output += f"{variant.body}\n\n"
    output += f"✨ **CTA**: {variant.cta}\n\n"

    # Deliverability indicator
    if variant.deliverability_score >= 90:
        output += f"✅ Deliverability: {variant.deliverability_score}/100 (Excellent)\n"
    elif variant.deliverability_score >= 80:
        output += f"⚠️ Deliverability: {variant.deliverability_score}/100 (Good)\n"
    else:
        output += f"❌ Deliverability: {variant.deliverability_score}/100 (Needs improvement)\n"

    return output

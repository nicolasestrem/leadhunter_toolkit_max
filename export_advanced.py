"""
Advanced export functionality for Lead Hunter Toolkit
Supports filtering, multiple formats, consulting pack exports, and ZIP packaging
"""

import os
import json
import csv
import datetime
import zipfile
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import pandas as pd
from dataclasses import dataclass


OUT_DIR = Path(__file__).parent / "out"
OUT_DIR.mkdir(exist_ok=True)


@dataclass
class ExportFilter:
    """Filter configuration for exports"""
    min_score: float = 0.0
    max_score: float = 10.0
    min_quality: float = 0.0
    min_fit: float = 0.0
    min_priority: float = 0.0
    business_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    has_emails: Optional[bool] = None
    has_phones: Optional[bool] = None
    date_from: Optional[datetime.datetime] = None
    date_to: Optional[datetime.datetime] = None
    columns: Optional[List[str]] = None  # Specific columns to export


def apply_filters(leads: List[Dict[str, Any]], filters: ExportFilter) -> List[Dict[str, Any]]:
    """Apply filters to lead list"""
    filtered = []

    for lead in leads:
        # Score filters
        if "score" in lead:
            if not (filters.min_score <= lead.get("score", 0) <= filters.max_score):
                continue

        # Multi-dimensional scores
        if "score_quality" in lead:
            if lead.get("score_quality", 0) < filters.min_quality:
                continue
        if "score_fit" in lead:
            if lead.get("score_fit", 0) < filters.min_fit:
                continue
        if "score_priority" in lead:
            if lead.get("score_priority", 0) < filters.min_priority:
                continue

        # Business type filter
        if filters.business_types:
            if lead.get("business_type") not in filters.business_types:
                continue

        # Tags filter
        if filters.tags:
            lead_tags = lead.get("tags", [])
            if not any(tag in lead_tags for tag in filters.tags):
                continue

        # Status filter
        if filters.statuses:
            if lead.get("status") not in filters.statuses:
                continue

        # Email/phone filters
        if filters.has_emails is not None:
            has_email = bool(lead.get("emails"))
            if has_email != filters.has_emails:
                continue

        if filters.has_phones is not None:
            has_phone = bool(lead.get("phones"))
            if has_phone != filters.has_phones:
                continue

        # Date range filter
        if filters.date_from or filters.date_to:
            lead_date_str = lead.get("when")
            if lead_date_str:
                try:
                    if isinstance(lead_date_str, str):
                        lead_date = datetime.datetime.fromisoformat(lead_date_str.replace('Z', '+00:00'))
                    else:
                        lead_date = lead_date_str

                    if filters.date_from and lead_date < filters.date_from:
                        continue
                    if filters.date_to and lead_date > filters.date_to:
                        continue
                except Exception:
                    pass

        filtered.append(lead)

    return filtered


def select_columns(leads: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Select specific columns from leads"""
    if not columns:
        return leads

    filtered_leads = []
    for lead in leads:
        filtered_lead = {col: lead.get(col) for col in columns if col in lead}
        filtered_leads.append(filtered_lead)

    return filtered_leads


def export_filtered_csv(
    leads: List[Dict[str, Any]],
    filters: ExportFilter,
    project: str = "default",
    filename_prefix: str = "leads"
) -> Tuple[str, int]:
    """
    Export leads to CSV with filtering
    Returns: (file_path, number_of_exported_records)
    """
    # Apply filters
    filtered_leads = apply_filters(leads, filters)

    # Select columns
    if filters.columns:
        filtered_leads = select_columns(filtered_leads, filters.columns)

    if not filtered_leads:
        raise ValueError("No leads match the filter criteria")

    # Create output directory
    out_path = OUT_DIR / project / "leads"
    out_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = out_path / f"{filename_prefix}_{timestamp}.csv"

    # Export to CSV
    headers = sorted({k for lead in filtered_leads for k in lead.keys()})
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for lead in filtered_leads:
            row = {}
            for k, v in lead.items():
                if isinstance(v, (list, dict)):
                    row[k] = json.dumps(v, ensure_ascii=False)
                else:
                    row[k] = v
            writer.writerow(row)

    return str(filename), len(filtered_leads)


def export_filtered_json(
    leads: List[Dict[str, Any]],
    filters: ExportFilter,
    project: str = "default",
    filename_prefix: str = "leads"
) -> Tuple[str, int]:
    """
    Export leads to JSON with filtering
    Returns: (file_path, number_of_exported_records)
    """
    # Apply filters
    filtered_leads = apply_filters(leads, filters)

    # Select columns
    if filters.columns:
        filtered_leads = select_columns(filtered_leads, filters.columns)

    if not filtered_leads:
        raise ValueError("No leads match the filter criteria")

    # Create output directory
    out_path = OUT_DIR / project / "leads"
    out_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = out_path / f"{filename_prefix}_{timestamp}.json"

    # Export to JSON
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(filtered_leads, f, ensure_ascii=False, indent=2)

    return str(filename), len(filtered_leads)


def export_filtered_xlsx(
    leads: List[Dict[str, Any]],
    filters: ExportFilter,
    project: str = "default",
    filename_prefix: str = "leads"
) -> Tuple[str, int]:
    """
    Export leads to XLSX with filtering
    Returns: (file_path, number_of_exported_records)
    """
    # Apply filters
    filtered_leads = apply_filters(leads, filters)

    # Select columns
    if filters.columns:
        filtered_leads = select_columns(filtered_leads, filters.columns)

    if not filtered_leads:
        raise ValueError("No leads match the filter criteria")

    # Create output directory
    out_path = OUT_DIR / project / "leads"
    out_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = out_path / f"{filename_prefix}_{timestamp}.xlsx"

    # Convert to DataFrame and export
    df = pd.DataFrame(filtered_leads)

    # Flatten nested structures for Excel
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x)

    df.to_excel(filename, index=False, engine='openpyxl')

    return str(filename), len(filtered_leads)


def export_filtered_markdown(
    leads: List[Dict[str, Any]],
    filters: ExportFilter,
    project: str = "default",
    filename_prefix: str = "leads"
) -> Tuple[str, int]:
    """
    Export leads to Markdown with filtering
    Returns: (file_path, number_of_exported_records)
    """
    # Apply filters
    filtered_leads = apply_filters(leads, filters)

    # Select columns
    if filters.columns:
        filtered_leads = select_columns(filtered_leads, filters.columns)

    if not filtered_leads:
        raise ValueError("No leads match the filter criteria")

    # Create output directory
    out_path = OUT_DIR / project / "leads"
    out_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = out_path / f"{filename_prefix}_{timestamp}.md"

    # Build markdown
    md_content = f"# Leads Export\n\n"
    md_content += f"**Generated:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    md_content += f"**Total Leads:** {len(filtered_leads)}\n\n"
    md_content += "---\n\n"

    for i, lead in enumerate(filtered_leads, 1):
        md_content += f"## {i}. {lead.get('name', 'Unknown')}\n\n"

        # Basic info
        if lead.get('domain'):
            md_content += f"**Domain:** {lead['domain']}\n\n"
        if lead.get('website'):
            md_content += f"**Website:** [{lead['website']}]({lead['website']})\n\n"

        # Scores
        if 'score_quality' in lead:
            md_content += f"**Quality:** {lead.get('score_quality', 0):.1f}/10 | "
            md_content += f"**Fit:** {lead.get('score_fit', 0):.1f}/10 | "
            md_content += f"**Priority:** {lead.get('score_priority', 0):.1f}/10\n\n"
        elif 'score' in lead:
            md_content += f"**Score:** {lead.get('score', 0):.1f}\n\n"

        # Business type
        if lead.get('business_type'):
            md_content += f"**Business Type:** {lead['business_type']}\n\n"

        # Contact info
        if lead.get('emails'):
            md_content += f"**Emails:** {', '.join(lead['emails'])}\n\n"
        if lead.get('phones'):
            md_content += f"**Phones:** {', '.join(lead['phones'])}\n\n"

        # Location
        if lead.get('city') or lead.get('address'):
            md_content += "**Location:** "
            if lead.get('city'):
                md_content += lead['city']
            if lead.get('address'):
                md_content += f" - {lead['address']}"
            md_content += "\n\n"

        # Tags
        if lead.get('tags'):
            md_content += f"**Tags:** {', '.join(lead['tags'])}\n\n"

        # Status
        if lead.get('status'):
            md_content += f"**Status:** {lead['status']}\n\n"

        # Notes
        if lead.get('notes'):
            md_content += f"**Notes:** {lead['notes']}\n\n"

        md_content += "---\n\n"

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)

    return str(filename), len(filtered_leads)


def create_consulting_pack_zip(
    lead: Dict[str, Any],
    dossier_result: Any = None,
    outreach_result: Any = None,
    audit_result: Any = None,
    project: str = "default"
) -> str:
    """
    Create a complete consulting pack ZIP with all materials
    Returns: path to ZIP file
    """
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    company_slug = lead.get('name', 'unknown').replace(' ', '_').replace('/', '_')

    # Create pack directory
    pack_dir = OUT_DIR / project / f"pack_{company_slug}_{timestamp}"
    pack_dir.mkdir(parents=True, exist_ok=True)

    files_created = []

    # 1. Save lead info
    lead_file = pack_dir / "lead_info.json"
    with open(lead_file, "w", encoding="utf-8") as f:
        json.dump(lead, f, ensure_ascii=False, indent=2)
    files_created.append(lead_file)

    # 2. Save dossier if available
    if dossier_result:
        dossier_md = pack_dir / "dossier.md"
        dossier_content = _format_dossier_markdown(dossier_result)
        with open(dossier_md, "w", encoding="utf-8") as f:
            f.write(dossier_content)
        files_created.append(dossier_md)

        # Also save as JSON
        dossier_json = pack_dir / "dossier.json"
        with open(dossier_json, "w", encoding="utf-8") as f:
            json.dump(dossier_result.dict() if hasattr(dossier_result, 'dict') else dossier_result,
                     f, ensure_ascii=False, indent=2, default=str)
        files_created.append(dossier_json)

    # 3. Save outreach if available
    if outreach_result:
        outreach_md = pack_dir / "outreach_variants.md"
        outreach_content = _format_outreach_markdown(outreach_result)
        with open(outreach_md, "w", encoding="utf-8") as f:
            f.write(outreach_content)
        files_created.append(outreach_md)

        # Save individual variants as separate files
        for i, variant in enumerate(outreach_result.variants, 1):
            variant_file = pack_dir / f"outreach_variant_{i}_{variant.angle}.txt"
            variant_content = ""
            if hasattr(variant, 'subject') and variant.subject:
                variant_content += f"Subject: {variant.subject}\n\n"
            variant_content += variant.body
            if hasattr(variant, 'cta') and variant.cta:
                variant_content += f"\n\nCTA: {variant.cta}"

            with open(variant_file, "w", encoding="utf-8") as f:
                f.write(variant_content)
            files_created.append(variant_file)

    # 4. Save audit if available
    if audit_result:
        audit_md = pack_dir / "audit_report.md"
        audit_content = _format_audit_markdown(audit_result)
        with open(audit_md, "w", encoding="utf-8") as f:
            f.write(audit_content)
        files_created.append(audit_md)

        # Save audit findings as CSV
        if hasattr(audit_result, 'audits') and audit_result.audits:
            audit_csv = pack_dir / "audit_findings.csv"
            _export_audit_csv(audit_result.audits, audit_csv)
            files_created.append(audit_csv)

    # 5. Create summary
    summary = {
        "company_name": lead.get('name', 'Unknown'),
        "domain": lead.get('domain'),
        "website": lead.get('website'),
        "export_date": datetime.datetime.utcnow().isoformat(),
        "included_materials": {
            "lead_info": True,
            "dossier": dossier_result is not None,
            "outreach": outreach_result is not None,
            "audit": audit_result is not None
        },
        "files_count": len(files_created)
    }

    summary_file = pack_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    files_created.append(summary_file)

    # 6. Create ZIP archive
    zip_path = pack_dir.parent / f"{pack_dir.name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_created:
            if file.is_file():
                zipf.write(file, arcname=file.name)

    return str(zip_path)


def _format_dossier_markdown(dossier) -> str:
    """Format dossier as markdown"""
    md = f"# Client Dossier: {dossier.company_name}\n\n"
    md += f"**Website:** {dossier.website}\n\n"
    md += f"**Pages Analyzed:** {dossier.pages_analyzed}\n\n"

    md += f"## Company Overview\n\n{dossier.company_overview}\n\n"

    md += f"## Services & Products\n\n"
    for item in dossier.services_products:
        md += f"- {item}\n"
    md += "\n"

    md += f"## Digital Presence\n\n"
    md += f"**Website Quality:** {dossier.digital_presence.website_quality}\n\n"
    if dossier.digital_presence.social_platforms:
        md += "**Social Platforms:**\n"
        for platform in dossier.digital_presence.social_platforms:
            md += f"- {platform}\n"
        md += "\n"

    if dossier.signals:
        md += f"## Signals\n\n"
        if dossier.signals.positive:
            md += "**Positive Signals:**\n"
            for sig in dossier.signals.positive:
                md += f"- {sig}\n"
            md += "\n"
        if dossier.signals.growth:
            md += "**Growth Signals:**\n"
            for sig in dossier.signals.growth:
                md += f"- {sig}\n"
            md += "\n"
        if dossier.signals.pain:
            md += "**Pain Signals:**\n"
            for sig in dossier.signals.pain:
                md += f"- {sig}\n"
            md += "\n"

    if dossier.issues:
        md += f"## Issues Detected\n\n"
        for issue in dossier.issues:
            md += f"- **[{issue.severity.upper()}] {issue.category}:** {issue.description}\n"
            md += f"  - Source: {issue.source}\n"
        md += "\n"

    if dossier.quick_wins:
        md += f"## 48-Hour Quick Wins\n\n"
        for i, qw in enumerate(dossier.quick_wins, 1):
            md += f"### {i}. {qw.title}\n\n"
            md += f"**Action:** {qw.action}\n\n"
            md += f"**Impact:** {qw.impact} | **Effort:** {qw.effort} | **Priority:** {qw.priority:.1f}/10\n\n"

    md += f"## Sources\n\n"
    for i, source in enumerate(dossier.sources, 1):
        md += f"{i}. {source}\n"

    return md


def _format_outreach_markdown(outreach) -> str:
    """Format outreach as markdown"""
    md = f"# Outreach Variants: {outreach.company_name}\n\n"
    md += f"**Type:** {outreach.message_type} | **Language:** {outreach.language} | **Tone:** {outreach.tone}\n\n"

    for i, variant in enumerate(outreach.variants, 1):
        md += f"## Variant {i}: {variant.angle.title()}\n\n"
        if hasattr(variant, 'subject') and variant.subject:
            md += f"**Subject:** {variant.subject}\n\n"
        md += f"**Message:**\n\n{variant.body}\n\n"
        if hasattr(variant, 'cta') and variant.cta:
            md += f"**CTA:** {variant.cta}\n\n"
        md += f"**Deliverability Score:** {variant.deliverability_score}/100\n\n"
        if variant.deliverability_issues:
            md += "**Deliverability Issues:**\n"
            for issue in variant.deliverability_issues:
                md += f"- {issue}\n"
            md += "\n"
        md += "---\n\n"

    return md


def _format_audit_markdown(audit_result) -> str:
    """Format audit as markdown"""
    md = f"# Audit Report: {audit_result.domain}\n\n"
    md += f"**Crawled:** {len(audit_result.crawled_urls)} pages | **Audited:** {len(audit_result.audits)} pages\n\n"

    for i, audit in enumerate(audit_result.audits, 1):
        md += f"## Page {i}: {audit.url}\n\n"
        md += f"**Score:** {audit.score}/100 | **Grade:** {audit.grade}\n\n"
        md += f"- Content: {audit.content_score}/100\n"
        md += f"- Technical: {audit.technical_score}/100\n"
        md += f"- SEO: {audit.seo_score}/100\n\n"

        if audit.issues:
            md += "**Issues:**\n"
            for issue in audit.issues:
                md += f"- [{issue.severity.upper()}] {issue.description}\n"
            md += "\n"

        if audit.strengths:
            md += "**Strengths:**\n"
            for strength in audit.strengths:
                md += f"- {strength}\n"
            md += "\n"

    if hasattr(audit_result, 'quick_wins') and audit_result.quick_wins:
        md += f"## Top Quick Wins\n\n"
        for i, task in enumerate(audit_result.quick_wins, 1):
            md += f"### {i}. {task.task.title}\n\n"
            md += f"**Action:** {task.task.action}\n\n"
            md += f"**Expected Impact:** {task.task.impact}\n\n"
            md += f"**Impact Score:** {task.impact:.1f}/10 | **Feasibility:** {task.feasibility:.1f}/10 | **Priority:** {task.priority_score:.1f}/10\n\n"

    return md


def _export_audit_csv(audits: List[Any], filepath: Path):
    """Export audit findings to CSV"""
    rows = []
    for audit in audits:
        for issue in audit.issues:
            rows.append({
                "url": audit.url,
                "severity": issue.severity,
                "category": issue.category,
                "description": issue.description,
                "score": audit.score,
                "grade": audit.grade
            })

    if rows:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["url", "severity", "category", "description", "score", "grade"])
            writer.writeheader()
            writer.writerows(rows)


def get_export_preview(
    leads: List[Dict[str, Any]],
    filters: ExportFilter,
    max_preview: int = 5
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Get preview of data to be exported with statistics
    Returns: (preview_leads, statistics)
    """
    # Apply filters
    filtered_leads = apply_filters(leads, filters)

    # Calculate statistics
    stats = {
        "total_filtered": len(filtered_leads),
        "total_original": len(leads),
        "filtered_percentage": (len(filtered_leads) / len(leads) * 100) if leads else 0,
        "has_emails": sum(1 for lead in filtered_leads if lead.get('emails')),
        "has_phones": sum(1 for lead in filtered_leads if lead.get('phones')),
        "avg_score": sum(lead.get('score', 0) for lead in filtered_leads) / len(filtered_leads) if filtered_leads else 0,
    }

    # Add multi-dimensional score averages if available
    quality_scores = [lead.get('score_quality', 0) for lead in filtered_leads if 'score_quality' in lead]
    if quality_scores:
        stats["avg_quality"] = sum(quality_scores) / len(quality_scores)

    fit_scores = [lead.get('score_fit', 0) for lead in filtered_leads if 'score_fit' in lead]
    if fit_scores:
        stats["avg_fit"] = sum(fit_scores) / len(fit_scores)

    priority_scores = [lead.get('score_priority', 0) for lead in filtered_leads if 'score_priority' in lead]
    if priority_scores:
        stats["avg_priority"] = sum(priority_scores) / len(priority_scores)

    # Business type distribution
    if filtered_leads and 'business_type' in filtered_leads[0]:
        business_types = {}
        for lead in filtered_leads:
            bt = lead.get('business_type', 'Unknown')
            business_types[bt] = business_types.get(bt, 0) + 1
        stats["business_type_distribution"] = business_types

    # Get preview (first N leads)
    preview = filtered_leads[:max_preview]

    return preview, stats

"""
Quick wins generator
Converts audit issues into prioritized tasks with impact × effort scoring
"""

from typing import List, Dict
from dataclasses import dataclass
from audit.page_audit import PageAudit, QuickWinTask, AuditIssue


@dataclass
class PrioritizedTask:
    """Task with priority scoring"""
    task: QuickWinTask
    priority_score: float  # Impact × Feasibility (0-10)
    impact: int  # 1-10
    feasibility: int  # 1-10


def estimate_impact(issue: AuditIssue) -> int:
    """
    Estimate impact of fixing an issue (1-10 scale)

    Args:
        issue: AuditIssue to evaluate

    Returns:
        Impact score (1-10)
    """
    impact_map = {
        'critical': 10,
        'high': 8,
        'medium': 5,
        'low': 3
    }

    base_impact = impact_map.get(issue.severity, 5)

    # Category multipliers
    category_multipliers = {
        'technical': 1.2,  # Technical issues often have high impact
        'seo': 1.1,
        'meta': 1.0,
        'content': 0.9,
        'images': 0.8,
        'links': 0.8,
        'headings': 0.9
    }

    multiplier = category_multipliers.get(issue.category, 1.0)

    return min(10, int(base_impact * multiplier))


def estimate_effort(task_effort_str: str) -> tuple[int, int]:
    """
    Estimate effort and convert to feasibility score

    Args:
        task_effort_str: Effort string (e.g., "5 mins", "1 hour")

    Returns:
        Tuple of (minutes, feasibility_score 1-10)
    """
    effort_lower = task_effort_str.lower()

    # Parse effort in minutes
    if 'min' in effort_lower:
        try:
            minutes = int(''.join(filter(str.isdigit, effort_lower)))
        except:
            minutes = 30
    elif 'hour' in effort_lower:
        try:
            hours = int(''.join(filter(str.isdigit, effort_lower)))
            minutes = hours * 60
        except:
            minutes = 60
    elif 'day' in effort_lower:
        minutes = 480  # 1 day = 8 hours
    else:
        minutes = 30  # Default

    # Convert to feasibility (higher score = easier/faster)
    if minutes <= 5:
        feasibility = 10
    elif minutes <= 15:
        feasibility = 9
    elif minutes <= 30:
        feasibility = 8
    elif minutes <= 60:
        feasibility = 6
    elif minutes <= 120:
        feasibility = 4
    else:
        feasibility = 2

    return minutes, feasibility


def convert_issue_to_task(issue: AuditIssue) -> QuickWinTask:
    """
    Convert AuditIssue to QuickWinTask

    Args:
        issue: AuditIssue to convert

    Returns:
        QuickWinTask
    """
    # Estimate effort based on severity and category
    effort_map = {
        'critical': '1 hour',
        'high': '30 mins',
        'medium': '15 mins',
        'low': '5 mins'
    }

    effort = effort_map.get(issue.severity, '15 mins')

    # Estimate impact description
    impact_descriptions = {
        'critical': 'High - Immediate improvement to security/functionality',
        'high': 'Significant - Noticeable improvement in user experience',
        'medium': 'Moderate - Incremental improvement',
        'low': 'Minor - Small enhancement'
    }

    impact_desc = impact_descriptions.get(issue.severity, 'Moderate improvement')

    return QuickWinTask(
        title=issue.title,
        action=issue.recommendation,
        impact=impact_desc,
        effort=effort
    )


def generate_quick_wins(
    audit: PageAudit,
    max_wins: int = 8,
    include_llm_wins: bool = True
) -> List[PrioritizedTask]:
    """
    Generate prioritized quick wins from audit

    Args:
        audit: PageAudit result
        max_wins: Maximum number of wins to return
        include_llm_wins: Whether to include LLM-generated quick wins

    Returns:
        List of PrioritizedTask, sorted by priority
    """
    tasks = []

    # Add LLM-generated quick wins (already prioritized)
    if include_llm_wins and audit.quick_wins:
        for i, qw in enumerate(audit.quick_wins):
            minutes, feasibility = estimate_effort(qw.effort)

            # LLM wins get bonus impact since they're curated
            impact = 8 + (max_wins - i)  # First wins get higher scores

            priority_score = (impact * feasibility) / 10.0

            tasks.append(PrioritizedTask(
                task=qw,
                priority_score=priority_score,
                impact=impact,
                feasibility=feasibility
            ))

    # Convert audit issues to tasks
    for issue in audit.issues:
        task = convert_issue_to_task(issue)

        impact = estimate_impact(issue)
        minutes, feasibility = estimate_effort(task.effort)

        priority_score = (impact * feasibility) / 10.0

        tasks.append(PrioritizedTask(
            task=task,
            priority_score=priority_score,
            impact=impact,
            feasibility=feasibility
        ))

    # Sort by priority score (descending)
    tasks.sort(key=lambda x: x.priority_score, reverse=True)

    # Return top N
    return tasks[:max_wins]


def export_quick_wins_markdown(
    tasks: List[PrioritizedTask],
    url: str,
    domain: str
) -> str:
    """
    Export quick wins to markdown format

    Args:
        tasks: List of PrioritizedTask
        url: Page URL
        domain: Domain name

    Returns:
        Markdown string
    """
    md = f"# Quick Wins: {domain}\n\n"
    md += f"**Page**: {url}\n"
    md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    md += "---\n\n"

    md += "## Priority Tasks (Impact × Effort)\n\n"

    for i, task_item in enumerate(tasks, 1):
        task = task_item.task
        md += f"### {i}. {task.title}\n\n"
        md += f"**Action**: {task.action}\n\n"
        md += f"**Expected Impact**: {task.impact}\n\n"
        md += f"**Effort**: {task.effort}\n\n"
        md += f"**Priority Score**: {task_item.priority_score:.1f}/10 "
        md += f"(Impact: {task_item.impact}/10, Feasibility: {task_item.feasibility}/10)\n\n"
        md += "---\n\n"

    return md


from datetime import datetime

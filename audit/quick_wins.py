"""
Quick wins generator
Converts audit issues into prioritized tasks with impact × effort scoring
"""

from typing import List, Dict
from dataclasses import dataclass
from audit.page_audit import PageAudit, QuickWinTask, AuditIssue


@dataclass
class PrioritizedTask:
    """Represents a task that has been prioritized based on impact and feasibility.

    Attributes:
        task (QuickWinTask): The underlying quick win task.
        priority_score (float): The calculated priority score (0-10).
        impact (int): The estimated impact of the task (1-10).
        feasibility (int): The estimated feasibility of the task (1-10).
    """
    task: QuickWinTask
    priority_score: float
    impact: int
    feasibility: int


def estimate_impact(issue: AuditIssue) -> int:
    """Estimate the impact of fixing an audit issue.

    This function assigns an impact score (1-10) based on the issue's severity
    and category, using a predefined mapping and multipliers.

    Args:
        issue (AuditIssue): The audit issue to evaluate.

    Returns:
        int: The estimated impact score.
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
    """Estimate the effort required for a task and convert it to a feasibility score.

    This function parses a human-readable effort string (e.g., "5 mins", "1 hour") and
    converts it into a numerical feasibility score (1-10), where a higher score
    indicates a more feasible (i.e., less effortful) task.

    Args:
        task_effort_str (str): The effort string to estimate.

    Returns:
        tuple[int, int]: A tuple containing the estimated minutes and the feasibility score.
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
    """Convert an AuditIssue into a QuickWinTask.

    This function transforms a detected issue into an actionable task, complete with
    an estimated effort and impact description.

    Args:
        issue (AuditIssue): The audit issue to convert.

    Returns:
        QuickWinTask: The resulting quick win task.
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
    """Generate a list of prioritized quick wins from a page audit.

    This is the main function for generating quick wins. It combines the quick wins
    suggested by the LLM with tasks derived from the audit issues, then prioritizes
    them based on their impact and feasibility.

    Args:
        audit (PageAudit): The result of the page audit.
        max_wins (int): The maximum number of quick wins to return.
        include_llm_wins (bool): If True, include the LLM-generated quick wins.

    Returns:
        List[PrioritizedTask]: A sorted list of the top prioritized tasks.
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
    """Export a list of quick wins to a markdown-formatted string.

    This function creates a human-readable report of the quick wins, which can be
    easily saved to a file or displayed in a UI.

    Args:
        tasks (List[PrioritizedTask]): A list of prioritized tasks.
        url (str): The URL of the audited page.
        domain (str): The domain name of the audited page.

    Returns:
        str: A markdown-formatted string of the quick wins.
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

"""
Outreach module for Lead Hunter Toolkit
Provides personalized outreach generation and deliverability checking
"""

from outreach.compose import compose_outreach, OutreachResult
from outreach.deliverability_checks import check_deliverability, DeliverabilityIssue

__all__ = ['compose_outreach', 'OutreachResult', 'check_deliverability', 'DeliverabilityIssue']

"""
Audit module for Lead Hunter Toolkit
Provides page auditing and quick wins generation
"""

from audit.page_audit import audit_page, PageAudit
from audit.quick_wins import generate_quick_wins, QuickWinTask

__all__ = ['audit_page', 'PageAudit', 'generate_quick_wins', 'QuickWinTask']

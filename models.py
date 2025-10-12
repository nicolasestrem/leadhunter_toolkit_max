from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class Social(BaseModel):
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    youtube: Optional[str] = None

class Lead(BaseModel):
    """Lead data model for business contact information"""
    name: Optional[str] = None
    domain: Optional[str] = None
    website: Optional[str] = None
    source_url: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    social: Social = Field(default_factory=Social)
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: str = "new"  # new, contacted, qualified, rejected
    score: float = 0.0
    notes: Optional[str] = None
    when: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config to allow dict compatibility"""
        from_attributes = True
        arbitrary_types_allowed = True


class LeadRecord(BaseModel):
    """
    Enhanced lead data model for consulting pack
    Includes classification, multi-dimensional scoring, and quality signals
    """
    # Basic information (inherited from Lead)
    name: Optional[str] = None
    domain: Optional[str] = None
    website: Optional[str] = None
    source_url: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    social: Social = Field(default_factory=Social)
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: str = "new"  # new, contacted, qualified, rejected
    notes: Optional[str] = None
    when: datetime = Field(default_factory=datetime.utcnow)

    # Legacy score (for backward compatibility)
    score: float = 0.0

    # Enhanced scoring (consulting pack)
    score_quality: float = 0.0  # Data completeness score (0-10)
    score_fit: float = 0.0      # SMB fit score (0-10)
    score_priority: float = 0.0 # Overall priority score (0-10)

    # Classification
    business_type: Optional[str] = None  # restaurant, retail, tech, etc.

    # Issue flags (technical/content problems)
    issue_flags: List[str] = Field(default_factory=list)
    # Examples: "No SSL", "Thin content", "Poor mobile", etc.

    # Quality signals (positive indicators)
    quality_signals: List[str] = Field(default_factory=list)
    # Examples: "Complete contact", "Professional design", "Social active", etc.

    # Content sample for LLM analysis
    content_sample: Optional[str] = None

    class Config:
        """Pydantic config to allow dict compatibility"""
        from_attributes = True
        arbitrary_types_allowed = True

    @classmethod
    def from_lead(cls, lead: Lead) -> 'LeadRecord':
        """Create LeadRecord from existing Lead"""
        return cls(
            name=lead.name,
            domain=lead.domain,
            website=lead.website,
            source_url=lead.source_url,
            emails=lead.emails,
            phones=lead.phones,
            social=lead.social,
            address=lead.address,
            city=lead.city,
            country=lead.country,
            tags=lead.tags,
            status=lead.status,
            score=lead.score,
            notes=lead.notes,
            when=lead.when
        )

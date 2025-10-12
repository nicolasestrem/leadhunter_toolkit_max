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

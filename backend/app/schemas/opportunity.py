import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OpportunityCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    topic_id: Optional[uuid.UUID] = None
    summary: Optional[str] = None
    status: str = Field(default="draft", description="draft, approved, rejected, archived")
    score: Optional[Decimal] = None


class OpportunityUpdateRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    score: Optional[Decimal] = None


class OpportunityResponseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    topic_id: Optional[uuid.UUID] = None
    title: str
    summary: Optional[str] = None
    status: str
    score: Optional[Decimal] = None
    evidence: Optional[Dict[str, Any]] = None
    limitations: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class OpportunityBriefGenerateResponseData(BaseModel):
    opportunity_id: uuid.UUID
    title: str
    signal_summary: str
    evidence_coverage: Dict[str, Any]
    audience_hypotheses: List[Dict[str, Any]]
    product_angles: List[str]
    campaign_experiments: List[Dict[str, Any]]
    risks_counter_signals: List[str]
    confidence_limitations: Dict[str, Any]
    asci_disclosure_reminder: str
    verified_citations: List[str]
    flagged_unverified_citations: List[str]
    generated_at: str

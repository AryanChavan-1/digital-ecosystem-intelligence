import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class TrendListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: uuid.UUID
    canonical_label: str
    period_start: date
    period_end: date
    mention_count: int
    previous_mention_count: int
    change_pct: Optional[Decimal] = None
    momentum_score: Decimal
    source_count: int
    confidence: str
    confidence_badge: str
    is_cold_start: bool
    generated_at: datetime


class TrendDetailResponseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: uuid.UUID
    canonical_label: str
    description: Optional[str] = None
    plain_language_summary: str
    confidence: str
    confidence_badge: str
    momentum_score: Decimal
    change_pct: Optional[Decimal] = None
    mention_count: int
    previous_mention_count: int
    source_count: int
    is_cold_start: bool
    period_start: date
    period_end: date
    timeline_series: List[Dict[str, Any]]
    source_coverage_breakdown: List[Dict[str, Any]]
    related_topics: List[Dict[str, Any]]
    associated_audiences: List[Dict[str, Any]]
    evidence_snippets: List[Dict[str, Any]]

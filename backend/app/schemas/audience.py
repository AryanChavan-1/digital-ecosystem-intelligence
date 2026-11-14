import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AudienceTopicItem(BaseModel):
    topic_id: uuid.UUID
    canonical_label: str
    weight: Decimal


class AudienceClusterResponseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: Optional[str] = None
    record_count: int
    quality_score: Optional[Decimal] = None
    is_user_renamed: bool
    label_locked: bool
    top_topics: List[AudienceTopicItem]
    created_at: datetime


class AudienceClusterUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Updated cluster name")

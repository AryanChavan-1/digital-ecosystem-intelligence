import uuid
from typing import Optional

from pydantic import BaseModel, Field


class WorkspaceSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    industry: Optional[str] = None
    market_region: str = "IN"
    default_language: str = "en"


class WorkspaceMembershipResponse(BaseModel):
    workspace_id: uuid.UUID
    name: str
    role: str
    status: str = "active"
    industry: Optional[str] = None
    market_region: str = "IN"
    default_language: str = "en"


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    industry: Optional[str] = Field(default=None, max_length=100)
    market_region: Optional[str] = Field(default=None, max_length=50)
    default_language: Optional[str] = Field(default=None, max_length=20)


class WorkspaceSeedDemoRequest(BaseModel):
    industry: Optional[str] = "Sustainable Fashion & D2C Apparel"


class WorkspaceSeedDemoResponse(BaseModel):
    workspace_id: uuid.UUID
    topics_seeded: int
    trends_seeded: int
    audiences_seeded: int
    sources_seeded: int
    message: str = "Demo workspace intelligence seeded successfully."


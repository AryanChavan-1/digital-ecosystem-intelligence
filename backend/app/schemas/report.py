import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReportResponseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    opportunity_id: Optional[uuid.UUID] = None
    created_by: Optional[uuid.UUID] = None
    object_key: str
    format: str
    status: str
    generated_at: datetime

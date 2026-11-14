import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DataSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: Optional[uuid.UUID] = None
    provider: str
    source_type: str
    display_name: str
    permission_status: str
    refresh_mode: str
    status: str
    last_success_at: Optional[datetime] = None
    created_at: datetime

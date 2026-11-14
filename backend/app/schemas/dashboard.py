from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.trend import TrendListItem


class DashboardSummaryResponseData(BaseModel):
    tracked_topics_count: int
    rising_topics_count: int
    saved_opportunities_count: int
    connected_sources_count: int
    top_rising_trends: List[TrendListItem]
    latest_freshness_timestamp: Optional[datetime] = None

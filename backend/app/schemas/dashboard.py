from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, computed_field

from app.schemas.trend import TrendListItem


class DashboardSummaryResponseData(BaseModel):
    tracked_topics_count: int
    rising_topics_count: int
    saved_opportunities_count: int
    connected_sources_count: int
    top_rising_trends: List[TrendListItem]
    latest_freshness_timestamp: Optional[datetime] = None

    @computed_field
    @property
    def tracked_topics(self) -> int:
        return self.tracked_topics_count

    @computed_field
    @property
    def rising_topics(self) -> int:
        return self.rising_topics_count

    @computed_field
    @property
    def saved_opportunities(self) -> int:
        return self.saved_opportunities_count

    @computed_field
    @property
    def connected_sources(self) -> int:
        return self.connected_sources_count

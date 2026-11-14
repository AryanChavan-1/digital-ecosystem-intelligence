import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CampaignResponseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    external_campaign_id: Optional[str] = None
    name: str
    channel: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currency: str = "INR"
    created_at: datetime


class CampaignDailyMetricItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    local_date: date
    impressions: int
    clicks: int
    spend: Decimal
    conversions: Decimal
    attributed_revenue: Decimal
    creative_label: Optional[str] = None
    audience_label: Optional[str] = None
    ctr: Optional[Decimal] = None
    cpc: Optional[Decimal] = None
    cpm: Optional[Decimal] = None
    cpa: Optional[Decimal] = None
    roas: Optional[Decimal] = None


class CampaignSummaryTotals(BaseModel):
    impressions: int
    clicks: int
    spend: Decimal
    conversions: Decimal
    attributed_revenue: Decimal
    currency: str
    ctr: Optional[Decimal] = None
    cpc: Optional[Decimal] = None
    cpm: Optional[Decimal] = None
    cpa: Optional[Decimal] = None
    roas: Optional[Decimal] = None


class CampaignSummaryResponseData(BaseModel):
    campaign: CampaignResponseData
    totals: CampaignSummaryTotals
    daily_metrics: List[CampaignDailyMetricItem]

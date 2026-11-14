import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_workspace, get_db, get_request_id
from app.core.errors import NotFoundException, TenantAccessDeniedException
from app.models.campaign import Campaign, CampaignDailyMetric
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.campaign import (
    CampaignDailyMetricItem,
    CampaignResponseData,
    CampaignSummaryResponseData,
    CampaignSummaryTotals,
)
from app.schemas.envelope import EnvelopeResponse, ResponseMeta
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get(
    "",
    response_model=EnvelopeResponse[List[CampaignResponseData]],
    status_code=status.HTTP_200_OK,
    summary="List campaigns in the active workspace",
)
async def list_campaigns(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    channel: Optional[str] = Query(default=None),
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[List[CampaignResponseData]]:
    """
    Paginated list of campaigns strictly scoped to the active workspace.
    Supports optional channel filter.
    """
    workspace, _ = workspace_and_role

    stmt = select(Campaign).where(Campaign.workspace_id == workspace.id)
    if channel:
        stmt = stmt.where(Campaign.channel == channel)

    stmt = stmt.order_by(Campaign.created_at.desc()).offset(offset).limit(limit)

    res = await db.execute(stmt)
    campaigns = res.scalars().all()

    data = [CampaignResponseData.model_validate(c) for c in campaigns]
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)


@router.get(
    "/{campaign_id}/summary",
    response_model=EnvelopeResponse[CampaignSummaryResponseData],
    status_code=status.HTTP_200_OK,
    summary="Get campaign performance summary and daily KPI metrics",
)
async def get_campaign_summary(
    campaign_id: uuid.UUID,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[CampaignSummaryResponseData]:
    """
    Calculate aggregated totals and computed CTR, CPC, CPM, CPA, ROAS
    (with strict zero/null-denominator guards returning null, never 0 or infinity),
    along with daily time-series breakdown sorted by local_date.
    """
    workspace, _ = workspace_and_role

    # Query campaign with metrics
    stmt = (
        select(Campaign)
        .options(selectinload(Campaign.metrics))
        .where(Campaign.id == campaign_id)
    )
    res = await db.execute(stmt)
    campaign = res.scalar_one_or_none()

    if not campaign:
        raise NotFoundException(message=f"Campaign {campaign_id} not found.")

    if campaign.workspace_id != workspace.id:
        raise TenantAccessDeniedException(
            message="Campaign does not belong to active workspace."
        )

    # Sort metrics by local_date
    metrics: List[CampaignDailyMetric] = sorted(
        campaign.metrics, key=lambda m: m.local_date
    )

    totals_dict, daily_series = CampaignService.aggregate_metrics(
        metric_items=metrics,
        target_currency=campaign.currency,
    )

    campaign_data = CampaignResponseData.model_validate(campaign)
    totals_data = CampaignSummaryTotals.model_validate(totals_dict)
    daily_metrics_data = [
        CampaignDailyMetricItem.model_validate(item) for item in daily_series
    ]

    response_data = CampaignSummaryResponseData(
        campaign=campaign_data,
        totals=totals_data,
        daily_metrics=daily_metrics_data,
    )
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=response_data, meta=meta)

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_workspace, get_db, get_request_id
from app.models.opportunity import Opportunity
from app.models.source import DataSource
from app.models.topic import Topic
from app.models.trend import TrendSnapshot
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.dashboard import DashboardSummaryResponseData
from app.schemas.envelope import EnvelopeResponse, ResponseMeta
from app.schemas.trend import TrendListItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=EnvelopeResponse[DashboardSummaryResponseData],
    status_code=status.HTTP_200_OK,
    summary="Get workspace dashboard summary and key intelligence metrics",
)
async def get_dashboard_summary(
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[DashboardSummaryResponseData]:
    """
    Returns:
    - tracked_topics_count
    - rising_topics_count (momentum_score > 0)
    - saved_opportunities_count
    - connected_sources_count
    - top_rising_trends
    - latest_freshness_timestamp
    """
    workspace, _ = workspace_and_role

    # 1. Tracked topics count (workspace-specific or global)
    topic_stmt = select(func.count(Topic.id)).where(
        or_(Topic.workspace_id == workspace.id, Topic.workspace_id.is_(None))
    )
    topic_res = await db.execute(topic_stmt)
    tracked_topics_count = topic_res.scalar() or 0

    # 2. Rising topics count (momentum_score > 0)
    rising_stmt = select(func.count(TrendSnapshot.id)).where(
        or_(
            TrendSnapshot.workspace_id == workspace.id,
            TrendSnapshot.workspace_id.is_(None),
        ),
        TrendSnapshot.momentum_score > 0,
    )
    rising_res = await db.execute(rising_stmt)
    rising_topics_count = rising_res.scalar() or 0

    # 3. Saved opportunities count
    opp_stmt = select(func.count(Opportunity.id)).where(
        Opportunity.workspace_id == workspace.id
    )
    opp_res = await db.execute(opp_stmt)
    saved_opportunities_count = opp_res.scalar() or 0

    # 4. Connected sources count
    source_stmt = select(func.count(DataSource.id)).where(
        DataSource.workspace_id == workspace.id
    )
    source_res = await db.execute(source_stmt)
    connected_sources_count = source_res.scalar() or 0

    # 5. Top rising trends
    trends_stmt = (
        select(TrendSnapshot)
        .options(selectinload(TrendSnapshot.topic))
        .where(
            or_(
                TrendSnapshot.workspace_id == workspace.id,
                TrendSnapshot.workspace_id.is_(None),
            )
        )
        .order_by(TrendSnapshot.momentum_score.desc())
        .limit(5)
    )
    trends_res = await db.execute(trends_stmt)
    top_snapshots = trends_res.scalars().all()

    top_rising_trends: List[TrendListItem] = []
    latest_freshness: datetime | None = None

    for snap in top_snapshots:
        if latest_freshness is None or snap.generated_at > latest_freshness:
            latest_freshness = snap.generated_at

        badge = "high" if snap.confidence == "high" else ("medium" if snap.confidence == "medium" else "low")
        is_cold = snap.source_count <= 1 or snap.previous_mention_count == 0

        top_rising_trends.append(
            TrendListItem(
                id=snap.id,
                topic_id=snap.topic_id,
                canonical_label=snap.topic.canonical_label if snap.topic else "Unknown Topic",
                period_start=snap.period_start,
                period_end=snap.period_end,
                mention_count=snap.mention_count,
                previous_mention_count=snap.previous_mention_count,
                change_pct=snap.change_pct,
                momentum_score=snap.momentum_score,
                source_count=snap.source_count,
                confidence=snap.confidence,
                confidence_badge=badge,
                is_cold_start=is_cold,
                generated_at=snap.generated_at,
            )
        )

    if latest_freshness is None:
        latest_freshness = datetime.now(timezone.utc)

    data = DashboardSummaryResponseData(
        tracked_topics_count=tracked_topics_count,
        rising_topics_count=rising_topics_count,
        saved_opportunities_count=saved_opportunities_count,
        connected_sources_count=connected_sources_count,
        top_rising_trends=top_rising_trends,
        latest_freshness_timestamp=latest_freshness,
    )
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_current_workspace,
    get_db,
    get_request_id,
)
from app.core.errors import ForbiddenException, TenantAccessDeniedException
from app.models.audience import AudienceCluster
from app.models.audit import AuditEvent
from app.models.campaign import Campaign, CampaignDailyMetric
from app.models.job import BackgroundJob
from app.models.record import SourceRecord
from app.models.source import DataSource
from app.models.topic import Topic, TopicRecordAssignment
from app.models.trend import TrendSnapshot
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.envelope import EnvelopeResponse, ResponseMeta
from app.schemas.workspace import (
    WorkspaceMembershipResponse,
    WorkspaceSeedDemoRequest,
    WorkspaceSeedDemoResponse,
    WorkspaceSummaryResponse,
    WorkspaceUpdateRequest,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get(
    "",
    response_model=EnvelopeResponse[List[WorkspaceMembershipResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_workspaces(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[List[WorkspaceMembershipResponse]]:
    """List all workspaces the authenticated user belongs to."""
    stmt = (
        select(WorkspaceMember, Workspace)
        .join(Workspace, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.status == "active",
        )
    )
    res = await db.execute(stmt)
    rows = res.all()

    workspaces = [
        WorkspaceMembershipResponse(
            workspace_id=ws.id,
            name=ws.name,
            role=wm.role,
            status=wm.status,
            industry=ws.industry,
            market_region=ws.market_region,
            default_language=ws.default_language,
        )
        for wm, ws in rows
    ]

    req_id = get_request_id(request)
    return EnvelopeResponse(
        data=workspaces,
        meta=ResponseMeta(request_id=req_id),
    )


@router.patch(
    "/{workspace_id}",
    response_model=EnvelopeResponse[WorkspaceSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def update_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[WorkspaceSummaryResponse]:
    """
    Update workspace metadata (industry, market_region, default_language, name).
    Enforces strict tenant isolation: user must have active membership with owner or admin role.
    Returns 403 TENANT_ACCESS_DENIED if user does not belong to this workspace.
    """
    # Verify tenant isolation via workspace_members
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
        WorkspaceMember.status == "active",
    )
    membership = await db.scalar(stmt)

    if not membership:
        raise TenantAccessDeniedException(
            code="TENANT_ACCESS_DENIED",
            message="Resource does not belong to active workspace.",
        )

    # Check permission level
    if membership.role not in ("owner", "admin"):
        raise ForbiddenException(
            code="FORBIDDEN",
            message="Only workspace owners or admins can update workspace settings.",
        )

    # Fetch workspace
    workspace = await db.scalar(select(Workspace).where(Workspace.id == workspace_id))
    if not workspace:
        raise TenantAccessDeniedException(
            code="TENANT_ACCESS_DENIED",
            message="Resource does not belong to active workspace.",
        )

    # Apply updates
    if payload.name is not None:
        workspace.name = payload.name.strip()
    if payload.industry is not None:
        workspace.industry = payload.industry.strip()
    if payload.market_region is not None:
        workspace.market_region = payload.market_region.strip()
    if payload.default_language is not None:
        workspace.default_language = payload.default_language.strip()

    audit = AuditEvent(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="workspace.update",
        resource_type="workspace",
        resource_id=workspace.id,
        metadata_json=payload.model_dump(exclude_unset=True),
    )
    db.add(audit)

    await db.commit()
    await db.refresh(workspace)

    req_id = get_request_id(request)
    return EnvelopeResponse(
        data=WorkspaceSummaryResponse(
            id=workspace.id,
            name=workspace.name,
            role=membership.role,
            industry=workspace.industry,
            market_region=workspace.market_region,
            default_language=workspace.default_language,
        ),
        meta=ResponseMeta(request_id=req_id),
    )


@router.post(
    "/{workspace_id}/seed-demo",
    response_model=EnvelopeResponse[WorkspaceSeedDemoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Seed demo Indian D2C intelligence data for workspace",
)
async def seed_demo_workspace(
    workspace_id: uuid.UUID,
    payload: Optional[WorkspaceSeedDemoRequest] = None,
    request: Request = None,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[WorkspaceSeedDemoResponse]:
    """
    Seed realistic Indian D2C sample data (topics, trend snapshots, source records,
    audience clusters, campaigns) for the authenticated workspace.
    Protected by get_current_user and get_current_workspace tenant boundary.
    """
    workspace, role = workspace_and_role
    if workspace.id != workspace_id:
        raise TenantAccessDeniedException(
            code="TENANT_ACCESS_DENIED",
            message="Resource does not belong to active workspace.",
        )

    now = datetime.now(timezone.utc)
    today = now.date()
    industry = payload.industry if payload and payload.industry else (workspace.industry or "Sustainable Fashion & D2C Apparel")

    # 1. Ensure a demo data source exists
    source_stmt = select(DataSource).where(
        DataSource.workspace_id == workspace.id,
        DataSource.display_name == "Meta & Social Commerce Export - Festive IN",
    )
    data_source = await db.scalar(source_stmt)
    sources_seeded = 0
    if not data_source:
        data_source = DataSource(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            provider="meta_ads",
            source_type="csv_upload",
            display_name="Meta & Social Commerce Export - Festive IN",
            permission_status="permitted",
            refresh_mode="manual",
            status="active",
            last_success_at=now,
        )
        db.add(data_source)
        await db.flush()
        sources_seeded += 1

    # 2. Seed Topics & Trends
    topics_catalog = [
        ("Organic Bamboo Linen", "Sustainable Fashion", "high", 84.5, 1420, 890, 59.55, 3),
        ("Ayurvedic Niacinamide Serum", "Clean Beauty", "high", 78.2, 2100, 1350, 55.56, 4),
        ("Kombucha Gut Health Fizz", "Food & Beverage", "medium", 62.1, 830, 610, 36.07, 2),
        ("Cold-Pressed Mustard Oil", "Food & Beverage", "low", 38.4, 310, 290, 6.90, 1),
    ]

    topics_seeded = 0
    trends_seeded = 0

    for name, category, confidence, momentum, mentions, prev_mentions, change_pct, src_count in topics_catalog:
        topic_stmt = select(Topic).where(
            Topic.workspace_id == workspace.id,
            Topic.canonical_label == name,
        )
        topic = await db.scalar(topic_stmt)
        if not topic:
            topic = Topic(
                id=uuid.uuid4(),
                workspace_id=workspace.id,
                canonical_label=name,
                description=f"Trending {category.lower()} category in India",
                status="active",
            )
            db.add(topic)
            await db.flush()
            topics_seeded += 1

            # Seed TrendSnapshot
            trend = TrendSnapshot(
                id=uuid.uuid4(),
                workspace_id=workspace.id,
                topic_id=topic.id,
                period_start=today - timedelta(days=30),
                period_end=today,
                mention_count=mentions,
                previous_mention_count=prev_mentions,
                change_pct=Decimal(str(change_pct)),
                momentum_score=Decimal(str(momentum)),
                source_count=src_count,
                confidence=confidence,
                feature_version="v1.0",
                model_version="momentum-v1",
                generated_at=now,
            )
            db.add(trend)
            trends_seeded += 1

            # Seed SourceRecord & TopicRecordAssignment
            snippet_text = f"Top-selling Indian D2C brands report sustained demand surge for {name.lower()} across Mumbai, Bengaluru, and Delhi-NCR festive collections."
            record = SourceRecord(
                id=uuid.uuid4(),
                workspace_id=workspace.id,
                source_id=data_source.id,
                source_type="instagram_caption" if "Fashion" in category else "ecom_review",
                external_record_id=f"demo_rec_{str(uuid.uuid4())[:8]}",
                text_content=snippet_text,
                published_at=now - timedelta(days=5),
            )
            db.add(record)
            await db.flush()

            assignment = TopicRecordAssignment(
                topic_id=topic.id,
                source_record_id=record.id,
                assignment_score=Decimal("0.9200"),
                model_version="v1.0",
            )
            db.add(assignment)

    # 3. Seed Audience Clusters
    audiences_seeded = 0
    cluster_definitions = [
        ("Eco-Conscious Urban Millennials", 650, 0.88),
        ("Holistic Wellness & Clean Living", 820, 0.82),
    ]

    for c_name, rec_count, q_score in cluster_definitions:
        c_stmt = select(AudienceCluster).where(
            AudienceCluster.workspace_id == workspace.id,
            AudienceCluster.name == c_name,
        )
        cluster = await db.scalar(c_stmt)
        if not cluster:
            cluster = AudienceCluster(
                id=uuid.uuid4(),
                workspace_id=workspace.id,
                name=c_name,
                is_user_renamed=False,
                label_locked=False,
                record_count=rec_count,
                quality_score=Decimal(str(q_score)),
            )
            db.add(cluster)
            await db.flush()
            audiences_seeded += 1

    # 4. Seed Demo Campaign & Metrics
    camp_stmt = select(Campaign).where(
        Campaign.workspace_id == workspace.id,
        Campaign.external_campaign_id == "festive_meta_d2c_in",
    )
    campaign = await db.scalar(camp_stmt)
    if not campaign:
        campaign = Campaign(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            external_campaign_id="festive_meta_d2c_in",
            name="Festive D2C Meta Conversion Campaign",
            channel="Meta Ads",
            currency="INR",
            start_date=today - timedelta(days=14),
            end_date=today,
        )
        db.add(campaign)
        await db.flush()

        metrics = CampaignDailyMetric(
            id=uuid.uuid4(),
            campaign_id=campaign.id,
            local_date=today - timedelta(days=1),
            impressions=45000,
            clicks=1800,
            spend=Decimal("25000.00"),
            conversions=90,
            attributed_revenue=Decimal("112500.00"),
            creative_label="Linen festive carousel",
            audience_label="Eco-conscious tier 1",
        )
        db.add(metrics)

    # 5. Audit Event and Job Queue record
    audit = AuditEvent(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="workspace.seed_demo",
        resource_type="workspace",
        resource_id=workspace.id,
        metadata_json={"industry": industry},
    )
    db.add(audit)

    job = BackgroundJob(
        workspace_id=workspace.id,
        job_type="seed_demo_workspace",
        payload={"workspace_id": str(workspace.id), "industry": industry},
        status="completed",
    )
    db.add(job)

    await db.commit()

    data = WorkspaceSeedDemoResponse(
        workspace_id=workspace.id,
        topics_seeded=topics_seeded,
        trends_seeded=trends_seeded,
        audiences_seeded=audiences_seeded,
        sources_seeded=sources_seeded,
    )
    req_id = get_request_id(request) if request else str(uuid.uuid4())
    return EnvelopeResponse(data=data, meta=ResponseMeta(request_id=req_id))

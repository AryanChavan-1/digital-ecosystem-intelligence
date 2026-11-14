import uuid
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_workspace, get_db, get_request_id
from app.core.errors import NotFoundException, TenantAccessDeniedException
from app.models.audience import AudienceCluster, ClusterTopic
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.audience import (
    AudienceClusterResponseData,
    AudienceClusterUpdateRequest,
    AudienceTopicItem,
)
from app.schemas.envelope import EnvelopeResponse, ResponseMeta

router = APIRouter(prefix="/audiences", tags=["Audiences"])


@router.get(
    "",
    response_model=EnvelopeResponse[List[AudienceClusterResponseData]],
    status_code=status.HTTP_200_OK,
    summary="List workspace interest clusters with top topics and quality scores",
)
async def list_audiences(
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[List[AudienceClusterResponseData]]:
    """
    List audience interest clusters belonging to the active workspace.
    Includes top weighted topics, cluster size, quality score, and label_locked status.
    """
    workspace, _ = workspace_and_role

    stmt = (
        select(AudienceCluster)
        .options(
            selectinload(AudienceCluster.cluster_topics).selectinload(ClusterTopic.topic)
        )
        .where(AudienceCluster.workspace_id == workspace.id)
        .order_by(AudienceCluster.created_at.desc())
    )
    res = await db.execute(stmt)
    clusters = res.scalars().all()

    items: List[AudienceClusterResponseData] = []
    for c in clusters:
        top_topics = [
            AudienceTopicItem(
                topic_id=ct.topic_id,
                canonical_label=ct.topic.canonical_label if ct.topic else "Topic",
                weight=ct.weight,
            )
            for ct in sorted(c.cluster_topics, key=lambda x: x.weight, reverse=True)[:5]
        ]

        items.append(
            AudienceClusterResponseData(
                id=c.id,
                workspace_id=c.workspace_id,
                name=c.name,
                description=c.description,
                record_count=c.record_count,
                quality_score=c.quality_score,
                is_user_renamed=c.is_user_renamed,
                label_locked=c.label_locked,
                top_topics=top_topics,
                created_at=c.created_at,
            )
        )

    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=items, meta=meta)


@router.patch(
    "/{cluster_id}",
    response_model=EnvelopeResponse[AudienceClusterResponseData],
    status_code=status.HTTP_200_OK,
    summary="Rename an audience cluster and lock label against re-clustering overwrites",
)
async def update_audience_cluster(
    cluster_id: uuid.UUID,
    payload: AudienceClusterUpdateRequest,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AudienceClusterResponseData]:
    """
    Update audience cluster label. Sets is_user_renamed=True and label_locked=True
    so nightly HDBSCAN re-clustering jobs never overwrite human-curated labels.
    """
    workspace, _ = workspace_and_role

    stmt = (
        select(AudienceCluster)
        .options(
            selectinload(AudienceCluster.cluster_topics).selectinload(ClusterTopic.topic)
        )
        .where(AudienceCluster.id == cluster_id)
    )
    res = await db.execute(stmt)
    cluster = res.scalar_one_or_none()

    if not cluster:
        raise NotFoundException(message=f"Audience cluster {cluster_id} not found.")

    if cluster.workspace_id != workspace.id:
        raise TenantAccessDeniedException(
            message="Audience cluster does not belong to active workspace."
        )

    # Rename and lock label
    cluster.name = payload.name.strip()
    cluster.is_user_renamed = True
    cluster.label_locked = True

    await db.commit()

    stmt = (
        select(AudienceCluster)
        .options(
            selectinload(AudienceCluster.cluster_topics).selectinload(ClusterTopic.topic)
        )
        .where(AudienceCluster.id == cluster_id)
    )
    res = await db.execute(stmt)
    cluster = res.scalar_one()

    top_topics = [
        AudienceTopicItem(
            topic_id=ct.topic_id,
            canonical_label=ct.topic.canonical_label if ct.topic else "Topic",
            weight=ct.weight,
        )
        for ct in sorted(cluster.cluster_topics, key=lambda x: x.weight, reverse=True)[:5]
    ]

    data = AudienceClusterResponseData(
        id=cluster.id,
        workspace_id=cluster.workspace_id,
        name=cluster.name,
        description=cluster.description,
        record_count=cluster.record_count,
        quality_score=cluster.quality_score,
        is_user_renamed=cluster.is_user_renamed,
        label_locked=cluster.label_locked,
        top_topics=top_topics,
        created_at=cluster.created_at,
    )
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)

from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_workspace, get_db, get_request_id
from app.models.source import DataSource
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.envelope import EnvelopeResponse, ResponseMeta
from app.schemas.source import DataSourceResponse

router = APIRouter(prefix="/sources", tags=["Data Sources"])


@router.get(
    "",
    response_model=EnvelopeResponse[List[DataSourceResponse]],
    status_code=status.HTTP_200_OK,
    summary="List configured data sources for the current workspace",
)
async def list_sources(
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[List[DataSourceResponse]]:
    """
    List configured data sources for the active workspace.
    Includes workspace-specific sources as well as global reference sources (workspace_id IS NULL).
    """
    workspace, _ = workspace_and_role

    stmt = (
        select(DataSource)
        .where(
            or_(
                DataSource.workspace_id == workspace.id,
                DataSource.workspace_id.is_(None),
            )
        )
        .order_by(DataSource.created_at.desc())
    )
    result = await db.execute(stmt)
    sources = result.scalars().all()

    data = [DataSourceResponse.model_validate(s) for s in sources]
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)

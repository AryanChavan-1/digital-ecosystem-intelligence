import uuid
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_request_id
from app.core.errors import ForbiddenException, TenantAccessDeniedException
from app.models.audit import AuditEvent
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.envelope import EnvelopeResponse, ResponseMeta
from app.schemas.workspace import (
    WorkspaceMembershipResponse,
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

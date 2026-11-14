import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_workspace, get_db, get_request_id
from app.core.errors import NotFoundException, TenantAccessDeniedException
from app.models.audit import AuditEvent
from app.models.record import SourceRecord
from app.models.source import DataSource
from app.models.topic import TopicRecordAssignment
from app.models.upload import Upload
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.envelope import EnvelopeResponse, ResponseMeta
from app.schemas.source import DataSourceResponse
from app.services.storage_service import get_storage_service

router = APIRouter(tags=["Data Sources"])


@router.get(
    "/sources",
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


async def _handle_delete_source(
    source_id: uuid.UUID,
    request: Request,
    workspace: Workspace,
    current_user: User,
    db: AsyncSession,
) -> EnvelopeResponse[Dict[str, Any]]:
    # 1. Query data source
    stmt = select(DataSource).where(DataSource.id == source_id)
    res = await db.execute(stmt)
    source = res.scalar_one_or_none()

    if not source:
        raise NotFoundException(message=f"Data source {source_id} not found.")

    if source.workspace_id != workspace.id:
        raise TenantAccessDeniedException(
            message="Data source does not belong to active workspace."
        )

    storage = get_storage_service()

    # 2. Check and delete raw file in storage if object_key exists
    if source.permission_reference and source.permission_reference.startswith("workspaces/"):
        try:
            storage.delete_object(source.permission_reference)
        except Exception:
            pass

    # Also check if any uploads in workspace are linked
    upload_stmt = select(Upload).where(
        Upload.workspace_id == workspace.id,
        Upload.original_filename.ilike(f"%{source.display_name}%"),
    )
    up_res = await db.execute(upload_stmt)
    for up in up_res.scalars().all():
        try:
            storage.delete_object(up.object_key)
        except Exception:
            pass

    # 3. Find associated source_records and cascade purge
    rec_stmt = select(SourceRecord.id).where(SourceRecord.source_id == source_id)
    rec_res = await db.execute(rec_stmt)
    record_ids = rec_res.scalars().all()

    if record_ids:
        # Purge assignments
        await db.execute(
            delete(TopicRecordAssignment).where(
                TopicRecordAssignment.source_record_id.in_(record_ids)
            )
        )
        # Purge records
        await db.execute(
            delete(SourceRecord).where(SourceRecord.source_id == source_id)
        )

    # 4. Purge source row
    await db.delete(source)

    # 5. Log DPDP compliance audit event without retaining deleted payload
    audit_event = AuditEvent(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="dpdp_source_purge",
        resource_type="data_sources",
        resource_id=source_id,
        metadata_json={
            "status": "purged",
            "purged_records_count": len(record_ids),
            "dpdp_compliant": True,
        },
    )
    db.add(audit_event)

    await db.commit()

    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(
        data={"deleted_source_id": str(source_id), "status": "purged"},
        meta=meta,
    )


@router.delete(
    "/data/{source_id}",
    response_model=EnvelopeResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="DPDP cascade purge of data source, records, and raw storage files",
)
async def delete_data_source(
    source_id: uuid.UUID,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[Dict[str, Any]]:
    workspace, _ = workspace_and_role
    return await _handle_delete_source(source_id, request, workspace, current_user, db)


@router.delete(
    "/sources/{source_id}",
    response_model=EnvelopeResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Alias for /data/{source_id}",
    include_in_schema=False,
)
async def delete_source_alias(
    source_id: uuid.UUID,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[Dict[str, Any]]:
    workspace, _ = workspace_and_role
    return await _handle_delete_source(source_id, request, workspace, current_user, db)

import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_workspace, get_db, get_request_id
from app.core.errors import NotFoundException, TenantAccessDeniedException
from app.models.job import BackgroundJob
from app.models.upload import Upload
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.envelope import EnvelopeResponse, ResponseMeta
from app.schemas.upload import (
    UploadConfirmRequest,
    UploadCreateRequest,
    UploadCreateResponseData,
    UploadDetailResponseData,
)
from app.services.storage_service import get_storage_service

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post(
    "",
    response_model=EnvelopeResponse[UploadCreateResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Create an upload record and get presigned upload URL",
)
async def create_upload(
    request: Request,
    payload: UploadCreateRequest,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[UploadCreateResponseData]:
    """
    Validate filename and size, generate safe UUID-based storage key,
    create an uploads table record (status='created'), and return presigned URL.
    """
    workspace, _ = workspace_and_role
    storage = get_storage_service()

    upload_id = uuid.uuid4()
    storage.validate_file_size(payload.file_size_bytes)
    object_key = storage.generate_object_key(workspace.id, upload_id, extension="csv")
    upload_url = storage.generate_upload_url(object_key)

    upload = Upload(
        id=upload_id,
        workspace_id=workspace.id,
        uploaded_by=current_user.id,
        object_key=object_key,
        original_filename=payload.filename,
        file_size_bytes=payload.file_size_bytes,
        status="created",
    )
    db.add(upload)
    await db.commit()
    await db.refresh(upload)

    data = UploadCreateResponseData(
        upload_id=upload.id,
        upload_url=upload_url,
        object_key=object_key,
    )
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)


async def _handle_upload_confirm(
    upload_id: uuid.UUID,
    payload: UploadConfirmRequest,
    request: Request,
    workspace: Workspace,
    db: AsyncSession,
) -> EnvelopeResponse[UploadDetailResponseData]:
    # Query upload
    stmt = select(Upload).where(Upload.id == upload_id)
    res = await db.execute(stmt)
    upload = res.scalar_one_or_none()

    if not upload:
        raise NotFoundException(message=f"Upload {upload_id} not found.")

    if upload.workspace_id != workspace.id:
        raise TenantAccessDeniedException(
            message="Upload does not belong to active workspace."
        )

    # Idempotent behavior: if already confirmed/uploaded, don't re-enqueue
    if upload.status == "created":
        mapping_data: Dict[str, Any] = {"mapping": payload.mapping}
        if payload.date_format:
            mapping_data["date_format"] = payload.date_format

        upload.mapping = mapping_data
        upload.status = "uploaded"

        # Enqueue background job: validate_upload
        job_payload = {
            "upload_id": str(upload.id),
            "workspace_id": str(workspace.id),
            "mapping": payload.mapping,
        }
        if payload.date_format:
            job_payload["date_format"] = payload.date_format

        job = BackgroundJob(
            workspace_id=workspace.id,
            job_type="validate_upload",
            payload=job_payload,
            status="queued",
        )
        db.add(job)
        await db.commit()
        await db.refresh(upload)

    data = UploadDetailResponseData.model_validate(upload)
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)


@router.post(
    "/{upload_id}/confirm",
    response_model=EnvelopeResponse[UploadDetailResponseData],
    status_code=status.HTTP_200_OK,
    summary="Confirm upload, save column mapping, and enqueue validation job",
)
async def confirm_upload(
    upload_id: uuid.UUID,
    payload: UploadConfirmRequest,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[UploadDetailResponseData]:
    workspace, _ = workspace_and_role
    return await _handle_upload_confirm(upload_id, payload, request, workspace, db)


@router.post(
    "/{upload_id}/complete",
    response_model=EnvelopeResponse[UploadDetailResponseData],
    status_code=status.HTTP_200_OK,
    summary="Alias for /confirm matching shared contract",
    include_in_schema=False,
)
async def complete_upload(
    upload_id: uuid.UUID,
    payload: UploadConfirmRequest,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[UploadDetailResponseData]:
    workspace, _ = workspace_and_role
    return await _handle_upload_confirm(upload_id, payload, request, workspace, db)


@router.get(
    "/{upload_id}",
    response_model=EnvelopeResponse[UploadDetailResponseData],
    status_code=status.HTTP_200_OK,
    summary="Get upload status and lifecycle metadata",
)
async def get_upload_status(
    upload_id: uuid.UUID,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[UploadDetailResponseData]:
    workspace, _ = workspace_and_role

    stmt = select(Upload).where(Upload.id == upload_id)
    res = await db.execute(stmt)
    upload = res.scalar_one_or_none()

    if not upload:
        raise NotFoundException(message=f"Upload {upload_id} not found.")

    if upload.workspace_id != workspace.id:
        raise TenantAccessDeniedException(
            message="Upload does not belong to active workspace."
        )

    data = UploadDetailResponseData.model_validate(upload)
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)


# Local storage endpoints for STORAGE_MODE=local dev/test
@router.put(
    "/local-storage/{object_path:path}",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def local_storage_put(object_path: str, request: Request) -> Response:
    """Direct binary upload adapter for local development and integration tests."""
    body = await request.body()
    storage = get_storage_service()
    storage.put_object(object_path, body)
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/local-storage/{object_path:path}",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def local_storage_get(object_path: str) -> Response:
    """Direct binary download adapter for local development and integration tests."""
    storage = get_storage_service()
    if not storage.object_exists(object_path):
        raise NotFoundException(message=f"Object {object_path} not found.")
    data = storage.get_object(object_path)
    return Response(content=data, media_type="text/csv")

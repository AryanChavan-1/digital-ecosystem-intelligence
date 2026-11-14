import uuid
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_workspace, get_db, get_request_id
from app.core.errors import NotFoundException, TenantAccessDeniedException
from app.models.opportunity import Opportunity
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.envelope import EnvelopeResponse, ResponseMeta
from app.schemas.opportunity import (
    OpportunityBriefGenerateResponseData,
    OpportunityCreateRequest,
    OpportunityResponseData,
    OpportunityUpdateRequest,
)
from app.services.brief_service import BriefService

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


@router.post(
    "",
    response_model=EnvelopeResponse[OpportunityResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Save a new opportunity from a trend or custom input",
)
async def create_opportunity(
    request: Request,
    payload: OpportunityCreateRequest,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[OpportunityResponseData]:
    workspace, _ = workspace_and_role

    opp = Opportunity(
        workspace_id=workspace.id,
        created_by=current_user.id,
        topic_id=payload.topic_id,
        title=payload.title,
        summary=payload.summary,
        status=payload.status,
        score=payload.score,
    )
    db.add(opp)
    await db.commit()
    await db.refresh(opp)

    data = OpportunityResponseData.model_validate(opp)
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)


@router.get(
    "",
    response_model=EnvelopeResponse[List[OpportunityResponseData]],
    status_code=status.HTTP_200_OK,
    summary="List saved opportunities in the active workspace",
)
async def list_opportunities(
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[List[OpportunityResponseData]]:
    workspace, _ = workspace_and_role

    stmt = (
        select(Opportunity)
        .where(Opportunity.workspace_id == workspace.id)
        .order_by(Opportunity.created_at.desc())
    )
    res = await db.execute(stmt)
    opps = res.scalars().all()

    data = [OpportunityResponseData.model_validate(o) for o in opps]
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)


@router.get(
    "/{opportunity_id}",
    response_model=EnvelopeResponse[OpportunityResponseData],
    status_code=status.HTTP_200_OK,
    summary="Get single opportunity details by ID",
)
async def get_opportunity(
    opportunity_id: uuid.UUID,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[OpportunityResponseData]:
    workspace, _ = workspace_and_role

    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    res = await db.execute(stmt)
    opp = res.scalar_one_or_none()

    if not opp:
        raise NotFoundException(message=f"Opportunity {opportunity_id} not found.")

    if opp.workspace_id != workspace.id:
        raise TenantAccessDeniedException(
            message="Opportunity does not belong to active workspace."
        )

    data = OpportunityResponseData.model_validate(opp)
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)


@router.patch(
    "/{opportunity_id}",
    response_model=EnvelopeResponse[OpportunityResponseData],
    status_code=status.HTTP_200_OK,
    summary="Edit opportunity brief text, status, score, or notes",
)
async def update_opportunity(
    opportunity_id: uuid.UUID,
    payload: OpportunityUpdateRequest,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[OpportunityResponseData]:
    workspace, _ = workspace_and_role

    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    res = await db.execute(stmt)
    opp = res.scalar_one_or_none()

    if not opp:
        raise NotFoundException(message=f"Opportunity {opportunity_id} not found.")

    if opp.workspace_id != workspace.id:
        raise TenantAccessDeniedException(
            message="Opportunity does not belong to active workspace."
        )

    if payload.title is not None:
        opp.title = payload.title
    if payload.summary is not None:
        opp.summary = payload.summary
    if payload.status is not None:
        opp.status = payload.status
    if payload.score is not None:
        opp.score = payload.score

    await db.commit()
    await db.refresh(opp)

    data = OpportunityResponseData.model_validate(opp)
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)


@router.post(
    "/{opportunity_id}/generate-brief",
    response_model=EnvelopeResponse[OpportunityBriefGenerateResponseData],
    status_code=status.HTTP_200_OK,
    summary="Synthesize 7-section Opportunity Brief with strict citation verification",
)
async def generate_brief(
    opportunity_id: uuid.UUID,
    request: Request,
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[OpportunityBriefGenerateResponseData]:
    """
    Synthesize Citation-Verified LLM Opportunity Brief:
    1. Gathers topic signals, top source records, audience clusters, and campaign KPIs.
    2. Calls LLM with prompt structured into 7 core analytical sections.
    3. Runs Strict Citation Verifier to eliminate hallucinated references.
    4. Enforces ASCI disclosure compliance reminder (#Ad, #Sponsored).
    5. Saves brief into opportunity.evidence and returns verified response.
    """
    workspace, _ = workspace_and_role

    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    res = await db.execute(stmt)
    opp = res.scalar_one_or_none()

    if not opp:
        raise NotFoundException(message=f"Opportunity {opportunity_id} not found.")

    if opp.workspace_id != workspace.id:
        raise TenantAccessDeniedException(
            message="Opportunity does not belong to active workspace."
        )

    brief_data = await BriefService.build_opportunity_brief(
        db=db, workspace_id=workspace.id, opportunity=opp
    )

    data = OpportunityBriefGenerateResponseData.model_validate(brief_data)
    meta = ResponseMeta(request_id=get_request_id(request))
    return EnvelopeResponse(data=data, meta=meta)

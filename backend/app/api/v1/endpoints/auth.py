from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, get_request_id
from app.core.config import settings
from app.core.errors import ConflictException, UnauthorizedException
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    sign_cookie_value,
    unsign_cookie_value,
    verify_password,
)
from app.models.audit import AuditEvent
from app.models.session import Session
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.auth import (
    AuthResponseData,
    LoginRequest,
    MeResponseData,
    SignupRequest,
    UserResponse,
)
from app.schemas.envelope import EnvelopeResponse, ResponseMeta
from app.schemas.workspace import WorkspaceMembershipResponse, WorkspaceSummaryResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_auth_cookie(response: Response, raw_token: str) -> None:
    """Set signed HttpOnly session cookie on response."""
    signed_val = sign_cookie_value(raw_token, settings.SESSION_SECRET)
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=signed_val,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clear session cookie on response."""
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )


@router.post(
    "/signup",
    response_model=EnvelopeResponse[AuthResponseData],
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    payload: SignupRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AuthResponseData]:
    """
    Sign up a new user.
    Creates user, default workspace, and owner membership in one atomic transaction,
    issues a session, and sets a signed HttpOnly session cookie.
    """
    email_clean = payload.email.lower().strip()

    # Check if user already exists
    existing = await db.scalar(select(User).where(User.email == email_clean))
    if existing:
        raise ConflictException(
            code="USER_ALREADY_EXISTS",
            message="An account with this email already exists.",
        )

    # 1. Create User
    pwd_hash = hash_password(payload.password)
    new_user = User(
        email=email_clean,
        password_hash=pwd_hash,
        display_name=payload.display_name,
    )
    db.add(new_user)
    await db.flush()

    # 2. Create Default Workspace
    ws_name = (
        payload.workspace_name.strip()
        if payload.workspace_name
        else f"{payload.display_name or 'My'} Workspace"
    )
    new_workspace = Workspace(
        name=ws_name,
        created_by=new_user.id,
        market_region="IN",
        default_language="en",
    )
    db.add(new_workspace)
    await db.flush()

    # 3. Create Workspace Member (Role: owner)
    member = WorkspaceMember(
        workspace_id=new_workspace.id,
        user_id=new_user.id,
        role="owner",
        status="active",
    )
    db.add(member)

    # 4. Create Session
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires = datetime.now(timezone.utc) + timedelta(
        seconds=settings.SESSION_MAX_AGE_SECONDS
    )
    new_session = Session(
        user_id=new_user.id,
        session_token_hash=token_hash,
        expires_at=expires,
    )
    db.add(new_session)

    # 5. Audit Log
    audit = AuditEvent(
        workspace_id=new_workspace.id,
        actor_user_id=new_user.id,
        action="auth.signup",
        resource_type="user",
        resource_id=new_user.id,
        metadata_json={"email": email_clean},
    )
    db.add(audit)

    await db.commit()

    # Set Cookie
    _set_auth_cookie(response, raw_token)

    req_id = get_request_id(request)
    return EnvelopeResponse(
        data=AuthResponseData(
            user=UserResponse(
                id=new_user.id,
                email=new_user.email,
                display_name=new_user.display_name,
                created_at=new_user.created_at,
            ),
            workspace=WorkspaceSummaryResponse(
                id=new_workspace.id,
                name=new_workspace.name,
                role="owner",
                industry=new_workspace.industry,
                market_region=new_workspace.market_region,
                default_language=new_workspace.default_language,
            ),
        ),
        meta=ResponseMeta(request_id=req_id),
    )


@router.post(
    "/login",
    response_model=EnvelopeResponse[AuthResponseData],
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AuthResponseData]:
    """
    Authenticate user via email & password.
    Issues session and sets signed HttpOnly session cookie.
    Returns generic error on credential mismatch to prevent account enumeration.
    """
    email_clean = payload.email.lower().strip()

    stmt = (
        select(User)
        .options(selectinload(User.memberships).selectinload(WorkspaceMember.workspace))
        .where(User.email == email_clean)
    )
    user = await db.scalar(stmt)

    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
        )

    # Issue Session
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires = datetime.now(timezone.utc) + timedelta(
        seconds=settings.SESSION_MAX_AGE_SECONDS
    )
    new_session = Session(
        user_id=user.id,
        session_token_hash=token_hash,
        expires_at=expires,
    )
    db.add(new_session)

    # Find primary/default workspace
    active_membership = next(
        (m for m in user.memberships if m.status == "active"), None
    )

    ws_id = active_membership.workspace.id if active_membership else None
    audit = AuditEvent(
        workspace_id=ws_id,
        actor_user_id=user.id,
        action="auth.login",
        resource_type="session",
        resource_id=new_session.id,
        metadata_json={},
    )
    db.add(audit)

    await db.commit()

    _set_auth_cookie(response, raw_token)

    req_id = get_request_id(request)
    primary_ws = active_membership.workspace if active_membership else None
    primary_role = active_membership.role if active_membership else "viewer"

    return EnvelopeResponse(
        data=AuthResponseData(
            user=UserResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                created_at=user.created_at,
            ),
            workspace=WorkspaceSummaryResponse(
                id=primary_ws.id if primary_ws else user.id,
                name=primary_ws.name if primary_ws else "Default Workspace",
                role=primary_role,
                industry=primary_ws.industry if primary_ws else None,
                market_region=primary_ws.market_region if primary_ws else "IN",
                default_language=primary_ws.default_language if primary_ws else "en",
            ),
        ),
        meta=ResponseMeta(request_id=req_id),
    )


@router.post(
    "/logout",
    response_model=EnvelopeResponse[Dict[str, str]],
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[Dict[str, str]]:
    """Log out user, invalidate session in database, and clear cookie."""
    signed_token = request.cookies.get(settings.COOKIE_NAME)
    if signed_token:
        raw_token = unsign_cookie_value(signed_token, settings.SESSION_SECRET)
        if raw_token:
            token_hash = hash_session_token(raw_token)
            stmt = select(Session).where(Session.session_token_hash == token_hash)
            session_rec = await db.scalar(stmt)
            if session_rec:
                await db.delete(session_rec)
                await db.commit()

    _clear_auth_cookie(response)
    req_id = get_request_id(request)
    return EnvelopeResponse(
        data={"message": "Logged out successfully."},
        meta=ResponseMeta(request_id=req_id),
    )


@router.get(
    "/me",
    response_model=EnvelopeResponse[MeResponseData],
    status_code=status.HTTP_200_OK,
)
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MeResponseData]:
    """Retrieve current authenticated user profile and active workspace memberships."""
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
        data=MeResponseData(
            user=UserResponse(
                id=current_user.id,
                email=current_user.email,
                display_name=current_user.display_name,
                created_at=current_user.created_at,
            ),
            workspaces=workspaces,
        ),
        meta=ResponseMeta(request_id=req_id),
    )

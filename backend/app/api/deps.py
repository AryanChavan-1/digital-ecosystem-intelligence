import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional, Tuple

from fastapi import Depends, Header, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.errors import TenantAccessDeniedException, UnauthorizedException
from app.core.security import hash_session_token, unsign_cookie_value
from app.models.session import Session
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember


def get_request_id(request: Request) -> str:
    """Extract request_id attached by RequestIdMiddleware."""
    return getattr(request.state, "request_id", "req_unknown")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate request using signed HttpOnly session cookie."""
    signed_token = request.cookies.get(settings.COOKIE_NAME)
    if not signed_token:
        raise UnauthorizedException(
            code="UNAUTHENTICATED",
            message="Authentication session cookie is missing.",
        )

    raw_token = unsign_cookie_value(signed_token, settings.SESSION_SECRET)
    if not raw_token:
        raise UnauthorizedException(
            code="INVALID_SESSION",
            message="Invalid or tampered session token.",
        )

    token_hash = hash_session_token(raw_token)
    now_utc = datetime.now(timezone.utc)

    # Query active session
    stmt = (
        select(Session)
        .options(selectinload(Session.user))
        .where(
            Session.session_token_hash == token_hash,
            Session.expires_at > now_utc,
        )
    )
    result = await db.execute(stmt)
    session_record = result.scalar_one_or_none()

    if not session_record or not session_record.user:
        raise UnauthorizedException(
            code="SESSION_EXPIRED",
            message="Session has expired or is invalid. Please log in again.",
        )

    # Update last_seen_at
    session_record.last_seen_at = now_utc
    await db.commit()

    return session_record.user


async def get_current_workspace(
    request: Request,
    x_workspace_id: Optional[str] = Header(default=None, alias="X-Workspace-ID"),
    query_workspace_id: Optional[str] = Query(default=None, alias="workspace_id"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tuple[Workspace, str]:
    """
    Enforce strict tenant boundary.
    Resolves requested workspace, checks active membership in `workspace_members`,
    and returns (workspace, user_role).
    Raises TenantAccessDeniedException if user is not an active member.
    """
    target_workspace_id_str = x_workspace_id or query_workspace_id
    target_workspace_id: Optional[uuid.UUID] = None

    if target_workspace_id_str:
        try:
            target_workspace_id = uuid.UUID(target_workspace_id_str)
        except ValueError:
            raise TenantAccessDeniedException(
                message="Invalid workspace ID format."
            )

    if target_workspace_id:
        stmt = (
            select(WorkspaceMember, Workspace)
            .join(Workspace, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                WorkspaceMember.workspace_id == target_workspace_id,
                WorkspaceMember.user_id == current_user.id,
                WorkspaceMember.status == "active",
            )
        )
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            raise TenantAccessDeniedException(
                code="TENANT_ACCESS_DENIED",
                message="Resource does not belong to active workspace.",
            )
        membership, workspace = row
        return workspace, membership.role
    else:
        # Default to first active workspace where user has membership
        stmt = (
            select(WorkspaceMember, Workspace)
            .join(Workspace, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                WorkspaceMember.user_id == current_user.id,
                WorkspaceMember.status == "active",
            )
            .order_by(
                func.case(
                    (WorkspaceMember.role == "owner", 1),
                    (WorkspaceMember.role == "admin", 2),
                    else_=3,
                )
            )
        )
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            raise TenantAccessDeniedException(
                code="NO_WORKSPACE_MEMBERSHIP",
                message="User does not belong to any active workspace.",
            )
        membership, workspace = row
        return workspace, membership.role

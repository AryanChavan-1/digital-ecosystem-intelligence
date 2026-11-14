import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.workspace import WorkspaceMembershipResponse, WorkspaceSummaryResponse


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    display_name: Optional[str] = Field(default=None, max_length=255)
    workspace_name: Optional[str] = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: Optional[str] = None
    created_at: datetime


class AuthResponseData(BaseModel):
    user: UserResponse
    workspace: WorkspaceSummaryResponse


class MeResponseData(BaseModel):
    user: UserResponse
    workspaces: List[WorkspaceMembershipResponse]

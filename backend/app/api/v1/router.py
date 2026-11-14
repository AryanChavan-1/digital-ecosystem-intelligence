from fastapi import APIRouter

from app.api.v1.endpoints import auth, workspaces
from app.schemas.auth import MeResponseData
from app.schemas.envelope import EnvelopeResponse

api_router = APIRouter()

# Mount auth routes (/api/v1/auth/*)
api_router.include_router(auth.router)

# Also expose GET /api/v1/me directly as specified in REST contract
api_router.add_api_route(
    "/me",
    auth.get_me,
    methods=["GET"],
    response_model=EnvelopeResponse[MeResponseData],
    tags=["Authentication"],
    summary="Get current user profile and workspaces",
)

# Mount workspaces routes (/api/v1/workspaces/*)
api_router.include_router(workspaces.router)

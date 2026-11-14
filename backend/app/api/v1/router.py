from fastapi import APIRouter

from app.api.v1.endpoints import (
    audiences,
    auth,
    campaigns,
    dashboard,
    opportunities,
    reports,
    sources,
    trends,
    uploads,
    workspaces,
)
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

# Mount sources & data routes (/api/v1/sources/* and /api/v1/data/*)
api_router.include_router(sources.router)

# Mount uploads routes (/api/v1/uploads/*)
api_router.include_router(uploads.router)

# Mount campaigns routes (/api/v1/campaigns/*)
api_router.include_router(campaigns.router)

# Mount dashboard routes (/api/v1/dashboard/*)
api_router.include_router(dashboard.router)

# Mount trends routes (/api/v1/trends/*)
api_router.include_router(trends.router)

# Mount audiences routes (/api/v1/audiences/*)
api_router.include_router(audiences.router)

# Mount opportunities routes (/api/v1/opportunities/*)
api_router.include_router(opportunities.router)

# Mount reports routes (/api/v1/reports/*)
api_router.include_router(reports.router)

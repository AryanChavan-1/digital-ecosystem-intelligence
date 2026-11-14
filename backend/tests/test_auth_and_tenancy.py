import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_health_live(client: AsyncClient):
    """Verify liveness probe returns live status."""
    res = await client.get("/health/live")
    assert res.status_code == 200
    assert res.json() == {"status": "live"}


@pytest.mark.asyncio
async def test_health_ready(client: AsyncClient):
    """Verify readiness probe checks database connectivity and returns ready status."""
    res = await client.get("/health/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ready", "database": "connected"}


@pytest.mark.asyncio
async def test_signup_creates_user_and_workspace(client: AsyncClient):
    """
    Test signup creates user, workspace with owner role, and sets HttpOnly cookie.
    Validates standard response envelope.
    """
    payload = {
        "email": "aryan@example.com",
        "password": "Password123!",
        "display_name": "Aryan Chavan",
        "workspace_name": "Aryan D2C Intelligence",
    }
    res = await client.post("/api/v1/auth/signup", json=payload)
    assert res.status_code == 201

    body = res.json()
    assert "data" in body
    assert "meta" in body
    assert body["meta"]["request_id"].startswith("req_")

    data = body["data"]
    assert data["user"]["email"] == "aryan@example.com"
    assert data["user"]["display_name"] == "Aryan Chavan"
    assert data["workspace"]["name"] == "Aryan D2C Intelligence"
    assert data["workspace"]["role"] == "owner"
    assert data["workspace"]["market_region"] == "IN"

    # Verify session cookie was set
    assert settings.COOKIE_NAME in res.cookies


@pytest.mark.asyncio
async def test_signup_duplicate_email_fails(client: AsyncClient):
    """Verify signup with an already registered email returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
    }
    res1 = await client.post("/api/v1/auth/signup", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/signup", json=payload)
    assert res2.status_code == 409
    body = res2.json()
    assert body["error"]["code"] == "USER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_login_and_logout_lifecycle(client: AsyncClient):
    """Verify login authenticates and logout invalidates session."""
    # 1. Signup
    signup_payload = {
        "email": "lifecycle@example.com",
        "password": "SecurePassword123!",
        "display_name": "Test User",
    }
    signup_res = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert signup_res.status_code == 201

    # 2. Login
    client.cookies.clear()
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "lifecycle@example.com", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    assert settings.COOKIE_NAME in login_res.cookies

    # 3. GET /me (both /api/v1/me and /api/v1/auth/me)
    me_res = await client.get("/api/v1/me")
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["user"]["email"] == "lifecycle@example.com"
    assert len(me_data["workspaces"]) == 1
    assert me_data["workspaces"][0]["role"] == "owner"

    auth_me_res = await client.get("/api/v1/auth/me")
    assert auth_me_res.status_code == 200

    # 4. Logout
    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    # 5. Subsequent /me call must be rejected as unauthenticated
    me_after_logout = await client.get("/api/v1/me")
    assert me_after_logout.status_code == 401
    assert me_after_logout.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_generic_error(client: AsyncClient):
    """Verify login with invalid password or non-existent email returns generic 401."""
    # Non-existent user
    res1 = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "AnyPassword123!"},
    )
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert res1.json()["error"]["message"] == "Invalid email or password."

    # Existing user, wrong password
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "realuser@example.com", "password": "CorrectPassword123!"},
    )
    client.cookies.clear()

    res2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "realuser@example.com", "password": "WrongPassword!"},
    )
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert res2.json()["error"]["message"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_cross_tenant_isolation(client: AsyncClient):
    """
    CRITICAL SECURITY TEST:
    Verify User A attempting to update or access User B's workspace is strictly denied (403).
    Verify workspaces list only returns workspaces where user has active membership.
    """
    # 1. User A signs up
    res_a = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user_a@example.com",
            "password": "Password123!",
            "workspace_name": "Workspace A",
        },
    )
    assert res_a.status_code == 201
    ws_a_id = res_a.json()["data"]["workspace"]["id"]
    cookie_a = client.cookies.get(settings.COOKIE_NAME)

    # 2. User B signs up
    client.cookies.clear()
    res_b = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user_b@example.com",
            "password": "Password123!",
            "workspace_name": "Workspace B",
        },
    )
    assert res_b.status_code == 201
    ws_b_id = res_b.json()["data"]["workspace"]["id"]
    cookie_b = client.cookies.get(settings.COOKIE_NAME)

    # 3. User A attempts to update Workspace B -> MUST FAIL with 403 TENANT_ACCESS_DENIED
    client.cookies.set(settings.COOKIE_NAME, cookie_a)
    patch_attempt_res = await client.patch(
        f"/api/v1/workspaces/{ws_b_id}",
        json={"industry": "hacked_industry"},
    )
    assert patch_attempt_res.status_code == 403
    assert patch_attempt_res.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    # 4. User B attempts to update Workspace A -> MUST FAIL with 403 TENANT_ACCESS_DENIED
    client.cookies.set(settings.COOKIE_NAME, cookie_b)
    patch_attempt_b = await client.patch(
        f"/api/v1/workspaces/{ws_a_id}",
        json={"industry": "hacked_by_b"},
    )
    assert patch_attempt_b.status_code == 403
    assert patch_attempt_b.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    # 5. User A updates their OWN workspace -> MUST SUCCEED
    client.cookies.set(settings.COOKIE_NAME, cookie_a)
    update_own_res = await client.patch(
        f"/api/v1/workspaces/{ws_a_id}",
        json={
            "name": "Workspace A Renamed",
            "industry": "sustainable_fashion",
            "market_region": "IN",
            "default_language": "en",
        },
    )
    assert update_own_res.status_code == 200
    updated_ws = update_own_res.json()["data"]
    assert updated_ws["name"] == "Workspace A Renamed"
    assert updated_ws["industry"] == "sustainable_fashion"

    # 6. Verify GET /workspaces for User A only returns Workspace A
    list_a_res = await client.get("/api/v1/workspaces")
    assert list_a_res.status_code == 200
    workspaces_a = list_a_res.json()["data"]
    assert len(workspaces_a) == 1
    assert workspaces_a[0]["workspace_id"] == ws_a_id

    # 7. Verify GET /workspaces for User B only returns Workspace B
    client.cookies.set(settings.COOKIE_NAME, cookie_b)
    list_b_res = await client.get("/api/v1/workspaces")
    assert list_b_res.status_code == 200
    workspaces_b = list_b_res.json()["data"]
    assert len(workspaces_b) == 1
    assert workspaces_b[0]["workspace_id"] == ws_b_id

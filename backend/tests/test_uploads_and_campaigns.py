import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignDailyMetric
from app.models.job import BackgroundJob
from app.models.source import DataSource
from app.models.upload import Upload
from app.services.campaign_service import CampaignService, MixedCurrencyError

# -------------------------------------------------------------------------
# 1. CampaignService Unit Tests
# -------------------------------------------------------------------------

def test_campaign_service_kpi_formulas_exact_decimal():
    # CTR = (clicks / impressions) * 100
    ctr = CampaignService.calculate_ctr(clicks=250, impressions=10000)
    assert ctr == Decimal("2.5000")

    # CPC = spend / clicks
    cpc = CampaignService.calculate_cpc(spend=Decimal("5000.00"), clicks=250)
    assert cpc == Decimal("20.0000")

    # CPM = (spend / impressions) * 1000
    cpm = CampaignService.calculate_cpm(spend=Decimal("5000.00"), impressions=100000)
    assert cpm == Decimal("50.0000")

    # CPA = spend / conversions
    cpa = CampaignService.calculate_cpa(spend=Decimal("5000.00"), conversions=Decimal("50"))
    assert cpa == Decimal("100.0000")

    # ROAS = attributed_revenue / spend
    roas = CampaignService.calculate_roas(
        attributed_revenue=Decimal("25000.00"), spend=Decimal("5000.00")
    )
    assert roas == Decimal("5.0000")


def test_campaign_service_zero_denominator_returns_none():
    # Never crash with ZeroDivisionError, never return 0.0, NaN, or Infinity
    assert CampaignService.calculate_ctr(clicks=10, impressions=0) is None
    assert CampaignService.calculate_ctr(clicks=10, impressions=None) is None
    assert CampaignService.calculate_ctr(clicks=None, impressions=100) is None

    assert CampaignService.calculate_cpc(spend=Decimal("100"), clicks=0) is None
    assert CampaignService.calculate_cpc(spend=Decimal("100"), clicks=None) is None
    assert CampaignService.calculate_cpc(spend=None, clicks=50) is None

    assert CampaignService.calculate_cpm(spend=Decimal("100"), impressions=0) is None
    assert CampaignService.calculate_cpm(spend=Decimal("100"), impressions=None) is None

    assert CampaignService.calculate_cpa(spend=Decimal("100"), conversions=0) is None
    assert CampaignService.calculate_cpa(spend=Decimal("100"), conversions=None) is None

    assert CampaignService.calculate_roas(attributed_revenue=Decimal("500"), spend=0) is None
    assert CampaignService.calculate_roas(attributed_revenue=Decimal("500"), spend=None) is None


def test_campaign_service_currency_isolation():
    # Same currency aggregation succeeds
    metrics_inr = [
        {"local_date": date(2026, 5, 1), "spend": Decimal("1000"), "clicks": 50, "currency": "INR"},
        {"local_date": date(2026, 5, 2), "spend": Decimal("2000"), "clicks": 100, "currency": "INR"},
    ]
    totals, _ = CampaignService.aggregate_metrics(metrics_inr)
    assert totals["spend"] == Decimal("3000.0000")
    assert totals["currency"] == "INR"

    # Mixed currencies without conversion must raise MixedCurrencyError
    metrics_mixed = [
        {"local_date": date(2026, 5, 1), "spend": Decimal("1000"), "currency": "INR"},
        {"local_date": date(2026, 5, 2), "spend": Decimal("50"), "currency": "USD"},
    ]
    with pytest.raises(MixedCurrencyError):
        CampaignService.aggregate_metrics(metrics_mixed)


# -------------------------------------------------------------------------
# 2. REST Endpoint & Tenant Isolation Tests
# -------------------------------------------------------------------------

async def _register_user(client: AsyncClient, email: str, ws_name: str) -> dict:
    res = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "display_name": email.split("@")[0].capitalize(),
            "workspace_name": ws_name,
        },
    )
    assert res.status_code == 201
    return res.json()["data"]


@pytest.mark.asyncio
async def test_sources_listing(client: AsyncClient, db_session: AsyncSession):
    # 1. Register User A
    user_a_data = await _register_user(client, "user_a_sources@example.com", "Workspace A")
    ws_a_id = uuid.UUID(user_a_data["workspace"]["id"])

    # 2. Add a workspace source and a global source
    ws_source = DataSource(
        workspace_id=ws_a_id,
        provider="meta",
        source_type="ad_account",
        display_name="Meta Ads Workspace A",
    )
    global_source = DataSource(
        workspace_id=None,
        provider="meta",
        source_type="public_trends",
        display_name="Global Meta Trends",
    )
    other_ws_source = DataSource(
        workspace_id=uuid.uuid4(),
        provider="meta",
        source_type="ad_account",
        display_name="Secret Source Other Workspace",
    )
    db_session.add_all([ws_source, global_source, other_ws_source])
    await db_session.commit()

    # 3. Fetch sources for Workspace A
    res = await client.get("/api/v1/sources", headers={"X-Workspace-ID": str(ws_a_id)})
    assert res.status_code == 200
    body = res.json()
    sources = body["data"]

    # Must contain ws_source and global_source, but NEVER other_ws_source
    source_names = [s["display_name"] for s in sources]
    assert "Meta Ads Workspace A" in source_names
    assert "Global Meta Trends" in source_names
    assert "Secret Source Other Workspace" not in source_names


@pytest.mark.asyncio
async def test_upload_creation_and_confirm_idempotency(
    client: AsyncClient, db_session: AsyncSession
):
    # Register user
    user_data = await _register_user(client, "user_uploads@example.com", "Uploads Workspace")
    ws_id = uuid.UUID(user_data["workspace"]["id"])

    # 1. Validation error on non-csv extension
    bad_res = await client.post(
        "/api/v1/uploads",
        json={"filename": "malicious.exe"},
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert bad_res.status_code == 422

    # 2. Validation error on oversized file (> 25MB)
    oversized_res = await client.post(
        "/api/v1/uploads",
        json={"filename": "huge_export.csv", "file_size_bytes": 30 * 1024 * 1024},
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert oversized_res.status_code == 422

    # 3. Create valid upload
    create_res = await client.post(
        "/api/v1/uploads",
        json={"filename": "meta_ads_may_2026.csv", "file_size_bytes": 1024 * 50},
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert create_res.status_code == 201
    create_data = create_res.json()["data"]
    upload_id = create_data["upload_id"]
    upload_url = create_data["upload_url"]
    object_key = create_data["object_key"]

    # Verify object_key format: workspaces/{workspace_id}/uploads/{upload_id}.csv
    expected_key = f"workspaces/{ws_id}/uploads/{upload_id}.csv"
    assert object_key == expected_key
    assert "local-storage" in upload_url or "http" in upload_url

    # 4. GET /uploads/{id} initially status='created'
    get_res = await client.get(
        f"/api/v1/uploads/{upload_id}",
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert get_res.status_code == 200
    assert get_res.json()["data"]["status"] == "created"

    # 5. Confirm upload (stores mapping and enqueues background job)
    mapping = {
        "date": "Day",
        "campaign_name": "Campaign Name",
        "impressions": "Impressions",
        "clicks": "Clicks",
        "spend": "Amount Spent (INR)",
    }
    confirm_res = await client.post(
        f"/api/v1/uploads/{upload_id}/confirm",
        json={"mapping": mapping, "date_format": "DD/MM/YYYY"},
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()["data"]
    assert confirm_data["status"] == "uploaded"
    assert confirm_data["mapping"]["date_format"] == "DD/MM/YYYY"

    # Verify background_jobs row was created
    stmt = select(BackgroundJob).where(
        BackgroundJob.workspace_id == ws_id,
        BackgroundJob.job_type == "validate_upload",
    )
    job_res = await db_session.execute(stmt)
    jobs = job_res.scalars().all()
    assert len(jobs) == 1
    job = jobs[0]
    assert job.status == "queued"
    assert job.payload["upload_id"] == upload_id
    assert job.payload["workspace_id"] == str(ws_id)
    assert job.payload["date_format"] == "DD/MM/YYYY"

    # 6. IDEMPOTENCY TEST: Calling confirm again must succeed and NOT insert duplicate background job
    confirm_again_res = await client.post(
        f"/api/v1/uploads/{upload_id}/confirm",
        json={"mapping": mapping, "date_format": "DD/MM/YYYY"},
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert confirm_again_res.status_code == 200
    job_res_2 = await db_session.execute(stmt)
    assert len(job_res_2.scalars().all()) == 1


@pytest.mark.asyncio
async def test_campaigns_and_summary_metrics(
    client: AsyncClient, db_session: AsyncSession
):
    # Register user
    user_data = await _register_user(client, "user_campaigns@example.com", "Campaigns Workspace")
    ws_id = uuid.UUID(user_data["workspace"]["id"])

    # 1. Create a campaign and daily metrics
    campaign = Campaign(
        workspace_id=ws_id,
        name="Summer Festive Launch",
        channel="meta",
        currency="INR",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 3),
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    # Day 1: normal metrics
    m1 = CampaignDailyMetric(
        campaign_id=campaign.id,
        local_date=date(2026, 5, 1),
        impressions=10000,
        clicks=250,
        spend=Decimal("5000.0000"),
        conversions=Decimal("25.0000"),
        attributed_revenue=Decimal("20000.0000"),
    )
    # Day 2: 0 impressions and 0 clicks (zero denominator test)
    m2 = CampaignDailyMetric(
        campaign_id=campaign.id,
        local_date=date(2026, 5, 2),
        impressions=0,
        clicks=0,
        spend=Decimal("0.0000"),
        conversions=Decimal("0.0000"),
        attributed_revenue=Decimal("0.0000"),
    )
    db_session.add_all([m1, m2])
    await db_session.commit()

    # 2. List campaigns
    list_res = await client.get("/api/v1/campaigns", headers={"X-Workspace-ID": str(ws_id)})
    assert list_res.status_code == 200
    camp_list = list_res.json()["data"]
    assert len(camp_list) == 1
    assert camp_list[0]["name"] == "Summer Festive Launch"

    # 3. Get campaign summary
    summary_res = await client.get(
        f"/api/v1/campaigns/{campaign.id}/summary",
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert summary_res.status_code == 200
    summary_data = summary_res.json()["data"]

    # Verify overall totals
    totals = summary_data["totals"]
    assert totals["impressions"] == 10000
    assert totals["clicks"] == 250
    assert Decimal(str(totals["spend"])) == Decimal("5000.0000")
    assert Decimal(str(totals["ctr"])) == Decimal("2.5000")
    assert Decimal(str(totals["cpc"])) == Decimal("20.0000")
    assert Decimal(str(totals["roas"])) == Decimal("4.0000")

    # Verify daily breakdown zero-denominator safety
    daily = summary_data["daily_metrics"]
    assert len(daily) == 2

    # Day 2 had 0 impressions and clicks -> CTR, CPC, CPM must be None (JSON null)
    day2 = daily[1]
    assert day2["local_date"] == "2026-05-02"
    assert day2["ctr"] is None
    assert day2["cpc"] is None
    assert day2["cpm"] is None
    assert day2["roas"] is None


@pytest.mark.asyncio
async def test_cross_tenant_isolation(client: AsyncClient, db_session: AsyncSession):
    # 1. Setup User A with Workspace A
    user_a = await _register_user(client, "alice@example.com", "Alice Workspace")
    ws_a_id = uuid.UUID(user_a["workspace"]["id"])

    # Create Alice's upload & campaign
    alice_upload = Upload(
        workspace_id=ws_a_id,
        object_key=f"workspaces/{ws_a_id}/uploads/{uuid.uuid4()}.csv",
        original_filename="alice_secret.csv",
        status="created",
    )
    alice_campaign = Campaign(
        workspace_id=ws_a_id,
        name="Alice Private Campaign",
        currency="INR",
    )
    db_session.add_all([alice_upload, alice_campaign])
    await db_session.commit()
    await db_session.refresh(alice_upload)
    await db_session.refresh(alice_campaign)

    # 2. Setup User B with Workspace B
    client.cookies.clear()
    user_b = await _register_user(client, "bob@example.com", "Bob Workspace")
    ws_b_id = uuid.UUID(user_b["workspace"]["id"])

    # 3. Bob attempts to access Alice's upload via GET -> 403 Forbidden
    res1 = await client.get(
        f"/api/v1/uploads/{alice_upload.id}",
        headers={"X-Workspace-ID": str(ws_b_id)},
    )
    assert res1.status_code == 403
    assert res1.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    # 4. Bob attempts to confirm Alice's upload -> 403 Forbidden
    res2 = await client.post(
        f"/api/v1/uploads/{alice_upload.id}/confirm",
        json={"mapping": {"date": "Day"}},
        headers={"X-Workspace-ID": str(ws_b_id)},
    )
    assert res2.status_code == 403
    assert res2.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    # 5. Bob attempts to view Alice's campaign summary -> 403 Forbidden
    res3 = await client.get(
        f"/api/v1/campaigns/{alice_campaign.id}/summary",
        headers={"X-Workspace-ID": str(ws_b_id)},
    )
    assert res3.status_code == 403
    assert res3.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    # 6. Bob lists campaigns -> Alice's campaign is not present
    res4 = await client.get("/api/v1/campaigns", headers={"X-Workspace-ID": str(ws_b_id)})
    assert res4.status_code == 200
    b_camps = res4.json()["data"]
    assert len(b_camps) == 0

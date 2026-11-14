import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audience import AudienceCluster, ClusterTopic
from app.models.audit import AuditEvent
from app.models.opportunity import Opportunity
from app.models.record import SourceRecord
from app.models.source import DataSource
from app.models.topic import Topic, TopicRecordAssignment, TopicRelation
from app.models.trend import TrendSnapshot
from app.services.brief_service import CitationVerifier


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


# -------------------------------------------------------------------------
# 1. Dashboard & Trends Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_summary_and_trends(
    client: AsyncClient, db_session: AsyncSession
):
    # 1. Register User & Workspace
    user_data = await _register_user(client, "dash_user@example.com", "Fashion D2C Workspace")
    ws_id = uuid.UUID(user_data["workspace"]["id"])

    # 2. Seed Data Sources
    source = DataSource(
        workspace_id=ws_id,
        provider="shopify",
        source_type="store_orders",
        display_name="Shopify Orders",
    )
    db_session.add(source)

    # 3. Seed Topics & Trends
    t1 = Topic(
        workspace_id=ws_id,
        canonical_label="Organic Linen Shirts",
        description="Breathable organic linen for Indian summer workwear.",
    )
    t2 = Topic(
        workspace_id=ws_id,
        canonical_label="Handloom Khadi Blazers",
        description="Handcrafted khadi tailored jackets.",
    )
    db_session.add_all([t1, t2])
    await db_session.commit()
    await db_session.refresh(t1)
    await db_session.refresh(t2)

    # Trend Snapshot for T1: Rising, high momentum
    s1 = TrendSnapshot(
        workspace_id=ws_id,
        topic_id=t1.id,
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 15),
        mention_count=2400,
        previous_mention_count=1200,
        change_pct=Decimal("100.0000"),
        momentum_score=Decimal("85.5000"),
        source_count=4,
        confidence="high",
    )
    # Trend Snapshot for T2: Lower momentum
    s2 = TrendSnapshot(
        workspace_id=ws_id,
        topic_id=t2.id,
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 15),
        mention_count=500,
        previous_mention_count=600,
        change_pct=Decimal("-16.6667"),
        momentum_score=Decimal("20.0000"),
        source_count=1,
        confidence="low",
    )
    db_session.add_all([s1, s2])

    # 4. Seed Opportunity
    opp = Opportunity(
        workspace_id=ws_id,
        title="Linen Workwear Drop",
        topic_id=t1.id,
        status="draft",
        score=Decimal("88.0000"),
    )
    db_session.add(opp)
    await db_session.commit()

    # 5. GET /dashboard/summary
    dash_res = await client.get("/api/v1/dashboard/summary", headers={"X-Workspace-ID": str(ws_id)})
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert dash_data["tracked_topics_count"] == 2
    assert dash_data["rising_topics_count"] == 2
    assert dash_data["saved_opportunities_count"] == 1
    assert dash_data["connected_sources_count"] == 1
    assert len(dash_data["top_rising_trends"]) == 2
    assert dash_data["top_rising_trends"][0]["canonical_label"] == "Organic Linen Shirts"
    assert dash_data["top_rising_trends"][0]["confidence_badge"] == "high"
    assert dash_data["latest_freshness_timestamp"] is not None

    # 6. GET /trends with search & filter
    trends_res = await client.get(
        "/api/v1/trends?search=Linen&confidence=high",
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert trends_res.status_code == 200
    trends_list = trends_res.json()["data"]
    assert len(trends_list) == 1
    assert trends_list[0]["canonical_label"] == "Organic Linen Shirts"
    assert trends_list[0]["is_cold_start"] is False

    # Check cold-start detection on T2 (source_count=1)
    trends_t2 = await client.get(
        "/api/v1/trends?search=Khadi",
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert trends_t2.status_code == 200
    assert trends_t2.json()["data"][0]["is_cold_start"] is True


@pytest.mark.asyncio
async def test_trend_detail_endpoint(client: AsyncClient, db_session: AsyncSession):
    user_data = await _register_user(client, "trend_detail@example.com", "Trend Workspace")
    ws_id = uuid.UUID(user_data["workspace"]["id"])

    # 1. Setup Topic, Related Topic, Audience Cluster, and Evidence Records
    main_topic = Topic(workspace_id=ws_id, canonical_label="Bamboo Silk Kurtas")
    related_topic = Topic(workspace_id=ws_id, canonical_label="Festive Casuals")
    db_session.add_all([main_topic, related_topic])
    await db_session.commit()
    await db_session.refresh(main_topic)
    await db_session.refresh(related_topic)

    snap = TrendSnapshot(
        workspace_id=ws_id,
        topic_id=main_topic.id,
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 15),
        mention_count=3200,
        previous_mention_count=1800,
        change_pct=Decimal("77.7778"),
        momentum_score=Decimal("82.0000"),
        source_count=3,
        confidence="high",
    )
    db_session.add(snap)

    # Relation
    rel = TopicRelation(
        source_topic_id=main_topic.id,
        target_topic_id=related_topic.id,
        relation_type="co_occurs",
        weight=Decimal("0.8500"),
        window_start=date(2026, 5, 1),
        window_end=date(2026, 5, 15),
    )
    db_session.add(rel)

    # Audience Cluster
    aud = AudienceCluster(
        workspace_id=ws_id,
        name="Conscious Ethnic Shoppers",
        record_count=150,
        quality_score=Decimal("0.9200"),
    )
    db_session.add(aud)
    await db_session.commit()
    await db_session.refresh(aud)

    cl_top = ClusterTopic(cluster_id=aud.id, topic_id=main_topic.id, weight=Decimal("0.9000"))
    db_session.add(cl_top)

    # Source Record & Assignment
    rec = SourceRecord(
        workspace_id=ws_id,
        source_type="instagram",
        text_content="Loving the new breathable bamboo silk kurta drop for office wear!",
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(rec)
    await db_session.commit()
    await db_session.refresh(rec)

    assign = TopicRecordAssignment(
        topic_id=main_topic.id,
        source_record_id=rec.id,
        assignment_score=Decimal("0.9500"),
        model_version="v1.0",
    )
    db_session.add(assign)
    await db_session.commit()
    await db_session.refresh(snap)

    # 2. GET /trends/{id}
    res = await client.get(f"/api/v1/trends/{snap.id}", headers={"X-Workspace-ID": str(ws_id)})
    assert res.status_code == 200
    detail = res.json()["data"]

    assert detail["canonical_label"] == "Bamboo Silk Kurtas"
    assert "Bamboo Silk Kurtas" in detail["plain_language_summary"]
    assert len(detail["timeline_series"]) >= 1
    assert len(detail["source_coverage_breakdown"]) >= 1
    assert any(rt["label"] == "Festive Casuals" for rt in detail["related_topics"])
    assert any(ac["name"] == "Conscious Ethnic Shoppers" for ac in detail["associated_audiences"])
    assert len(detail["evidence_snippets"]) >= 1
    assert "bamboo silk" in detail["evidence_snippets"][0]["snippet"].lower()


# -------------------------------------------------------------------------
# 2. Audiences & Cluster Rename Locking Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audiences_listing_and_label_locking(
    client: AsyncClient, db_session: AsyncSession
):
    user_data = await _register_user(client, "audience_user@example.com", "Audience WS")
    ws_id = uuid.UUID(user_data["workspace"]["id"])

    # 1. Create cluster with topic
    topic = Topic(workspace_id=ws_id, canonical_label="Sustainable Denim")
    cluster = AudienceCluster(
        workspace_id=ws_id,
        name="Auto-Generated Cluster #4",
        record_count=80,
        quality_score=Decimal("0.7800"),
        is_user_renamed=False,
        label_locked=False,
    )
    db_session.add_all([topic, cluster])
    await db_session.commit()
    await db_session.refresh(topic)
    await db_session.refresh(cluster)

    ct = ClusterTopic(cluster_id=cluster.id, topic_id=topic.id, weight=Decimal("0.8500"))
    db_session.add(ct)
    await db_session.commit()

    # 2. GET /audiences
    res = await client.get("/api/v1/audiences", headers={"X-Workspace-ID": str(ws_id)})
    assert res.status_code == 200
    clusters = res.json()["data"]
    assert len(clusters) == 1
    assert clusters[0]["name"] == "Auto-Generated Cluster #4"
    assert clusters[0]["label_locked"] is False
    assert clusters[0]["top_topics"][0]["canonical_label"] == "Sustainable Denim"

    # 3. PATCH /audiences/{id} renaming the cluster
    patch_res = await client.patch(
        f"/api/v1/audiences/{cluster.id}",
        json={"name": "Eco-Conscious Denim Enthusiasts"},
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()["data"]
    assert updated["name"] == "Eco-Conscious Denim Enthusiasts"
    assert updated["is_user_renamed"] is True
    assert updated["label_locked"] is True

    # 4. Verify in DB
    db_res = await db_session.execute(
        select(AudienceCluster).where(AudienceCluster.id == cluster.id)
    )
    db_cluster = db_res.scalar_one()
    assert db_cluster.name == "Eco-Conscious Denim Enthusiasts"
    assert db_cluster.label_locked is True
    assert db_cluster.is_user_renamed is True


# -------------------------------------------------------------------------
# 3. Citation-Verified Opportunity Brief Engine Tests
# -------------------------------------------------------------------------

def test_citation_verifier_unit():
    valid_id_1 = str(uuid.uuid4()).lower()
    valid_id_2 = str(uuid.uuid4()).lower()
    hallucinated_id = str(uuid.uuid4()).lower()

    valid_ids = {valid_id_1, valid_id_2}

    # Text containing 2 valid citations and 1 hallucinated citation
    raw_text = (
        f"Significant breakout observed in user reviews [record:{valid_id_1}] and "
        f"confirmed by ad spend data [record:{hallucinated_id}]. Repeat interest shown in [record:{valid_id_2}]."
    )

    cleaned, verified, flagged = CitationVerifier.verify_and_clean_text(raw_text, valid_ids)

    # Verified citations must contain both valid IDs
    assert valid_id_1 in verified
    assert valid_id_2 in verified
    assert hallucinated_id not in verified

    # Hallucinated ID must be flagged
    assert hallucinated_id in flagged

    # Cleaned text must retain valid citations and completely strip hallucinated citation
    assert f"[record:{valid_id_1}]" in cleaned
    assert f"[record:{valid_id_2}]" in cleaned
    assert hallucinated_id not in cleaned


@pytest.mark.asyncio
async def test_generate_opportunity_brief_lifecycle(
    client: AsyncClient, db_session: AsyncSession
):
    user_data = await _register_user(client, "brief_user@example.com", "Brief Workspace")
    ws_id = uuid.UUID(user_data["workspace"]["id"])

    # 1. Create Topic, Trend Snapshot, and Valid Source Record
    topic = Topic(workspace_id=ws_id, canonical_label="Ayurvedic Scalp Oils")
    db_session.add(topic)
    await db_session.commit()
    await db_session.refresh(topic)

    snap = TrendSnapshot(
        workspace_id=ws_id,
        topic_id=topic.id,
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 15),
        mention_count=1800,
        momentum_score=Decimal("88.0000"),
        source_count=3,
        confidence="high",
    )
    rec = SourceRecord(
        workspace_id=ws_id,
        source_type="meta",
        text_content="Rosemary & Bhringraj Scalp Serum showed 4x CTR over standard hair oil.",
    )
    db_session.add_all([snap, rec])
    await db_session.commit()
    await db_session.refresh(rec)

    # 2. Create Opportunity
    create_res = await client.post(
        "/api/v1/opportunities",
        json={
            "title": "Ayurvedic Scalp Serum Launch",
            "topic_id": str(topic.id),
            "status": "draft",
        },
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert create_res.status_code == 201
    opp_id = create_res.json()["data"]["id"]

    # 3. Call POST /opportunities/{id}/generate-brief (mock LLM mode)
    brief_res = await client.post(
        f"/api/v1/opportunities/{opp_id}/generate-brief",
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert brief_res.status_code == 200
    brief_data = brief_res.json()["data"]

    # Verify 7 Core Sections Exist
    assert "signal_summary" in brief_data
    assert "evidence_coverage" in brief_data
    assert "audience_hypotheses" in brief_data
    assert "product_angles" in brief_data
    assert "campaign_experiments" in brief_data
    assert "risks_counter_signals" in brief_data
    assert "confidence_limitations" in brief_data

    # Verify ASCI Disclosure Reminder is appended
    assert "ASCI Disclosure" in brief_data["asci_disclosure_reminder"]
    assert "#Ad" in brief_data["asci_disclosure_reminder"]

    # Verify Citations: rec.id must be in verified citations
    assert str(rec.id).lower() in brief_data["verified_citations"]


# -------------------------------------------------------------------------
# 4. DPDP Deletion, Report Export & Cross-Tenant Isolation Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dpdp_source_purge_and_cross_tenant_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    # Setup Alice
    alice_data = await _register_user(client, "alice_dpdp@example.com", "Alice WS")
    alice_ws_id = uuid.UUID(alice_data["workspace"]["id"])

    # Alice's source, record, and opportunity
    alice_source = DataSource(
        workspace_id=alice_ws_id,
        provider="meta",
        source_type="ad_account",
        display_name="Alice Meta Ad Account",
    )
    db_session.add(alice_source)
    await db_session.commit()
    await db_session.refresh(alice_source)

    alice_rec = SourceRecord(
        source_id=alice_source.id,
        workspace_id=alice_ws_id,
        source_type="meta",
        text_content="Alice private customer data",
    )
    alice_opp = Opportunity(
        workspace_id=alice_ws_id,
        title="Alice Confidential Brief",
    )
    db_session.add_all([alice_rec, alice_opp])
    await db_session.commit()

    # Setup Bob
    client.cookies.clear()
    bob_data = await _register_user(client, "bob_dpdp@example.com", "Bob WS")
    bob_ws_id = uuid.UUID(bob_data["workspace"]["id"])

    # 1. CROSS-TENANT CHECK: Bob cannot view Alice's opportunity
    bob_opp_res = await client.get(
        f"/api/v1/opportunities/{alice_opp.id}",
        headers={"X-Workspace-ID": str(bob_ws_id)},
    )
    assert bob_opp_res.status_code == 403
    assert bob_opp_res.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    # 2. CROSS-TENANT CHECK: Bob cannot delete Alice's source
    bob_del_res = await client.delete(
        f"/api/v1/data/{alice_source.id}",
        headers={"X-Workspace-ID": str(bob_ws_id)},
    )
    assert bob_del_res.status_code == 403
    assert bob_del_res.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    # 3. DPDP PURGE: Alice deletes her own source
    client.cookies.clear()
    # Log back in as Alice
    await client.post(
        "/api/v1/auth/login",
        json={"email": "alice_dpdp@example.com", "password": "SecurePassword123!"},
    )

    del_res = await client.delete(
        f"/api/v1/data/{alice_source.id}",
        headers={"X-Workspace-ID": str(alice_ws_id)},
    )
    assert del_res.status_code == 200
    assert del_res.json()["data"]["status"] == "purged"

    # Verify source row is gone
    check_src = await db_session.get(DataSource, alice_source.id)
    assert check_src is None

    # Verify records are purged
    rec_check = await db_session.execute(
        select(SourceRecord).where(SourceRecord.source_id == alice_source.id)
    )
    assert len(rec_check.scalars().all()) == 0

    # Verify DPDP AuditEvent was logged without storing deleted payload
    audit_res = await db_session.execute(
        select(AuditEvent).where(
            AuditEvent.workspace_id == alice_ws_id,
            AuditEvent.action == "dpdp_source_purge",
        )
    )
    audits = audit_res.scalars().all()
    assert len(audits) == 1
    assert audits[0].metadata_json.get("dpdp_compliant") is True


@pytest.mark.asyncio
async def test_reports_csv_export(client: AsyncClient, db_session: AsyncSession):
    user_data = await _register_user(client, "reports_user@example.com", "Reports WS")
    ws_id = uuid.UUID(user_data["workspace"]["id"])

    # Seed topic and trend
    t = Topic(workspace_id=ws_id, canonical_label="Cold Pressed Juices")
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)

    snap = TrendSnapshot(
        workspace_id=ws_id,
        topic_id=t.id,
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 15),
        mention_count=800,
        momentum_score=Decimal("65.0000"),
        source_count=2,
        confidence="medium",
    )
    db_session.add(snap)
    await db_session.commit()

    # Call GET /reports/export.csv
    res = await client.get(
        "/api/v1/reports/export.csv?report_type=trends",
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")

    csv_text = res.text
    # Verify DPDP compliance header comment
    assert "# Export Generated:" in csv_text
    assert "DPDP Compliant" in csv_text
    assert "Cold Pressed Juices" in csv_text


@pytest.mark.asyncio
async def test_workspace_seed_demo_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
):
    # Setup test workspace
    user_data = await _register_user(client, "demo_seed_user@example.com", "Demo D2C Workspace")
    ws_id = uuid.UUID(user_data["workspace"]["id"])

    # Call POST /api/v1/workspaces/{workspace_id}/seed-demo
    res = await client.post(
        f"/api/v1/workspaces/{ws_id}/seed-demo",
        headers={"X-Workspace-ID": str(ws_id)},
        json={"industry": "Sustainable Fashion & D2C Apparel"},
    )
    assert res.status_code == 201
    body = res.json()
    assert "data" in body
    data = body["data"]
    assert data["workspace_id"] == str(ws_id)
    assert data["topics_seeded"] >= 4
    assert data["trends_seeded"] >= 4
    assert data["audiences_seeded"] >= 2

    # Verify topics and trends appear on dashboard/summary and trends explorer
    dash_res = await client.get(
        "/api/v1/dashboard/summary",
        headers={"X-Workspace-ID": str(ws_id)},
    )
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert dash_data["tracked_topics"] >= 4
    assert dash_data["connected_sources"] >= 1
    assert len(dash_data["top_rising_trends"]) >= 4

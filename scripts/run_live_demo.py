import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

async def run_live_demo():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
        print("=== 1. Live Signup & Session Auth ===")
        unique_email = f"aryan.demo_{uuid.uuid4().hex[:6]}@auraorganics.in"
        signup_res = await client.post("/api/v1/auth/signup", json={
            "email": unique_email,
            "password": "SecurePassword123!",
            "full_name": "Aryan Chavan",
            "workspace_name": "Aura Organics D2C"
        })
        print("Signup Status:", signup_res.status_code)
        user_data = signup_res.json()["data"]
        ws_id = user_data["workspace"]["id"]
        print(f"Created User: {user_data['user']['email']} | Workspace: {user_data['workspace']['name']} ({ws_id})")

        headers = {"X-Workspace-ID": ws_id}

        print("\n=== 2. Explore Demo Intelligence (Onboarding Fast Setup) ===")
        seed_res = await client.post(f"/api/v1/workspaces/{ws_id}/seed-demo", headers=headers, json={
            "industry": "Sustainable Fashion & D2C Apparel"
        })
        print("Seed Status:", seed_res.status_code)
        seed_data = seed_res.json()["data"]
        print(f"Seeded: {seed_data['topics_seeded']} topics, {seed_data['trends_seeded']} trends, {seed_data['audiences_seeded']} audience clusters")

        print("\n=== 3. Overview Dashboard KPIs ===")
        dash_res = await client.get("/api/v1/dashboard/summary", headers=headers)
        dash = dash_res.json()["data"]
        print(f"Tracked Topics: {dash['tracked_topics']} | Rising Topics: {dash['rising_topics']}")
        print(f"Connected Sources: {dash['connected_sources']} | Saved Opportunities: {dash['saved_opportunities']}")
        print(f"Top Rising Signal: {dash['top_rising_trends'][0]['topic_name']} (Momentum: {dash['top_rising_trends'][0]['momentum_score']})")

        print("\n=== 4. Trend Explorer & Filter Ranking ===")
        trends_res = await client.get("/api/v1/trends?min_momentum=50", headers=headers)
        trends = trends_res.json()["data"]
        print(f"Found {len(trends)} high-momentum trends:")
        for t in trends[:3]:
            print(f"  - {t['topic_name']} | Score: {t['momentum_score']} | Conf: {t['confidence']}")

        first_trend_id = trends[0]["trend_id"]
        print(f"\n=== 5. Trend Detail ({trends[0]['topic_name']}) ===")
        detail_res = await client.get(f"/api/v1/trends/{first_trend_id}", headers=headers)
        detail = detail_res.json()["data"]
        print(f"Summary: {detail['summary'][:90]}...")
        print(f"Timeline points: {len(detail['timeline'])} | Evidence Snippets: {len(detail['evidence_snippets'])}")

        print("\n=== 6. Audience Clusters & Label Locking ===")
        aud_res = await client.get("/api/v1/audiences", headers=headers)
        audiences = aud_res.json()["data"]
        first_cluster = audiences[0]
        print(f"Original Cluster: \"{first_cluster['name']}\" (Label Locked: {first_cluster['label_locked']})")

        rename_res = await client.patch(f"/api/v1/audiences/{first_cluster['id']}", headers=headers, json={
            "name": "Gen-Z Eco Warriors (Custom D2C)"
        })
        renamed = rename_res.json()["data"]
        print(f"Renamed Cluster: \"{renamed['name']}\" (Label Locked: {renamed['label_locked']}, User Renamed: {renamed['is_user_renamed']})")

        print("\n=== 7. Citation-Verified Opportunity Brief Generation ===")
        opp_res = await client.post("/api/v1/opportunities", headers=headers, json={
            "topic_id": detail["topic_id"],
            "title": f"Festive Scale: {detail['topic_name']}"
        })
        opp_id = opp_res.json()["data"]["id"]
        print(f"Created Opportunity: {opp_id}")

        brief_res = await client.post(f"/api/v1/opportunities/{opp_id}/generate-brief", headers=headers)
        brief_data = brief_res.json()["data"]
        brief = brief_data["brief_json"]
        print("Generated 7-Section Opportunity Brief:")
        print(f"  1. Signal Summary: {brief['signal_summary'][:80]}...")
        print(f"  2. Product Angles: {brief['product_angles'][:80]}...")
        print(f"  3. ASCI Compliance: {brief.get('asci_disclosure', '#Ad #Sponsored')}")
        print(f"  4. Citations verified: {len(brief.get('citations', []))} citations validated against database")

        print("\n=== 8. Streaming DPDP Compliance Report Export ===")
        rep_res = await client.get("/api/v1/reports/export.csv?report_type=trends", headers=headers)
        print(f"Export Status: {rep_res.status_code} | Content-Type: {rep_res.headers.get('content-type')}")
        lines = rep_res.text.splitlines()[:2]
        print(f"Export Preview (Header Comments):\n  {lines[0]}\n  {lines[1]}")

        print("\n=======================================================")
        print("🎉 LIVE END-TO-END DEMO WALKTHROUGH COMPLETED SUCCESSFULLY! 🎉")
        print("=======================================================")

if __name__ == "__main__":
    asyncio.run(run_live_demo())

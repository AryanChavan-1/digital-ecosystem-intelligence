# Shared API, Database & Job Queue Contract

**Status:** Single Source of Truth (v1.1)  
**Owners:** Aryan Chavan (API & UI) & Unnati Kadam (DB, ETL & ML)

> **Rule:** Neither developer may rename database columns, change `background_jobs` payload keys, or alter `/api/v1` JSON response envelopes without updating this document and notifying the other co-founder.

---

## 1. PostgreSQL Table Ownership Matrix

| Table | Schema Owner | Primary Writer | Primary Reader | Tenant Isolation Column |
| :--- | :--- | :--- | :--- | :--- |
| `users`, `sessions`, `workspaces` | Unnati (DDL) | Aryan (Auth API) | Aryan (Auth Guard) | `workspaces.created_by` |
| `data_sources`, `uploads` | Unnati (DDL) | Aryan (Upload API) & Unnati (Worker) | Both | `workspace_id` (`NULL` if `is_global`) |
| `background_jobs` | Unnati (DDL) | Aryan (API Enqueue) & Unnati (Worker) | Unnati (Worker Runner) | `workspace_id` |
| `campaigns`, `campaign_daily_metrics` | Unnati (DDL) | Aryan (`locale_parser` / CSV task) | Aryan (Campaign API) & Unnati (Brief Context) | `workspace_id` |
| `source_records` | Unnati (DDL) | Unnati (ETL & Embedding Worker) | Unnati (ML) & Aryan (Evidence API) | `workspace_id` (`NULL` if `is_global`) |
| `topics`, `topic_record_assignments` | Unnati (DDL) | Unnati (Topic/Clustering Worker) | Both | `topics.workspace_id` |
| `trend_snapshots` | Unnati (DDL) | Unnati (Momentum Engine) | Aryan (`/trends` & `/dashboard` API) | `workspace_id` |
| `audience_clusters`, `cluster_topics` | Unnati (DDL) | Unnati (HDBSCAN Worker) & Aryan (`PATCH /audiences`) | Both | `workspace_id` |
| `opportunities` | Unnati (DDL) | Unnati (LLM Brief Worker) & Aryan (`PATCH /opportunities`) | Aryan (`/opportunities` API) | `workspace_id` |
| `model_runs`, `audit_events` | Unnati (DDL) | Both | Both | `workspace_id` |

---

## 2. Background Job Queue Contract (`background_jobs`)

Aryan's FastAPI endpoints enqueue tasks by inserting rows into `background_jobs` (`status = 'queued'`). Unnati's `worker/runner.py` claims rows using `SELECT ... FOR UPDATE SKIP LOCKED` and dispatches handlers based on `task_name`.

### Standard `task_name` & `payload` Schemas

1. **`seed_demo_workspace`** (Enqueued by `POST /api/v1/workspaces/{id}/seed-demo`)
   ```json
   { "workspace_id": "uuid", "industry": "sustainable_fashion" }
   ```
2. **`validate_and_ingest_csv`** (Enqueued by `POST /api/v1/uploads/{id}/complete`)
   ```json
   {
     "upload_id": "uuid",
     "workspace_id": "uuid",
     "source_id": "uuid",
     "date_format": "%d/%m/%Y",
     "mapping": {
       "date": "Day",
       "campaign_name": "Campaign Name",
       "channel": "Platform",
       "currency": "Currency",
       "impressions": "Impressions",
       "clicks": "Clicks",
       "spend": "Amount Spent (INR)",
       "conversions": "Purchases",
       "attributed_revenue": "Purchase Conversion Value"
     }
   }
   ```
3. **`recompute_workspace_intelligence`** (Enqueued after CSV ingestion or via nightly cron)
   ```json
   { "workspace_id": "uuid", "window_days": 30 }
   ```
4. **`generate_opportunity_brief`** (Enqueued by `POST /api/v1/opportunities`)
   ```json
   { "opportunity_id": "uuid", "workspace_id": "uuid", "topic_id": "uuid" }
   ```
5. **`cascade_delete_source`** (Enqueued by `DELETE /api/v1/data/{source_id}`)
   ```json
   { "source_id": "uuid", "workspace_id": "uuid" }
   ```

---

## 3. Standard REST Envelopes (`/api/v1`)

### Success Response
```json
{
  "data": {},
  "meta": {
    "request_id": "req_8f92a1",
    "generated_at": "2026-11-14T00:00:00Z"
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "TENANT_ACCESS_DENIED",
    "message": "Resource does not belong to active workspace.",
    "details": {},
    "request_id": "req_8f92a1"
  }
}
```

### Cluster Rename Protection Rule (`audience_clusters`)
* When Aryan's `PATCH /api/v1/audiences/{id}` updates `audience_clusters.name`, it **must** set `is_user_renamed = TRUE`.
* When Unnati's `cluster_topics.py` matches an existing centroid (`cosine_similarity >= 0.85`), it **must not** overwrite `name` if `is_user_renamed = TRUE`.
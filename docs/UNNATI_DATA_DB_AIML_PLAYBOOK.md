# Unnati Kadam — Execution Playbook (Database, Data Engineering & AI/ML)

**Scope:** PostgreSQL 16 + `pgvector` Schema, Alembic Migrations, `SKIP LOCKED` Background Worker, ETL & Anti-Spam Filtering, `all-MiniLM-L6-v2` Embeddings, Dual-Mode Momentum Scoring, HDBSCAN Centroid Clustering, and Citation-Grounded LLM Brief Synthesis.  
**Order of Execution:** Schema & Ground-Truth Benchmark First → Job Worker & ETL → Embeddings & Clustering → Grounded LLM Briefs & Deletion Purge.

---

## Phase 1: PostgreSQL + `pgvector` Schema & Ground-Truth Benchmark (Weeks 1–2)

### Task U1 — Alembic Migrations & `pgvector` Indexes
* **Folder:** `backend/migrations/`
* **Deliverables:**
  1. Enable `pgcrypto`, `citext`, and `vector` extensions in PostgreSQL 16.
  2. Create all 16 core tables defined in `04_DATA_AND_DATABASE.md` and `SHARED_API_AND_DB_CONTRACT.md`:
     * `users`, `sessions`, `workspaces`
     * `data_sources`, `background_jobs` (partial index on `(status, run_after) WHERE status='queued'`), `uploads`
     * `source_records` (with `local_date DATE`, `content_hash`, `spam_score`, `embedding vector(384)`)
     * `campaigns`, `campaign_daily_metrics`
     * `topics` (with nullable `workspace_id` for tenant isolation), `topic_record_assignments`, `trend_snapshots`
     * `audience_clusters` (with `centroid_vector vector(384)` and `is_user_renamed BOOLEAN`), `cluster_topics`
     * `opportunities`, `model_runs`, `audit_events`
  3. Add HNSW index on `source_records.embedding` (`vector_cosine_ops`) for fast similarity search.

### Task U2 — Curate 50-Trend Indian D2C Ground-Truth Benchmark & Demo Seed
* **Folder:** `data_ml/benchmarks/`, `backend/worker/tasks/seed_demo.py`
* **Deliverables:**
  1. Curate 50 labelled Indian D2C topic windows (25 genuine breakout trends + 25 flat/spam baselines) in `data_ml/benchmarks/indian_d2c_50_trends.json`.
  2. Implement `seed_demo_workspace(workspace_id)` worker task to populate realistic demo social posts, trend snapshots, clusters, and INR campaign rows tagged `source_type='demo'`.

---

## Phase 2: `SKIP LOCKED` Worker & Clean ETL Pipeline (Weeks 3–4)

### Task U3 — PostgreSQL Transactional Job Worker (`worker/runner.py`)
* **Folder:** `backend/worker/`
* **Deliverables:**
  1. Build polling worker claiming jobs via `SELECT * FROM background_jobs WHERE status = 'queued' AND run_after <= now() ORDER BY created_at ASC FOR UPDATE SKIP LOCKED LIMIT 1`.
  2. Route `task_name` payloads (`seed_demo_workspace`, `validate_and_ingest_csv`, `recompute_workspace_intelligence`, `generate_opportunity_brief`, `cascade_delete_source`).
  3. Implement retry backoff (`attempts < max_attempts`) and error logging.

### Task U4 — CSV Ingestion Worker, Deduplication & Anti-Spam Filter
* **Folder:** `backend/worker/tasks/ingest_csv.py`, `data_ml/etl/`
* **Deliverables:**
  1. Download uploaded CSV from S3/R2, call Aryan's `locale_parser.py` sanitizers, write invalid rows to `quarantine_object_key` in S3/R2, and bulk-insert valid rows into `campaign_daily_metrics` or `source_records`.
  2. Compute `local_date = (published_at AT TIME ZONE workspace.timezone)::date` so IST (`Asia/Kolkata`) campaigns align with social records.
  3. Compute `content_hash` (SHA-256 of normalized lowercase alphanumeric text) to flag 24h duplicates (`is_duplicate=TRUE`) and score spam (`>15` hashtags, giveaway templates).

---

## Phase 3: Embeddings, Momentum Engine & Stable Clustering (Weeks 5–8)

### Task U5 — `all-MiniLM-L6-v2` Embedding & Keyphrase Pipeline
* **Folder:** `data_ml/embeddings/`
* **Deliverables:**
  1. Load `sentence-transformers/all-MiniLM-L6-v2` (384d) with batch size `32` so peak RAM stays safely under **2.5GB** on a 4GB host.
  2. Generate L2-normalized embeddings for non-duplicate, non-spam `source_records` and persist to `source_records.embedding`.
  3. Extract top 1–3 gram keyphrases via `TF-IDF` / `KeyBERT` to create workspace-scoped `topics`.

### Task U6 — Dual-Mode Momentum Scoring Engine
* **Folder:** `data_ml/trends/`
* **Deliverables:**
  1. Aggregate daily deduplicated counts per `(workspace_id, topic_id, local_date)`.
  2. Compute **Full Multi-Source Momentum** (`S_k = 100 * (0.40 G_k + 0.25 P_k + 0.20 D_k + 0.15 Q_k)`) when `source_count >= 2` and `history_days >= 14`.
  3. Compute **Single-Source Snapshot Score** (`S_k_snapshot = 100 * (0.55 G_k + 0.45 Q_k)`) for Day-1 datasets, setting `scoring_mode='single_source_snapshot'`.
  4. Validate against `indian_d2c_50_trends.json` (`>= 80% Precision@10`) and log metrics to `model_runs`.

### Task U7 — HDBSCAN Clustering with `pgvector` Centroid Alignment
* **Folder:** `data_ml/clustering/`
* **Deliverables:**
  1. Cluster workspace embeddings via `HDBSCAN` (`min_cluster_size=8`, fallback to `K-Means` on small sets); suppress clusters with `< 5` records.
  2. Compute L2-normalized `centroid_vector` (`vector(384)`) and query existing `audience_clusters` via `pgvector` cosine similarity (`1 - (centroid_vector <=> new_centroid)`).
  3. If similarity `>= 0.85`, preserve the existing cluster `UUID` and user-edited `name` (when `is_user_renamed=TRUE`), updating `centroid_vector` via EMA (`0.7 * old + 0.3 * new`).

---

## Phase 4: Grounded LLM Briefs & Cascading DPDP Deletion (Weeks 9–12)

### Task U8 — Citation-Verified LLM Opportunity Brief Generator
* **Folder:** `backend/worker/tasks/draft_brief.py`, `data_ml/synthesis/`
* **Deliverables:**
  1. Fetch `trend_snapshots`, top 10 `source_records` (IDs + snippets), linked `audience_clusters`, and aggregate category `campaign_daily_metrics`.
  2. Call structured JSON LLM API (`temperature=0.2`) to synthesize `signal_summary`, `audience_hypotheses`, `product_gap_hypotheses`, `recommended_experiments` (with ASCI paid-partnership reminders), `risks_and_counter_signals`, and `data_limitations`.
  3. Verify every `[record_id]` cited by the LLM exists in the retrieved context list before saving to `opportunities`.

### Task U9 — Cascading Source Deletion Worker (`cascade_delete_source`)
* **Folder:** `backend/worker/tasks/delete_source.py`
* **Deliverables:**
  1. Delete raw + quarantine files from S3/R2 for `source_id`.
  2. Delete `source_records` and `campaign_daily_metrics` rows, recompute `trend_snapshots` and `audience_clusters`, delete the `data_sources` row, and insert a non-PII `audit_events` record.
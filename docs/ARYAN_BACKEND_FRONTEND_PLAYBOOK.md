# Aryan Chavan — Execution Playbook (Backend API & Frontend)

**Scope:** FastAPI Control Plane, Auth & Tenant Isolation, Locale-Aware CSV Parser, S3/R2 Signed Uploads, REST APIs, and React/Vite Frontend.  
**Order of Execution:** Hardest Backend Security & Ingestion Logic First → API Contract Freeze → Frontend Integration Last.

---

## Phase 1: Backend Foundation, Cookie Auth & Tenant Isolation (Weeks 1–2)

### Task A1 — FastAPI Skeleton, Config & Health Probes
* **Folder:** `backend/app/`
* **Deliverables:**
  1. Set up FastAPI app with `Pydantic v2` settings (`DATABASE_URL`, `S3_ENDPOINT`, `S3_BUCKET`, `SESSION_SECRET`, `FRONTEND_ORIGIN`).
  2. Add structured JSON logging with `request_id` middleware.
  3. Implement `/health/live` and `/health/ready` (verifies PostgreSQL connectivity).

### Task A2 — `HttpOnly` Cookie Auth & Strict Tenant Guard
* **Folder:** `backend/app/auth/`, `backend/app/workspaces/`
* **Deliverables:**
  1. Implement `POST /api/v1/auth/signup`, `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, and `GET /api/v1/me`.
  2. Hash passwords using `Argon2id`. Store random session hashes in `sessions` and set `HttpOnly`, `SameSite=Lax` cookies.
  3. Implement `POST /api/v1/workspaces` (defaults: `market_region='IN'`, `timezone='Asia/Kolkata'`, `default_currency='INR'`).
  4. Write `get_current_workspace` dependency that checks `workspace.created_by == current_user.id` and pass `workspace_id` explicitly to every DB query.

---

## Phase 2: S3 Signed Uploads & Indian Locale CSV Parser (Weeks 3–4)

### Task A3 — Presigned Object Storage Upload Lifecycle
* **Folder:** `backend/app/uploads/`
* **Deliverables:**
  1. `POST /api/v1/uploads`: Creates `uploads` row (`status='created'`), generates UUID `object_key`, and returns a short-lived S3/R2 presigned `PUT` URL.
  2. `POST /api/v1/uploads/{id}/complete`: Verifies uploaded object size (`<= 25MB`) and SHA-256 checksum, saves column `mapping` and `date_format`, updates status to `uploaded`, and inserts a `validate_and_ingest_csv` row into `background_jobs`.
  3. `GET /api/v1/uploads/{id}`: Returns live job status, `rows_accepted`, `rows_quarantined`, and presigned download URL for `quarantine_object_key` if rows failed.

### Task A4 — Indian Locale Sanitizer (`locale_parser.py`) & Campaign Metrics
* **Folder:** `backend/app/core/locale_parser.py`, `backend/app/campaigns/`
* **Deliverables:**
  1. Build reusable sanitizer functions for Unnati's ingestion worker to call:
     * Strip `₹`, `INR`, `$`, `USD`, and Indian/Western commas (`"1,25,450.50"` → `Decimal("125450.50")`).
     * Convert `"--"`, `"-"`, `"N/A"` in optional metrics to `None`.
     * Skip summary rows matching `^(Total|Grand Total|Summary)$`.
     * Parse dates strictly using user-specified `date_format` (`%d/%m/%Y`, `%m/%d/%Y`, `%Y-%m-%d`).
  2. Build `CampaignService` calculating `CTR`, `CPC`, `CPM`, `CPA`, and `ROAS` using `Decimal` arithmetic (`None` on zero denominators).

---

## Phase 3: Complete `/api/v1` REST Layer & Security QA (Weeks 5–8)

### Task A5 — Implement All Intelligence, Brief & Export Endpoints
* **Folder:** `backend/app/api/v1/endpoints/`
* **Deliverables:**
  1. **Dashboard & Trends:** `GET /dashboard/summary`, `GET /trends` (cursor-paginated, filterable by `window_days`, `source_type`, `min_records`), `GET /trends/{id}` (returns timeline + evidence snippets).
  2. **Audiences:** `GET /audiences` and `PATCH /audiences/{id}` (updates `name` and sets `is_user_renamed = TRUE`).
  3. **Sources & DPDP Deletion:** `GET /sources` and `DELETE /data/{source_id}` (immediately sets `status='deleting'` and enqueues `cascade_delete_source` job).
  4. **Opportunities & Exports:** `POST /opportunities` (enqueues `generate_opportunity_brief`), `GET /opportunities`, `GET /opportunities/{id}`, `PATCH /opportunities/{id}`, and `GET /reports/{id}/export.csv` (streaming CSV response).
  5. Export frozen `shared/openapi.yaml` and run adversarial cross-tenant `pytest` suite.

---

## Phase 4: End-to-End Frontend Integration & Print-PDF Polish (Weeks 9–12)

### Task A6 — React + Vite App Shell, Auth & Onboarding
* **Folder:** `frontend/src/`
* **Deliverables:**
  1. Scaffold React 18 + TypeScript + Vite + Tailwind CSS + `shadcn/ui` + TanStack Query.
  2. Build `/login`, `/signup`, and `/onboarding` with 1-click **"Load Demo Dataset"** (`POST /workspaces/{id}/seed-demo`).

### Task A7 — Overview, Trend Explorer & Trend Detail UI
* **Deliverables:**
  1. Build `/app` overview KPIs, freshness banner, and contextual empty states.
  2. Build `/app/trends` with `Multi-Source` vs. `Single-Source Snapshot` badges and `/app/trends/:id` with Recharts timelines and source evidence cards.

### Task A8 — Client-Side CSV Wizard (`PapaParse`) & Campaign Dashboard
* **Deliverables:**
  1. Build `/app/campaigns` upload modal parsing the first 20 rows locally via `PapaParse` before requesting an S3 upload URL.
  2. Flag `₹` symbols, summary rows, and ambiguous `DD/MM/YYYY` vs. `MM/DD/YYYY` dates in the UI preview.
  3. Poll `GET /uploads/{id}` and render `CTR`, `CPC`, `CPM`, `CPA`, `ROAS` (`—` for null).

### Task A9 — Editable Opportunity Briefs, Cluster Rename & `@media print` PDF
* **Deliverables:**
  1. Build `/app/audiences` with inline cluster label editing.
  2. Build `/app/opportunities/:id` with inline section editing, `"AI-Synthesized Draft"` transparency badge, and clickable `[record_id]` evidence links.
  3. Add `@media print` CSS stylesheet to `/app/reports/:id` for clean browser Save-as-PDF exports and wire `DELETE /data/{source_id}` in `/app/sources`.
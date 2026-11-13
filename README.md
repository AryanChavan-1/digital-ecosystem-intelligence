# Digital Ecosystem Intelligence Platform — MVP

An AI-driven market and consumer intelligence platform built specifically for **Indian Direct-to-Consumer (D2C) brands and growth agencies**. It ingests permitted public/licensed signals and user-authorised campaign CSV exports, detects breakout category trends using dual-mode momentum scoring, clusters related interests via `pgvector` centroid alignment, and synthesizes citation-grounded **Opportunity Briefs**.

* **Co-Founder (Frontend & Backend API):** Aryan Chavan
* **Co-Founder (Database, Data Engineering & AI/ML):** Unnati Kadam
* **Architecture:** Modular Monolith (`FastAPI` + `PostgreSQL 16 / pgvector` + `S3/R2` + `React/Vite`)
* **Target Runtime:** 4GB RAM Container Footprint (Railway / Render / AWS Lightsail)

---

## 1. Repository Structure & Ownership

```text
digital-ecosystem-intel/
├── .github/
│   ├── CODEOWNERS                  # Enforces PR review ownership per domain
│   └── workflows/ci.yml            # Automated pytest, ruff, tsc, and vitest checks
├── frontend/                       # [OWNER: Aryan] React 18 + TypeScript + Vite SPA
├── backend/
│   ├── app/                        # [OWNER: Aryan] FastAPI routes, Auth, Services, Locale Parser
│   ├── migrations/                 # [OWNER: Unnati] Alembic PostgreSQL + pgvector schemas
│   └── worker/                     # [OWNER: Unnati] SKIP LOCKED background jobs & ML triggers
├── data_ml/                        # [OWNER: Unnati] Embeddings, Momentum Scoring, Clustering, Benchmarks
├── shared/
│   └── openapi.yaml                # [SHARED] Frozen REST API contract
├── docker-compose.yml              # Local PostgreSQL 16 (pgvector) + API + Worker
├── .env.example                    # Environment template (never commit .env)
└── README.md
```

---

## 2. Quickstart (Local Development)

### Prerequisites
* Docker & Docker Compose
* Python 3.11+ & `uv` (or `pip`)
* Node.js 20+ & `npm`

### Step 1: Clone & Configure Environment
```bash
git clone https://github.com/<your-org>/digital-ecosystem-intel.git
cd digital-ecosystem-intel
cp .env.example .env
```

### Step 2: Start PostgreSQL 16 + `pgvector` & Backend Services
```bash
docker compose up -d db
cd backend
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Step 3: Start the Background Worker (Separate Terminal)
```bash
cd backend
python -m worker.runner
```

### Step 4: Start the React Frontend (Separate Terminal)
```bash
cd frontend
npm install
npm run dev
```
* Frontend runs at `http://localhost:5173`
* FastAPI Swagger UI runs at `http://localhost:8000/docs`

---

## 3. GitHub Branching & Merge-Conflict Prevention Strategy

To prevent merge conflicts while working concurrently, follow these rules strictly:

1. **Branch Hierarchy:**
   * `main`: Protected, production/demo-ready branch. Only merged from `dev` after Sprint QA passes.
   * `dev`: Active integration branch. All feature PRs target `dev`.
   * Feature branches: Prefix with your name and domain:
     * `aryan/backend-auth`, `aryan/backend-csv-upload`, `aryan/frontend-trends`
     * `unnati/db-schema`, `unnati/ml-momentum`, `unnati/ml-clustering`
2. **Domain Isolation:**
   * **Aryan** never edits files inside `data_ml/` or `backend/migrations/` without coordinating via PR.
   * **Unnati** never edits files inside `frontend/` or `backend/app/api/` without coordinating via PR.
   * **Shared Contract:** Any change to database columns, job payloads, or REST JSON schemas must be updated in `SHARED_API_AND_DB_CONTRACT.md` first.
3. **Pull Request Rules:**
   * Never push directly to `main` or `dev`.
   * Every PR must pass `.github/workflows/ci.yml` (`ruff`, `pytest`, `tsc --noEmit`, `vitest`) before merging.
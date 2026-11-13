# Backend Engineering Specification

## Digital Ecosystem Intelligence Platform --- MVP

**Founders:** Unnati Kadam and Aryan Chavan\
**Document owner:** Backend workstream\
**Status:** Build blueprint for MVP\
**Version:** 1.0

------------------------------------------------------------------------

## 1. Backend mission

The backend is the trusted control plane between the frontend, data
stores, ingestion jobs and ML services. It must: 1. Authenticate users
and enforce workspace-level authorization. 2. Receive and validate
permitted data. 3. Orchestrate ingestion and asynchronous processing. 4.
Expose stable APIs for trends, audiences, campaigns and reports. 5.
Store provenance, model versions and processing status. 6. Protect
customer data and provide deletion/export capabilities.

The MVP is a modular monolith, not a microservice fleet. Keep the
codebase separable by domain, but deploy one FastAPI application plus
one background worker initially.

------------------------------------------------------------------------

## 2. Recommended architecture

``` mermaid
flowchart LR
  UI[React frontend] --> API[FastAPI API]
  API --> AUTH[Auth and workspace access]
  API --> PG[(PostgreSQL)]
  API --> OBJ[(Object storage)]
  API --> Q[Job queue]
  Q --> WORKER[Background worker]
  WORKER --> RAW[Raw file validation]
  RAW --> CLEAN[Normalize and clean]
  CLEAN --> PG
  CLEAN --> OBJ
  WORKER --> ML[ML pipeline]
  ML --> PG
  API --> PG
  API --> REPORT[Report generation]
  REPORT --> OBJ
```

### MVP components

-   FastAPI application.
-   PostgreSQL for transactional and analytical metadata.
-   Object storage for uploaded source files and generated exports.
-   Redis + RQ/Celery, or a simpler database-backed job table initially,
    for background work.
-   Background worker for imports, aggregations and model jobs.
-   Structured logging and error monitoring.

### Why modular monolith?

It reduces deployment and debugging overhead for a two-person team.
Split services only when workload, ownership or scaling requires it.

------------------------------------------------------------------------

## 3. Recommended backend stack

  -----------------------------------------------------------------------
  Concern                 MVP choice              Alternatives
  ----------------------- ----------------------- -----------------------
  Language                Python 3.11+            ---

  API                     FastAPI + Pydantic      Django REST Framework

  ORM/migrations          SQLAlchemy 2 + Alembic  Django ORM

  Database                PostgreSQL 16+          Managed PostgreSQL

  Queue                   Redis + RQ              Celery; managed queue

  Object storage          S3-compatible storage   Cloudflare R2, Supabase
                                                  Storage

  Authentication          Secure session cookies; Managed auth provider
                          Argon2 password hashing 

  Validation              Pydantic + Pandera      Great Expectations for
                                                  larger pipelines

  Reports                 HTML template → PDF;    WeasyPrint/Playwright
                          CSV export              PDF

  Testing                 pytest + httpx          ---

  Deployment              Docker                  Managed container
                                                  platform

  Observability           JSON logs +             Managed observability
                          Sentry/OpenTelemetry    
  -----------------------------------------------------------------------

Use managed services when they materially reduce operations burden. Do
not self-host every component for the MVP.

------------------------------------------------------------------------

## 4. Domain modules

``` text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── errors.py
│   ├── api/v1/
│   │   ├── router.py
│   │   └── endpoints/
│   ├── auth/
│   ├── workspaces/
│   ├── sources/
│   ├── uploads/
│   ├── ingestion/
│   ├── trends/
│   ├── audiences/
│   ├── campaigns/
│   ├── opportunities/
│   ├── reports/
│   ├── jobs/
│   ├── models/
│   ├── schemas/
│   └── services/
├── worker/
│   ├── tasks/
│   └── runner.py
├── migrations/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

Keep endpoint handlers thin. Business logic belongs in service modules;
database access belongs in repositories or clearly defined query
functions.

------------------------------------------------------------------------

## 5. API conventions

Base path: `/api/v1`

### Standard response

``` json
{
  "data": {},
  "meta": {
    "request_id": "req_123",
    "generated_at": "2026-11-13T12:00:00Z"
  }
}
```

### Standard error

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The uploaded file is missing the impressions column.",
    "details": {"required_fields": ["impressions"]},
    "request_id": "req_123"
  }
}
```

Use HTTP status codes consistently: - 200/201 successful read/create. -
202 accepted for asynchronous processing. - 400 malformed request. - 401
unauthenticated. - 403 authenticated but not permitted. - 404 missing or
inaccessible resource. - 409 conflict or duplicate idempotency key. -
413 upload too large. - 422 schema validation. - 429 rate limited. - 500
unexpected server error.

### Initial API inventory

  Method   Path                         Description
  -------- ---------------------------- ---------------------------------
  POST     `/auth/signup`               Create account
  POST     `/auth/login`                Authenticate
  POST     `/auth/logout`               End session
  GET      `/me`                        Current user
  POST     `/workspaces`                Create workspace
  GET      `/workspaces`                List memberships
  POST     `/workspaces/{id}/members`   Invite member
  GET      `/sources`                   List configured sources
  POST     `/uploads`                   Create upload record
  POST     `/uploads/{id}/complete`     Finalize object upload
  GET      `/uploads/{id}`              Upload/processing status
  GET      `/trends`                    Search trends
  GET      `/trends/{id}`               Trend details
  GET      `/audiences`                 List interest clusters
  GET      `/campaigns`                 List campaigns
  GET      `/campaigns/{id}/summary`    Campaign metrics
  POST     `/opportunities`             Save opportunity
  GET      `/opportunities`             List saved opportunities
  POST     `/reports`                   Start report generation
  GET      `/reports/{id}`              Report status/download metadata
  DELETE   `/data/{source_id}`          Request source-data deletion

Use pagination (`limit`, `cursor`), filters and stable sorting for list
endpoints. Do not return unbounded datasets.

------------------------------------------------------------------------

## 6. Authentication and authorization

### Authentication

-   Store password hashes using Argon2id or delegate to a reputable
    managed identity provider.
-   Use short-lived sessions and secure, HttpOnly, SameSite cookies.
-   Rotate session identifiers after login and privilege changes.
-   Apply login rate limits and generic error messages to reduce account
    enumeration.
-   Add email verification and password reset before public beta.

### Authorization

Every tenant-owned record must include `workspace_id` or be reachable
only through a workspace-owned parent. For every request: 1. Identify
the authenticated user. 2. Resolve the requested workspace. 3. Verify
active membership and role. 4. Scope every database query to that
workspace. 5. Verify ownership before updates/deletes/downloads.

Roles: - `owner`: billing, members, workspace deletion. - `admin`:
sources, uploads, members, workspace settings. - `analyst`: view data,
create insights and reports. - `viewer`: read-only.

Never rely on a workspace ID supplied by the browser without checking
membership.

------------------------------------------------------------------------

## 7. Upload and ingestion workflow

### CSV upload lifecycle

1.  API creates an upload record and returns a short-lived signed upload
    URL (or accepts a small file directly for local development).
2.  Browser uploads to object storage.
3.  API receives completion request.
4.  Worker checks extension, MIME signature, file size and encoding.
5.  Worker scans/validates file and parses a bounded sample.
6.  User's column mapping is checked against the expected schema.
7.  Worker normalizes fields and writes canonical rows.
8.  Aggregation and ML jobs are enqueued.
9.  Status moves through
    `created → uploaded → validating → processing → completed` or
    `failed`.
10. Frontend polls status or subscribes to notifications.

Never trust client-provided filenames, MIME types, row counts or
workspace IDs. Use generated object keys and strict upload limits. For
the MVP, set configurable limits (e.g. 25 MB and 250,000 rows) and test
memory usage before increasing them.

### Idempotency

Use a unique idempotency key for upload completion and job creation.
Store source checksum, file version and processing version so retries do
not duplicate data.

### Job states

`queued`, `running`, `succeeded`, `failed`, `cancelled`, `retrying`.

Store attempts, timestamps, error code and safe diagnostic message. Do
not expose stack traces to end users.

------------------------------------------------------------------------

## 8. Business logic and service boundaries

-   **SourceService:** records connector permissions, source metadata
    and sync status.
-   **UploadService:** creates uploads, validates mapping and tracks
    lifecycle.
-   **IngestionService:** parses, normalizes and persists records.
-   **TrendService:** retrieves precomputed trend summaries and
    evidence.
-   **AudienceService:** serves cluster summaries and model provenance.
-   **CampaignService:** computes campaign metrics from uploaded data.
-   **OpportunityService:** saves and versions generated briefs.
-   **ReportService:** creates exports and records report provenance.
-   **ModelRegistryService:** records model version, feature version and
    evaluation.

Avoid running heavy ML inference inside a synchronous API request.
Enqueue a job and return 202 with a job ID.

------------------------------------------------------------------------

## 9. Campaign metric calculation

For a campaign with valid denominators: - `CTR = clicks / impressions` -
`CPC = spend / clicks` - `CPM = (spend / impressions) * 1000` -
`CPA = spend / conversions` - `ROAS = attributed_revenue / spend`

Validate that metrics are non-negative and currency is known. Preserve
the original currency and do not combine different currencies without an
explicit conversion rate and timestamp. Missing or zero denominators
produce null, not infinity or fabricated zero.

------------------------------------------------------------------------

## 10. Background jobs and schedules

MVP jobs: - `validate_upload(upload_id)` -
`normalize_campaign_file(upload_id)` -
`aggregate_topic_signals(workspace_id, date_range)` -
`build_trend_features(date_range)` -
`run_trend_detection(model_version, date_range)` -
`cluster_interest_topics(dataset_version)` -
`generate_opportunity_brief(opportunity_id)` -
`generate_report(report_id)` - `delete_source_data(source_id)`

Use batch schedules (e.g. daily) initially. Do not promise streaming or
instant refresh when upstream sources are batch-only.

------------------------------------------------------------------------

## 11. Reliability and observability

Log: - request ID, route, status, duration. - job ID, task name,
duration, outcome. - source ID and dataset version. - model version and
feature version.

Do not log raw user content, secrets, access tokens, passwords or full
uploaded rows.

Monitor: - API latency and error rate. - worker queue depth and job
failures. - database connections and storage. - upload validation
failures. - source freshness. - model pipeline duration and data drift
indicators.

Add health endpoints: - `/health/live`: process is alive. -
`/health/ready`: required dependencies are available.

------------------------------------------------------------------------

## 12. Security and privacy

-   TLS in production; secrets stored in deployment secret manager.
-   Encrypt managed database and object storage at rest.
-   Restrict object access; use short-lived signed URLs.
-   Validate and parameterize all database queries.
-   Apply rate limits and request-size limits.
-   Use dependency scanning and pinned dependencies.
-   Back up PostgreSQL and test restore.
-   Define retention and deletion policies.
-   Keep a data inventory and source-specific lawful basis/permission
    record.
-   Provide a process for data access, correction and deletion requests
    as applicable.
-   Do not ingest private messages, protected profiles or sensitive
    personal data for this product.

Legal review is required before commercial launch. This engineering
document is not legal advice.

------------------------------------------------------------------------

## 13. Deployment topology

Local development: - `frontend` container or Vite dev server. - `api`
FastAPI container. - `worker` container. - `postgres` container. -
`redis` container if using queue. - local object storage emulator or
filesystem adapter.

Production: - frontend static hosting. - API container service. -
separate worker process. - managed PostgreSQL. - managed object
storage. - managed Redis/queue only if needed. - monitoring and backups.

Use separate dev/staging/prod environments and separate credentials. Run
Alembic migrations as a controlled release step.

------------------------------------------------------------------------

## 14. Backend testing strategy

-   Unit tests for metrics, permissions, validation and state
    transitions.
-   Repository tests against a real temporary PostgreSQL database.
-   API tests for authentication, authorization and pagination.
-   Upload tests for malformed, oversized and adversarial CSVs.
-   Tenant-isolation tests: user A must never read workspace B.
-   Worker retry/idempotency tests.
-   Integration tests for object storage and queue.
-   Migration tests from an empty database and previous schema.
-   Load test critical read endpoints with realistic data volume.

Critical security acceptance test: changing a resource ID in a request
must never expose another workspace's data.

------------------------------------------------------------------------

## 15. Backend milestones

  Sprint   Deliverable
  -------- -----------------------------------------------
  1        FastAPI skeleton, config, health, database
  2        Auth, workspace and RBAC
  3        Upload records, object storage and validation
  4        Normalization and campaign metric services
  5        Trend and audience read APIs
  6        Background jobs, report generation
  7        Security, observability, integration tests
  8        Staging, deployment, backups and launch

------------------------------------------------------------------------

## 16. Definition of done

-   API contract documented and versioned.
-   Workspace authorization tested at query level.
-   Input validation and safe error handling implemented.
-   Long-running tasks are asynchronous.
-   Retries are idempotent.
-   Provenance and model versions are stored.
-   Logs exclude secrets and raw personal data.
-   Backups and deletion workflows are tested.
-   Health, metrics and alerting exist for production.

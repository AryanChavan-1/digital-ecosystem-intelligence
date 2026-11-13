# Data Engineering & Database Specification

## Digital Ecosystem Intelligence Platform --- MVP

**Founders:** Unnati Kadam and Aryan Chavan\
**Document owner:** Data engineering and database workstream\
**Status:** Build blueprint for MVP\
**Version:** 1.0

------------------------------------------------------------------------

## 1. Purpose

This document defines where data comes from, what may be collected, how
it enters the platform, how it is validated and stored, how it becomes
analytics-ready, and how it is deleted or exported.

The platform connects signals from social/content ecosystems,
professional/industry context and commercial activity. For MVP, do not
attempt to ingest the whole internet. Start with a small, defensible set
of permitted datasets and one customer workflow.

**Recommended first use case:** trend and audience-interest intelligence
for small D2C brands or marketing agencies, supported by user-authorised
campaign exports.

------------------------------------------------------------------------

## 2. Data acquisition strategy

### Source categories

  ----------------------------------------------------------------------------
  Source category   Example data       MVP acquisition   Constraints
                                       method            
  ----------------- ------------------ ----------------- ---------------------
  Public/open       Public posts,      Dataset download  Check licence,
  datasets          reviews,           with licence      permitted use,
                    product/category   review            attribution and
                    text, research                       redistribution
                    datasets                             

  Official social   Account insights,  Approved official Availability, review,
  platform APIs     media metadata,    API and           rate limits and
                    permitted public   user-authorised   policy can change
                    content            scopes            

  Professional      Industry pages,    Official APIs,    Do not scrape member
  ecosystem         public job/skills  licensed          profiles or
                    aggregates,        providers, public restricted content
                    company-level      reports           
                    signals                              

  Customer campaign Spend,             User-authorised   Customer must have
  data              impressions,       CSV export        rights; handle
                    clicks,                              confidential business
                    conversions,                         data
                    revenue                              

  Brand/product     Product title,     Customer upload   Licence, freshness
  catalogues        category, price,   or licensed feed  and territory
                    attributes                           restrictions

  Search/market     Search interest,   Official/public   Often
  signals           category demand    trend products or sampled/normalized;
                    proxies            licensed provider not absolute demand

  Demo/synthetic    Simulated posts,   Internal          Must be labelled
  data              campaigns and      generator         synthetic; never
                    products                             present as live
                                                         market evidence
  ----------------------------------------------------------------------------

### Important source-access rule

The MVP must not depend on scraping private profiles, private groups,
messages, login-gated pages or bypassing platform controls. Do not
automate around rate limits or access restrictions. Use official APIs,
licensed datasets, user-authorised exports and public datasets whose
terms allow the intended use.

### Practical first data bundle

1.  A curated public/licensed text dataset for a single category.
2.  A small, hand-curated list of public source URLs/records where
    display and processing rights are clear.
3.  A synthetic time-series dataset to test trend logic.
4.  A customer-authorised campaign CSV template.
5.  Optional official API integration only after access approval.

This is enough to build and validate the pipeline before platform
integrations are available.

------------------------------------------------------------------------

## 3. Data-source research checklist

For every source, create a source register entry: - provider and dataset
name. - owner/controller and contact. - source URL or API
documentation. - collection date and terms version. - licence or API
permission. - permitted purposes (internal analysis, commercial use,
model training, display, redistribution). - fields collected. - personal
data categories. - geographic coverage and language. - rate limits and
refresh frequency. - retention/deletion rules. - attribution/display
requirements. - contact for access revocation. - approval status:
`pending`, `approved`, `restricted`, `rejected`.

Do not enable a connector until the required permission and use case are
documented.

------------------------------------------------------------------------

## 4. Ingestion architecture

``` mermaid
flowchart TD
  A1[Official API adapter] --> B[Ingestion gateway]
  A2[Customer CSV upload] --> B
  A3[Licensed/open dataset] --> B
  A4[Demo data generator] --> B
  B --> C[Source registry and permission check]
  C --> D[Raw landing storage]
  D --> E[Schema and quality validation]
  E -->|valid| F[Canonical normalization]
  E -->|invalid| G[Quarantine and error report]
  F --> H[(PostgreSQL canonical tables)]
  F --> I[(Object storage curated files)]
  H --> J[Daily aggregates / feature tables]
  I --> J
  J --> K[Analytics and ML]
  K --> L[(Derived insight tables)]
  L --> M[Backend APIs and dashboards]
```

### Batch first

For MVP, daily or user-triggered batch jobs are simpler, cheaper and
easier to debug. Real-time streaming is not required because: - many
public data sources are rate-limited or batch-oriented. - a daily
refresh is sufficient for early trend discovery. - streaming adds
operational complexity and cost.

Move to streaming only when users demonstrate that delay materially
harms the decision.

------------------------------------------------------------------------

## 5. Storage architecture

### Recommended MVP storage

  -----------------------------------------------------------------------
  Data class              Store                   Reason
  ----------------------- ----------------------- -----------------------
  Users, workspaces,      PostgreSQL              Transactional integrity
  roles                                           

  Source registry and     PostgreSQL              Auditable metadata
  permissions                                     

  Upload metadata and job PostgreSQL              Queryable workflow
  states                                          state

  Normalized records      PostgreSQL initially    Simple joins and
                                                  filters

  Original CSV/API        Object storage          Cheap durable file
  payload files                                   storage

  Large curated datasets  Parquet in object       Columnar analytics and
                          storage                 portability

  Daily aggregates and    PostgreSQL initially    Fast dashboard reads
  feature tables                                  

  Embeddings              PostgreSQL + pgvector   Vector similarity
                          when needed             without separate
                                                  service

  Logs/metrics            Observability service   Operations and
                                                  debugging
  -----------------------------------------------------------------------

Avoid adding a data lakehouse, Kafka, Spark cluster or separate graph
database until actual volume and use cases justify them. For a small
MVP, PostgreSQL + object storage + Parquet is sufficient.

### Storage zones

-   **Raw:** immutable source file/payload snapshot, access restricted,
    retention-limited.
-   **Quarantine:** invalid or suspicious records, short retention,
    restricted access.
-   **Clean:** normalized canonical records.
-   **Curated:** aggregates, features and ML-ready datasets.
-   **Serving:** dashboard-ready insight summaries.

Keep raw source payloads only where permitted and necessary. Some
sources may allow derived aggregates but not long-term storage of
original content.

------------------------------------------------------------------------

## 6. Database design

Use PostgreSQL with UUID primary keys, UTC timestamps, foreign keys and
indexes. Add `workspace_id` to tenant-owned tables. Use migrations and
constraints rather than relying only on application code.

### Core relational entities

``` mermaid
erDiagram
  USER ||--o{ WORKSPACE_MEMBER : joins
  WORKSPACE ||--o{ WORKSPACE_MEMBER : has
  WORKSPACE ||--o{ DATA_SOURCE : configures
  DATA_SOURCE ||--o{ INGESTION_RUN : produces
  DATA_SOURCE ||--o{ SOURCE_RECORD : supplies
  WORKSPACE ||--o{ UPLOAD : owns
  UPLOAD ||--o{ CAMPAIGN_ROW : parses
  WORKSPACE ||--o{ TREND_SNAPSHOT : views
  TOPIC ||--o{ TREND_SNAPSHOT : measured
  TOPIC ||--o{ TOPIC_RELATION : connects
  WORKSPACE ||--o{ OPPORTUNITY : saves
  OPPORTUNITY ||--o{ REPORT : exports
```

### Table definitions (logical schema)

#### `users`

-   `id UUID PK`
-   `email CITEXT UNIQUE NOT NULL`
-   `password_hash TEXT` (nullable if managed auth)
-   `display_name TEXT`
-   `email_verified_at TIMESTAMPTZ`
-   `created_at`, `updated_at TIMESTAMPTZ`

#### `workspaces`

-   `id UUID PK`
-   `name TEXT NOT NULL`
-   `industry TEXT`
-   `market_region TEXT`
-   `default_language TEXT`
-   `created_by UUID FK users`
-   `created_at TIMESTAMPTZ`

#### `workspace_members`

-   `workspace_id UUID FK`
-   `user_id UUID FK`
-   `role TEXT CHECK (role IN ('owner','admin','analyst','viewer'))`
-   `status TEXT`
-   `created_at TIMESTAMPTZ`
-   Primary key: `(workspace_id, user_id)`

#### `data_sources`

-   `id UUID PK`
-   `workspace_id UUID FK`
-   `provider TEXT`
-   `source_type TEXT`
-   `display_name TEXT`
-   `permission_status TEXT`
-   `permission_reference TEXT`
-   `terms_version TEXT`
-   `scopes JSONB`
-   `refresh_mode TEXT`
-   `last_success_at TIMESTAMPTZ`
-   `status TEXT`
-   `created_at TIMESTAMPTZ`

#### `source_records`

-   `id UUID PK`
-   `source_id UUID FK`
-   `external_record_id TEXT`
-   `source_type TEXT`
-   `canonical_url TEXT`
-   `published_at TIMESTAMPTZ`
-   `collected_at TIMESTAMPTZ`
-   `language_code TEXT`
-   `text_content TEXT` (only if retention/display rights permit)
-   `content_hash TEXT`
-   `permission_status TEXT`
-   `metadata JSONB`
-   Unique key: `(source_id, external_record_id)` where available
-   Indexes: `(source_type, published_at)`, `content_hash`, `source_id`

#### `ingestion_runs`

-   `id UUID PK`
-   `source_id UUID FK`
-   `started_at`, `finished_at TIMESTAMPTZ`
-   `status TEXT`
-   `records_received INTEGER`
-   `records_accepted INTEGER`
-   `records_rejected INTEGER`
-   `error_summary TEXT`
-   `pipeline_version TEXT`

#### `uploads`

-   `id UUID PK`
-   `workspace_id UUID FK`
-   `uploaded_by UUID FK users`
-   `object_key TEXT`
-   `original_filename TEXT` (display only; never use as storage key)
-   `checksum_sha256 TEXT`
-   `file_size_bytes BIGINT`
-   `status TEXT`
-   `mapping JSONB`
-   `created_at TIMESTAMPTZ`
-   `completed_at TIMESTAMPTZ`

#### `campaigns`

-   `id UUID PK`
-   `workspace_id UUID FK`
-   `external_campaign_id TEXT`
-   `name TEXT`
-   `channel TEXT`
-   `start_date DATE`
-   `end_date DATE`
-   `currency CHAR(3)`
-   `created_at TIMESTAMPTZ`

#### `campaign_daily_metrics`

-   `id UUID PK`
-   `campaign_id UUID FK`
-   `metric_date DATE`
-   `impressions BIGINT`
-   `clicks BIGINT`
-   `spend NUMERIC(18,4)`
-   `conversions NUMERIC(18,4)`
-   `attributed_revenue NUMERIC(18,4)`
-   `creative_label TEXT`
-   `audience_label TEXT`
-   `source_upload_id UUID FK uploads`
-   Unique key:
    `(campaign_id, metric_date, creative_label, audience_label)`

#### `topics`

-   `id UUID PK`
-   `canonical_label TEXT`
-   `description TEXT`
-   `language_code TEXT`
-   `status TEXT`
-   `created_at TIMESTAMPTZ`

#### `topic_aliases`

-   `id UUID PK`
-   `topic_id UUID FK`
-   `alias TEXT`
-   `language_code TEXT`

#### `topic_record_assignments`

-   `topic_id UUID FK`
-   `source_record_id UUID FK`
-   `assignment_score NUMERIC`
-   `model_version TEXT`
-   Primary key: `(topic_id, source_record_id, model_version)`

#### `trend_snapshots`

-   `id UUID PK`
-   `workspace_id UUID FK`
-   `topic_id UUID FK`
-   `period_start DATE`
-   `period_end DATE`
-   `mention_count BIGINT`
-   `previous_mention_count BIGINT`
-   `change_pct NUMERIC`
-   `momentum_score NUMERIC`
-   `source_count INTEGER`
-   `confidence TEXT`
-   `feature_version TEXT`
-   `model_version TEXT`
-   `generated_at TIMESTAMPTZ`

#### `topic_relations`

-   `source_topic_id UUID FK topics`
-   `target_topic_id UUID FK topics`
-   `relation_type TEXT`
-   `weight NUMERIC`
-   `window_start DATE`
-   `window_end DATE`
-   `model_version TEXT`
-   Primary key:
    `(source_topic_id, target_topic_id, relation_type, window_start)`

#### `audience_clusters`

-   `id UUID PK`
-   `workspace_id UUID FK`
-   `name TEXT`
-   `description TEXT`
-   `dataset_version TEXT`
-   `model_version TEXT`
-   `record_count INTEGER`
-   `quality_score NUMERIC`
-   `created_at TIMESTAMPTZ`

#### `cluster_topics`

-   `cluster_id UUID FK audience_clusters`
-   `topic_id UUID FK topics`
-   `weight NUMERIC`
-   Primary key: `(cluster_id, topic_id)`

#### `opportunities`

-   `id UUID PK`
-   `workspace_id UUID FK`
-   `created_by UUID FK users`
-   `title TEXT`
-   `summary TEXT`
-   `status TEXT`
-   `score NUMERIC`
-   `evidence JSONB`
-   `limitations JSONB`
-   `created_at`, `updated_at TIMESTAMPTZ`

#### `model_runs`

-   `id UUID PK`
-   `model_name TEXT`
-   `model_version TEXT`
-   `dataset_version TEXT`
-   `feature_version TEXT`
-   `started_at`, `finished_at TIMESTAMPTZ`
-   `metrics JSONB`
-   `status TEXT`
-   `code_commit TEXT`

#### `reports`

-   `id UUID PK`
-   `workspace_id UUID FK`
-   `opportunity_id UUID FK`
-   `created_by UUID FK users`
-   `object_key TEXT`
-   `format TEXT`
-   `status TEXT`
-   `generated_at TIMESTAMPTZ`

#### `audit_events`

-   `id UUID PK`
-   `workspace_id UUID`
-   `actor_user_id UUID`
-   `action TEXT`
-   `resource_type TEXT`
-   `resource_id UUID`
-   `created_at TIMESTAMPTZ`
-   `metadata JSONB` (no secrets or raw sensitive payloads)

------------------------------------------------------------------------

## 7. Data normalization rules

### Canonical timestamps

-   Store timestamps in UTC (`TIMESTAMPTZ`).
-   Preserve original timezone or source offset when available.
-   Do not infer a precise timestamp from a date-only record.

### Text

-   Store original text only if permitted.
-   Keep normalized text in a separate derived field/table.
-   Record language code and preprocessing version.
-   Do not silently translate text; store translation and model/version
    separately if introduced.

### Currency and numbers

-   Store currency as ISO 4217 code.
-   Store spend/revenue in `NUMERIC`, not floating-point.
-   Keep original values and currency.
-   Convert only with an explicit FX rate, provider, timestamp and
    methodology.

### Deduplication

-   Prefer provider record ID.
-   Otherwise use normalized URL + content hash + timestamp window.
-   Keep duplicate decisions auditable.
-   Avoid deleting similar but genuinely distinct records based only on
    text similarity.

------------------------------------------------------------------------

## 8. Data quality checks

For every ingestion run, record: - row/record count received. - accepted
and rejected counts. - required-field completeness. - timestamp parse
rate. - duplicate rate. - language distribution. - invalid numeric
values. - out-of-range values. - source coverage and freshness. - schema
version.

Quarantine invalid rows and provide a downloadable error report that
identifies row number and reason without exposing other customers' data.

### Example campaign CSV template

``` csv
date,campaign_name,channel,currency,impressions,clicks,spend,conversions,attributed_revenue
2026-10-01,Autumn Launch,Instagram,INR,12000,360,8500,18,42000
2026-10-02,Autumn Launch,Instagram,INR,14500,410,9100,21,51000
```

These are illustrative values only. The customer should export data from
an account they are authorised to access.

------------------------------------------------------------------------

## 9. Analytics-ready data products

Build these derived datasets: - `daily_topic_volume`: topic, date,
count, source count. - `topic_period_features`: rolling means, growth,
persistence, volatility. - `trend_rankings`: score, confidence, source
coverage, model version. - `topic_cooccurrence`: related topic pairs and
weights. - `interest_cluster_summary`: cluster, top topics, size,
quality. - `campaign_performance_daily`: spend, impressions, clicks,
conversions, revenue and computed rates. - `opportunity_evidence`:
ranked signals and references.

Precompute these datasets on a schedule. Dashboards should read prepared
summaries, not scan all raw data for every page view.

------------------------------------------------------------------------

## 10. Retention, deletion and governance

Create a retention schedule by source and data type. Retention must
respect: - provider/API terms. - dataset licence. - customer contract. -
legal requirements. - purpose limitation and data minimisation.

Deletion workflow: 1. User/admin requests deletion of a source or
workspace. 2. Backend marks deletion request and blocks new processing.
3. Worker removes raw objects, canonical rows and derived data
attributable to that source where feasible. 4. Recompute affected
aggregates if they contain deleted records. 5. Remove or expire
embeddings and cached reports derived from deleted content. 6. Record a
deletion audit event without retaining the deleted payload. 7. Confirm
completion to the user.

Backups have a documented expiry schedule; deletion from live systems
does not imply instant removal from immutable backups. Explain this in
policy and operational procedures.

------------------------------------------------------------------------

## 11. Privacy and India-specific readiness

The platform may process personal data when source records or customer
uploads contain identifiable individuals. Before public commercial
launch: - map data flows and roles (data fiduciary/controller and
processor roles as applicable). - determine lawful purpose and
notice/consent requirements with qualified counsel. - minimise personal
data and avoid sensitive profiling. - provide access, correction,
erasure and grievance workflows as applicable. - document processors,
hosting regions, cross-border transfers and security controls. - assess
the current status and applicability of India's Digital Personal Data
Protection Act, rules and commencement notifications at launch time. -
review platform terms and API policies separately from privacy law.

This is an engineering readiness checklist, not legal advice. Laws,
rules, commencement dates and platform terms can change.

------------------------------------------------------------------------

## 12. Database indexes and performance

Initial indexes: - `workspace_members(user_id, workspace_id)` -
`data_sources(workspace_id, status)` -
`source_records(source_id, published_at)` -
`source_records(content_hash)` - `campaigns(workspace_id, start_date)` -
`campaign_daily_metrics(campaign_id, metric_date)` -
`trend_snapshots(workspace_id, period_end, momentum_score DESC)` -
`opportunities(workspace_id, updated_at DESC)` -
`uploads(workspace_id, created_at DESC)`

Use `EXPLAIN ANALYZE` on slow queries. Add composite indexes based on
observed query patterns. Partition only when table size and query plans
justify it.

------------------------------------------------------------------------

## 13. Backup and recovery

-   Enable managed PostgreSQL backups and point-in-time recovery where
    available.
-   Version object storage or maintain controlled backup copies.
-   Define recovery point objective (RPO) and recovery time objective
    (RTO).
-   Test restore at least once before launch and periodically
    thereafter.
-   Restrict backup access and apply retention limits.
-   Do not store production secrets in repository or backup manifests.

------------------------------------------------------------------------

## 14. Data engineering milestones

  Sprint   Deliverable
  -------- -----------------------------------------------------------
  1        Source register, source eligibility and CSV contract
  2        PostgreSQL schema and migrations
  3        Object storage and upload landing zone
  4        Validation, quarantine and canonical normalization
  5        Daily aggregates and campaign analytics tables
  6        ML feature tables and provenance
  7        Retention, deletion, audit and backup workflows
  8        Performance checks, restore test and production readiness

------------------------------------------------------------------------

## 15. MVP acceptance criteria

-   Every source has documented permission, licence and intended use.
-   No restricted/private data is collected.
-   Every record can be traced to a source and ingestion run.
-   Raw, clean, curated and serving layers are logically separated.
-   Uploads are validated and invalid rows quarantined.
-   Campaign metrics are reproducible and currency-aware.
-   Trend and feature tables include data/model versions.
-   Tenant isolation is enforced.
-   Retention and deletion workflows are tested.
-   Database backup and restore are demonstrated.
-   Dashboard results disclose source coverage and freshness.

------------------------------------------------------------------------

## 16. Practical data build order

1.  Build the schema and source registry before connecting any external
    provider.
2.  Create a synthetic dataset to test the end-to-end system.
3.  Add one properly licensed/open dataset for the selected vertical.
4.  Implement a customer-authorised campaign CSV upload.
5.  Build daily aggregation and trend features.
6.  Validate the results with a small set of human-reviewed examples.
7.  Add one official API integration only when access is approved and
    its terms are understood.
8.  Add additional sources only when they improve a customer decision
    enough to justify their cost and compliance burden.

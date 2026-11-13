# Frontend Engineering Specification

## Digital Ecosystem Intelligence Platform --- MVP

**Founders:** Unnati Kadam and Aryan Chavan\
**Document owner:** Frontend workstream\
**Status:** Build blueprint for MVP\
**Version:** 1.0

------------------------------------------------------------------------

## 1. Purpose and product boundary

The frontend is the customer-facing workspace for a digital intelligence
product that combines permitted social/content signals,
professional/industry context, creator and brand information, and
commercial/campaign data.

The MVP should solve one narrow, useful problem first:

> Help a small D2C brand or marketing agency discover rising topics in a
> chosen market, understand the audience and evidence behind those
> topics, and turn the findings into a practical campaign or content
> brief.

The UI must not imply that it can see all Instagram or LinkedIn
activity. It must clearly show the source, date range, coverage, and
limitations of every insight.

### MVP users

-   **Brand/marketing analyst:** explores trends and exports a concise
    opportunity report.
-   **Agency strategist:** compares topics, audience segments and
    creator candidates.
-   **Workspace admin:** connects permitted data sources, uploads
    campaign exports and manages team access.

### Explicitly out of scope for the first release

-   Private user profiles, private messages, or non-public engagement
    data.
-   Automated posting, ad buying, or contacting creators.
-   A universal cross-platform identity graph that claims to identify
    the same person across services.
-   Real-time global trend monitoring.
-   Predicting an individual person's purchases or sensitive traits.

------------------------------------------------------------------------

## 2. Core user journeys

### Journey A --- First-time workspace setup

1.  User signs up and verifies their email.
2.  User creates a workspace and selects an industry (initial focus: D2C
    / consumer brands).
3.  User chooses market, language and topics of interest.
4.  User sees available data connectors and their access requirements.
5.  User may upload a permitted CSV export or use clearly labelled
    sample data.
6.  The platform validates the upload and shows row counts, date
    coverage, rejected rows and warnings.
7.  User lands on the Overview dashboard with a guided checklist.

**Success condition:** a first-time user can reach a populated sample or
own-data dashboard in under 10 minutes.

### Journey B --- Discover an emerging opportunity

1.  User opens **Trend Explorer**.
2.  Filters by industry, market, date range, source and topic.
3.  Sees ranked topics with momentum, volume, source coverage and
    confidence.
4.  Opens a topic to inspect evidence: representative public content
    snippets or aggregated records, trend history and related terms.
5.  Opens **Opportunity Brief** to see audience hypotheses, related
    products/categories and possible campaign angles.
6.  User saves the opportunity, adds notes and exports a report.

**Success condition:** user can move from a topic to an evidence-backed
brief without needing to understand ML terminology.

### Journey C --- Understand audience segments

1.  User opens **Audience Insights**.
2.  Selects a topic or uploaded campaign.
3.  Reviews aggregated clusters based on permitted content/topic
    interactions or campaign-level attributes.
4.  Sees segment labels, distinguishing interests, sample size and
    confidence/limitations.
5.  Compares segments and exports a planning summary.

The UI must call these *interest clusters* or *audience hypotheses*
unless the data truly represents a validated customer segment. Do not
claim demographic identity from text or infer sensitive attributes.

### Journey D --- Evaluate a campaign

1.  User uploads an authorised campaign performance CSV.
2.  Frontend previews columns and asks the user to map them to standard
    fields.
3.  Backend validates and processes the data.
4.  User sees spend, impressions, clicks, CTR, CPC, conversions, CPA and
    ROAS where the uploaded file contains the required fields.
5.  User compares campaign performance by date, channel, creative or
    audience label.
6.  User sees descriptive insights and, only where enough history
    exists, a cautious forecast.

### Journey E --- Export and collaborate

1.  User saves an insight to a workspace board.
2.  Adds notes, owner and due date.
3.  Generates a PDF/CSV report.
4.  Shares it with workspace members using role-based access.

------------------------------------------------------------------------

## 3. Information architecture

  --------------------------------------------------------------------------------
  Area              Route                      Purpose           MVP
  ----------------- -------------------------- ----------------- -----------------
  Authentication    `/login`, `/signup`        Secure access     Yes

  Onboarding        `/onboarding`              Workspace,        Yes
                                               market, interests 

  Overview          `/app`                     Key signals and   Yes
                                               recent work       

  Trend Explorer    `/app/trends`              Search and rank   Yes
                                               topics            

  Trend detail      `/app/trends/:id`          Evidence,         Yes
                                               history, related  
                                               terms             

  Opportunity Brief `/app/opportunities/:id`   Convert signals   Yes
                                               into action       

  Audience Insights `/app/audiences`           Explain interest  Yes, basic
                                               clusters          

  Campaign          `/app/campaigns`           Upload and        Yes
  Analytics                                    analyse campaign  
                                               exports           

  Data Sources      `/app/sources`             Connector status, Yes
                                               upload and        
                                               provenance        

  Saved Board       `/app/saved`               Saved insights    Yes
                                               and notes         

  Reports           `/app/reports`             Export reports    Yes

  Settings          `/app/settings`            Team,             Basic
                                               preferences,      
                                               privacy           

  Creator matching  `/app/creators`            Match creators to Later
                                               campaign briefs   

  Graph explorer    `/app/graph`               Explore entity    Later
                                               relationships     
  --------------------------------------------------------------------------------

### Global navigation

-   Overview
-   Discover: Trends, Audiences, Opportunities
-   Measure: Campaigns, Reports
-   Workspace: Saved, Data Sources, Settings

Use a persistent left sidebar on desktop and a compact responsive
navigation on mobile.

------------------------------------------------------------------------

## 4. Screen specifications

### 4.1 Overview dashboard

**Purpose:** answer "what should I look at first?"

Components: - Date range selector. - Market and industry filters. - KPI
cards: tracked topics, rising topics, saved opportunities, connected
data sources. - Rising topics table with momentum and coverage. - "Why
this is rising" evidence panel. - Recent campaign performance summary,
if campaign data exists. - Data freshness indicator and source coverage
notice.

Do not show a KPI if its input data is absent. Use an empty state with a
useful next action.

### 4.2 Trend Explorer

Filters: - Topic/search query. - Industry/category. - Market/region. -
Source. - Time window (7/30/90 days). - Minimum observation count.

Table columns: - Topic. - Current volume (or normalized mention
count). - Change versus prior comparable period. - Momentum score
(0--100, model-defined). - Source coverage. - Confidence label. - Last
updated.

A trend score must be labelled as a platform-derived ranking, not a
probability of commercial success. Clicking a row opens Trend Detail.

### 4.3 Trend Detail

Sections: 1. Summary in plain language. 2. Trend timeline and comparison
period. 3. Source breakdown. 4. Related terms and co-occurring topics.
5. Representative evidence, respecting source licences and display
rules. 6. Audience/interest clusters. 7. Potential commercial relevance,
clearly marked as a hypothesis. 8. "Create opportunity brief" action.

Each chart should show the date range, units, source and missing-data
notes.

### 4.4 Opportunity Brief

A generated brief should include: - Opportunity title. - Signal
summary. - Evidence and source coverage. - Likely audience interests
(not personal identity claims). - Relevant product/category
hypotheses. - Suggested content/campaign experiments. - Risks and
counter-signals. - Confidence and data limitations. - Links to
underlying trend and campaign records.

The user must be able to edit the brief. AI-generated text must be
labelled and traceable to evidence.

### 4.5 Audience Insights

Show: - Number of records included. - Cluster name (human-readable,
editable). - Top terms/topics. - Relative size. - Distinguishing
signals. - Stability/quality indicator. - "How this was created"
explanation.

Do not display sensitive demographic inference. Suppress small groups
where re-identification risk exists.

### 4.6 Campaign Analytics

Upload wizard: 1. Select CSV. 2. Preview first 20 rows. 3. Map columns.
4. Validate currency, dates and numeric fields. 5. Confirm upload and
processing. 6. Show summary and warnings.

Core metrics: - CTR = clicks / impressions. - CPC = spend / clicks. -
CPM = spend / impressions × 1,000. - CPA = spend / conversions. - ROAS =
attributed revenue / spend.

Guard against division by zero and display "---" when a denominator or
required field is missing. Explain attribution assumptions; ROAS from
user-uploaded exports is not independently verified.

### 4.7 Data Sources

Cards for: - CSV upload. - Public/open dataset import (admin/developer
enabled). - Official API connector (only after credentials and
permission are configured). - Demo dataset.

Each card shows: - Connected / needs setup / paused / error. - Last
successful sync. - Data categories collected. - Permission/scope
summary. - Disconnect/delete controls where applicable.

### 4.8 Saved Board and Reports

-   Saved opportunity cards.
-   Notes, owner, tags and status.
-   Export as PDF/CSV.
-   Include report generated-at timestamp and data coverage statement.

------------------------------------------------------------------------

## 5. Recommended frontend stack

  -----------------------------------------------------------------------
  Layer                   Recommendation          Reason
  ----------------------- ----------------------- -----------------------
  Framework               React + TypeScript +    Familiar, fast
                          Vite                    iteration

  UI                      Tailwind CSS +          Accessible reusable
                          shadcn/ui or Radix      components

  Routing                 React Router            Simple route-based
                                                  application

  Server state            TanStack Query          Caching, retries,
                                                  loading states

  Forms                   React Hook Form + Zod   Validated forms and
                                                  upload mapping

  Charts                  Recharts                Accessible,
                                                  React-native charts

  Tables                  TanStack Table          Filtering, sorting and
                                                  pagination

  Auth                    Backend-issued secure   Avoid storing
                          session cookie          long-lived tokens in
                                                  localStorage

  Testing                 Vitest + React Testing  Unit, component and
                          Library + Playwright    end-to-end tests

  Hosting                 Vercel or Cloudflare    Simple static frontend
                          Pages                   deployment
  -----------------------------------------------------------------------

Use the existing React/Vite/Tailwind/Recharts familiarity if available,
but keep the API contract independent of the framework.

------------------------------------------------------------------------

## 6. Frontend project structure

``` text
frontend/
├── public/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── providers.tsx
│   ├── api/
│   │   ├── client.ts
│   │   ├── trends.ts
│   │   ├── campaigns.ts
│   │   ├── sources.ts
│   │   └── reports.ts
│   ├── components/
│   │   ├── layout/
│   │   ├── charts/
│   │   ├── tables/
│   │   ├── feedback/
│   │   └── upload/
│   ├── features/
│   │   ├── auth/
│   │   ├── onboarding/
│   │   ├── overview/
│   │   ├── trends/
│   │   ├── opportunities/
│   │   ├── audiences/
│   │   ├── campaigns/
│   │   ├── sources/
│   │   └── reports/
│   ├── hooks/
│   ├── lib/
│   ├── types/
│   ├── styles/
│   └── main.tsx
├── tests/
├── .env.example
├── package.json
└── README.md
```

### Environment variables

``` bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_ENV=development
```

Never place API secrets, database credentials, private access tokens or
signing keys in `VITE_*` variables. Vite exposes these values to the
browser bundle.

------------------------------------------------------------------------

## 7. API integration contract

All requests should use a shared client with: - Base URL from
environment. - Credentials included for secure cookie auth. - Request
IDs for tracing. - Consistent error parsing. - Timeout and retry
policy. - No automatic retry for non-idempotent writes unless an
idempotency key is used.

Example TypeScript types:

``` ts
export type TrendSummary = {
  id: string;
  topic: string;
  periodStart: string;
  periodEnd: string;
  currentVolume: number;
  previousVolume: number | null;
  changePct: number | null;
  momentumScore: number;
  coverageSources: string[];
  confidence: "low" | "medium" | "high";
  updatedAt: string;
};

export type ApiError = {
  code: string;
  message: string;
  requestId?: string;
  details?: Record<string, unknown>;
};
```

### Initial endpoints

  Method   Endpoint                    Purpose
  -------- --------------------------- ---------------------------
  POST     `/auth/signup`              Create account
  POST     `/auth/login`               Start session
  POST     `/workspaces`               Create workspace
  GET      `/dashboard/summary`        Overview cards
  GET      `/trends`                   Search/filter trends
  GET      `/trends/{id}`              Trend detail
  POST     `/uploads`                  Create upload
  POST     `/uploads/{id}/confirm`     Confirm validated mapping
  GET      `/campaigns`                List campaigns
  GET      `/campaigns/{id}/summary`   Campaign metrics
  POST     `/opportunities`            Save opportunity
  GET      `/reports/{id}`             Report metadata
  POST     `/reports`                  Generate report

------------------------------------------------------------------------

## 8. UX states and accessibility

Every data screen must implement: - Loading skeleton. - Empty state. -
Error state with retry. - Partial-data state. - Stale-data warning. -
Permission/upgrade state if relevant.

Accessibility requirements: - Keyboard navigation for all controls. -
Visible focus indicators. - Semantic headings and landmarks. - Form
labels and error descriptions. - Charts with text summaries or
accessible data tables. - Sufficient colour contrast; do not use colour
alone to encode status. - Responsive layout at 360px, tablet and desktop
widths.

------------------------------------------------------------------------

## 9. Security and privacy requirements

-   Do not store session tokens in localStorage.
-   Use HTTPS in production.
-   Use secure, HttpOnly, SameSite cookies where cookie auth is
    selected.
-   Enforce workspace membership on the backend; frontend hiding is not
    security.
-   Validate file size/type client-side for UX and again server-side for
    security.
-   Never render uploaded CSV cells as raw HTML.
-   Do not log secrets, raw personal data or uploaded row contents.
-   Provide user-facing data source, purpose, retention and deletion
    information.
-   Show the data provenance for insights and the date they were
    computed.

------------------------------------------------------------------------

## 10. Delivery plan

  -----------------------------------------------------------------------
  Sprint                  Frontend deliverable    Acceptance criteria
  ----------------------- ----------------------- -----------------------
  1                       App shell, routing,     Routes work; responsive
                          auth screens            shell

  2                       Onboarding and data     Workspace and
                          source page             sample-data flow works

  3                       Overview and Trend      Filters,
                          Explorer                loading/error/empty
                                                  states

  4                       Trend Detail and        Evidence and provenance
                          Opportunity Brief       visible

  5                       Campaign CSV upload and Mapping, validation and
                          dashboard               metrics work

  6                       Audience page, saved    Save/export flows work
                          board, reports          

  7                       Accessibility, security Critical journeys pass
                          review, E2E tests       

  8                       Production polish and   Deployed MVP with
                          launch                  telemetry
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 11. Definition of done

A frontend feature is done only when: - It uses the documented API
contract. - It has loading, empty, error and partial-data states. - It
works on mobile and desktop. - It is keyboard accessible. - It does not
expose secrets or bypass backend authorization. - It displays data
source and freshness where relevant. - It has tests for its critical
behaviour. - Product copy does not overstate data coverage or model
certainty.

------------------------------------------------------------------------

## 12. Frontend launch checklist

-   [ ] Sign-up/login and logout work.
-   [ ] Workspace switching respects membership.
-   [ ] Demo data is clearly labelled.
-   [ ] CSV upload preview and validation are understandable.
-   [ ] Trend rankings show method, coverage and freshness.
-   [ ] Opportunity brief is editable and evidence-linked.
-   [ ] Campaign metrics handle missing values and zero denominators.
-   [ ] Reports state date range and source limitations.
-   [ ] Mobile and keyboard flows are tested.
-   [ ] Production environment contains no client-side secrets.

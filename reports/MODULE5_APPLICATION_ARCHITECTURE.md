# MODULE 5 — PHASE 9B.1: APPLICATION ARCHITECTURE SPECIFICATION
## PAIMANA PREDICTIVE RISK INTELLIGENCE
### Full-Stack Technical Architecture, Component Contracts, and Build Blueprint

---

# 1. System Overview

**PAIMANA Predictive Risk Intelligence** is a specialized, web-based decision-support platform designed for central infrastructure project surveillance (Ministry of Statistics and Programme Implementation — MoSPI).

The core mission of the platform is to transition public capital expenditure oversight from retrospective accounting into prospective, early-warning risk management. Rather than simply plotting accrued expenditures and historical delays, PAIMANA applies machine learning models to Point-in-Time (PIT) administrative snapshots, surfacing statistical vulnerabilities across prospective cost escalation and schedule slippage horizons.

To maintain absolute scientific rigor, auditability, and governance compliance, the system maintains strict separation across four distinct informational strata:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. OBSERVED DATA                                                            │
│    Verifiable administrative facts reported by CPSEs/MoSPI                  │
│    (Sanctioned cost, cumulative expenditure, physical progress %, dates)    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. MODEL-DERIVED INTELLIGENCE                                               │
│    Prospective statistical probabilities & sensitivity attributions         │
│    (Cost risk probability P_c, schedule risk probability P_s, MDI, delta)   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. RULE-DERIVED INTERVENTIONS                                               │
│    Deterministic operational logic translating risk into action             │
│    (Attention score, quantile tiers, 7 controlled monitoring protocols)     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. PRESENTATION & API LAYER                                                 │
│    RESTful JSON services & responsive UI client dashboards                  │
│    (7 OpenAPI endpoints, 5 React dashboard screens, coverage badges)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. High-Level System Architecture

The application adopts a clean, decoupled three-tier architecture connecting an offline intelligence engine with real-time web clients through an application data store and REST API services:

```mermaid
flowchart TD
    subgraph OfflineIntelligence ["Offline Intelligence Layer (Frozen)"]
        F1["Canonical Source Snapshots (Tables 7, 4, 6)"]
        F2["Longitudinal Snapshot Panel & Identity Map"]
        F3["PIT Features Cohort (N=437, July 2025 Cutoff)"]
        F4["Random Forest Scoring Engine (Cost & Schedule)"]
        F5["Local Explainability Engine (Marginal Reference Perturbation)"]
        F6["Intervention Prioritisation Rule Engine"]
        F1 --> F2 --> F3 --> F4 --> F5 --> F6
    end

    subgraph DataStore ["Application Data Layer (PostgreSQL 15+)"]
        T1[("projects (Metadata)")]
        T2[("project_risk_scores (Probabilities & Tiers)")]
        T3[("project_risk_explanations (Top 3 Drivers & Facts)")]
        T4[("project_intervention_priorities (Actions & Protocols)")]
    end

    subgraph BackendServices ["Backend API Layer (FastAPI / Python 3.11+)"]
        R1["Router / Endpoint Handlers (7 REST Routes)"]
        R2["Domain Service Layer & DTO Mappers"]
        R3["Pydantic v2 Validation & Response Schemas"]
        R4["SQLAlchemy ORM / Data Access Layer"]
        R1 --> R2 --> R3 --> R4
    end

    subgraph FrontendClients ["Frontend UI Layer (React 18 / Vite / TypeScript)"]
        UI1["Portfolio Overview Dashboard"]
        UI2["Risk Ranking Table (Leaderboard)"]
        UI3["Project Detail Profile"]
        UI4["Explainable Risk Drivers Panel"]
        UI5["Intervention Action Panel"]
    end

    F3 & F4 & F5 & F6 -->|One-Time Seed / ETL Ingestion| DataStore
    DataStore <-->|Connection Pool / SQL Queries| R4
    BackendServices <-->|HTTP / JSON (REST API)| FrontendClients
```

### Critical Operational Boundary: No Live Model Retraining
The live application **DOES NOT retrain ML models** when users browse, search, or inspect projects on the dashboard. Model fitting, feature engineering, and probability estimation are performed strictly offline within the deterministic Module 3–4 pipeline. The web backend operates strictly as an ultra-low-latency query and aggregation layer over frozen, pre-computed intelligence stored in the relational database.

---

# 3. Technology Stack Recommendations

The following technology stack is proposed for the Module 5 MVP implementation. These selections prioritize type safety, developer velocity, execution performance, and native alignment with the existing Python data science codebase.

### 3.1 Frontend Web Client
* **Framework**: **React 18** with **Vite** build tooling (fast HMR, lightweight bundle size).
* **Language**: **TypeScript 5.x** (strict type safety matching OpenAPI schemas).
* **Styling**: **Tailwind CSS 3.x** (utility-first, responsive layouts, consistent color coding for attention tiers).
* **Routing**: **React Router v6** (declarative client-side routing between portfolio, leaderboard, and detail views).
* **Data Fetching & State**: **TanStack Query (React Query v5)** + **Axios** (automatic caching, background refetching, loading states).
* **Visualizations**: **Recharts** (composable SVG charts for attention distributions, gauge cards, and feature impact bars).
* **Icons & UI Primitives**: **Lucide React** + **Radix UI** primitives (accessible modals, tooltips, dropdowns).

### 3.2 Backend REST API Services
* **Framework**: **FastAPI 0.110+** (high performance ASGI, automatic OpenAPI/Swagger documentation, native async).
* **Language & Runtime**: **Python 3.11+** with **Uvicorn** ASGI server.
* **Schema Validation**: **Pydantic v2** (ultra-fast C-based validation matching product contracts).
* **ORM & Database Client**: **SQLAlchemy 2.0+** (async-capable session management, robust query construction).
* **API Documentation**: Auto-generated interactive Swagger UI (`/docs`) and Redoc (`/redoc`).

### 3.3 Database & Storage Layer
* **RDBMS**: **PostgreSQL 15+** (ACID compliance, robust numeric precision for coordinates and costs, native JSON support).
* **Migration Tool**: **Alembic** (declarative schema migration management).

### 3.4 AI / Data Modeling Foundation
* **Runtime**: Existing Python + **scikit-learn 1.4+**, **pandas 2.2+**, **numpy 1.26+**.
* **Role**: Preserved as the offline data engineering, scoring, and explainability generator.

### 3.5 Version Control & Collaboration
* **VCS**: **Git** / **GitHub** (maintaining commit lineage, branch protection, and reproducible CI test runs).

*(Note: These stack selections represent implementation blueprints for Module 5; no application code has been generated in Phase 9B.1).*

---

# 4. End-to-End Data Flow

The complete data lifecycle bridges historical administrative reporting and web client delivery across 11 sequential stages:

```
[STAGES 1–8: COMPLETE & FROZEN IN MODULES 1–4]
1. MoSPI / PAIMANA Raw Source Data (June 2025 Table 7, July 2025 Table 4, July 2026 Table 6)
   │
2. Canonical Extraction & Cleaning (Standardized currencies, dates, physical metrics)
   │
3. Identity Resolution (Deterministic ID pairing, multi-snapshot link, review flags)
   │
4. Longitudinal Snapshot Panel (4,161 snapshot observations across 3,633 projects)
   │
5. Point-in-Time (PIT) Feature Cohort (437 projects; July 31, 2025 cutoff; July 2026 targets)
   │
6. Machine Learning Scoring (Random Forest Cost Overrun >5% & Schedule Slippage >=3M models)
   │
7. Explainable Driver Generation (Top 3 marginal reference perturbation signals & source facts)
   │
8. Intervention Prioritisation (Controlled 7-action taxonomy & evidence linking)
   │
   ▼
[STAGES 9–11: FUTURE MODULE 5 APPLICATION IMPLEMENTATION]
9. Database Ingestion & ETL Seeding (Populating PostgreSQL tables from frozen CSVs)
   │
10. Backend API Serving (FastAPI routes validating query parameters and returning JSON)
   │
11. Frontend UI Rendering (React components rendering dashboards, tables, and warnings)
```

---

# 5. Component Responsibilities & Architectural Boundaries

To ensure independent development across functional teams, system boundaries are strictly demarcated:

### A. Data / AI Intelligence Layer (Frozen)
* Responsible for data cleaning, identity resolution, PIT feature extraction, model inference, score calculation, explainability attribution, and intervention assignment.
* Produces immutable, cryptographically verified CSV artifacts.
* **Boundary**: Does not serve HTTP requests or maintain database connections.

### B. Database Layer (PostgreSQL)
* Responsible for relational persistence, relational constraints, foreign key referential integrity, indexing for fast filtering, and query execution.
* Houses the 4 core entities seeded from frozen intelligence files.
* **Boundary**: Contains no business logic or scoring equations.

### C. Backend / API Layer (FastAPI)
* Responsible for HTTP routing, parameter parsing, request validation, executing optimized database queries via SQLAlchemy, mapping records to Pydantic DTOs, and enforcing error standards (RFC 7807).
* Implements the 7 authoritative endpoint contracts.
* **Boundary**: Does not retrain ML models; does not compute probabilities dynamically.

### D. Frontend Layer (React / Vite)
* Responsible for user interaction, visual presentation, reactive client-side filtering, state management, displaying coverage badges, and rendering non-causal advisory notices.
* Consumes JSON payloads from the Backend API.
* **Boundary**: Never recalculates risk scores or alters attention tiers client-side.

### E. Integration Layer
* Responsible for cross-tier contract testing, end-to-end API response validation, CORS configuration, seed verification, and Docker compose orchestration.

---

# 6. Frozen vs. Dynamic System Boundary

A foundational architectural principle of PAIMANA is the strict separation between what is statically verified and what is dynamically served:

| System Element | Classification | Operational Rules & Constraints |
| :--- | :---: | :--- |
| **PIT Feature Dataset** | **FROZEN** | SHA-256 verified (`052def43...`); 437 rows; immutable observation boundary. |
| **Risk Scores & Probabilities** | **FROZEN** | SHA-256 verified (`6fac347...`); $P_c, P_s$, attention score, quantile tiers immutable. |
| **Risk Explanations & Drivers** | **FROZEN** | SHA-256 verified (`5b73c88...`); 874 rows; top 3 features and source facts immutable. |
| **Intervention Priorities** | **FROZEN** | SHA-256 verified (`3dfacd2...`); 437 rows; priority levels and actions immutable. |
| **Mathematical Semantics** | **FROZEN** | Attention score formula, compound exposure bound, quantile tier cutoffs. |
| **Database Ingestion / ETL** | **DYNAMIC** | Python seed scripts reading frozen CSVs into PostgreSQL tables. |
| **API Request Serving** | **DYNAMIC** | Querying relational tables with pagination, sorting, and multi-field filtering. |
| **Frontend Filtering & Search**| **DYNAMIC** | Client-side reactive searching by project name, CPSE agency, and state. |
| **UI Visualizations** | **DYNAMIC** | Rendering interactive SVG charts, histograms, and drill-down modals. |
| **Future Refresh Pipeline** | **DYNAMIC** | Post-hackathon batch pipelines ingesting future quarterly MoSPI snapshots. |

---

# 7. Database Implementation Architecture

The database architecture directly operationalizes the 4 relational entities established in Module 4 Phase 8 without any schema alterations.

### 7.1 Entity Relationship Diagram
```
┌───────────────────────────────────────┐
│              projects                 │
├───────────────────────────────────────┤
│ PK  canonical_project_key (VARCHAR)   │
│     source_project_id (INT)           │
│     project_name (TEXT)               │
│     state (VARCHAR)                   │
│     agency (VARCHAR)                  │
│     original_cost_crore (NUMERIC)     │
│     cumulative_expenditure_crore      │
│     expenditure_ratio (NUMERIC)       │
│     physical_progress_pct (NUMERIC)   │
│     divergence (NUMERIC)              │
│     project_age_months (NUMERIC)      │
│     remaining_duration_months (NUM)   │
│     snapshot_date (DATE)              │
└──────────────────┬────────────────────┘
                   │
                   ├─── 1:1 ───► project_risk_scores
                   │             (PK: canonical_project_key, FK -> projects)
                   │
                   ├─── 1:2 ───► project_risk_explanations
                   │             (PK: explanation_id, FK -> projects, UQ(proj, task))
                   │
                   └─── 1:1 ───► project_intervention_priorities
                                 (PK: canonical_project_key, FK -> projects)
```

### 7.2 Entity Specifications & Integrity Constraints
1. **`projects`** ($N=437$ records): Primary identity table. Primary Key: `canonical_project_key`. Contains observed point-in-time baseline metrics.
2. **`project_risk_scores`** ($N=437$ records): Primary Key: `canonical_project_key` (Foreign Key $\to$ `projects`). Enforces check constraints:
   - `cost_risk_probability BETWEEN 0.0 AND 1.0`
   - `schedule_risk_probability BETWEEN 0.0 AND 1.0` (or NULL)
   - `risk_coverage IN ('FULL', 'PARTIAL')`
   - `attention_tier IN ('Tier 1', 'Tier 2', 'Tier 3', 'Tier 4')`
   - `portfolio_rank >= 1`
3. **`project_risk_explanations`** ($N=874$ records): Primary Key: `explanation_id`. Foreign Key: `canonical_project_key`. Exactly 2 rows per project (`task = 'cost_overrun'` and `task = 'schedule_slippage'`). Unique constraint: `UNIQUE (canonical_project_key, task)`.
4. **`project_intervention_priorities`** ($N=437$ records): Primary Key: `canonical_project_key` (Foreign Key $\to$ `projects`). Enforces check constraints:
   - `intervention_priority IN ('PRIORITY_1', 'PRIORITY_2', 'PRIORITY_3', 'PRIORITY_4')`
   - `data_quality_flag IN ('COMPLETE_BASELINE_DATA', 'SCHEDULE_OUTCOME_UNOBSERVED', 'MISSING_APPROVAL_DATE')`

### 7.3 Null Semantics & Coverage Representation
* For the 132 `PARTIAL` coverage projects:
  - `schedule_risk_probability`: Strictly SQL `NULL`.
  - `compound_exposure`: Strictly SQL `NULL`.
  - `data_quality_flag`: `'SCHEDULE_OUTCOME_UNOBSERVED'`.
* Database constraints and ORM mappers must **never** coalesce `NULL` schedule values to `0.0`.

---

# 8. Backend Architecture & API Specifications

The backend layer is structured into four distinct sub-layers within a modular FastAPI application:

```text
[HTTP Request]
     │
     ▼
[Router Layer (api/v1/endpoints/)]
     │ (Validates HTTP params, enforces status codes)
     ▼
[Service Layer (services/)]
     │ (Applies portfolio business logic, joins entities)
     ▼
[Data Access Layer (repositories/)]
     │ (Executes optimized SQLAlchemy async queries)
     ▼
[Schema / Validation Layer (schemas/)]
     │ (Serializes Pydantic DTO responses with RFC 7807 errors)
     ▼
[HTTP 200 OK / JSON Response]
```

### 8.1 The 7 Authoritative API Endpoints
All endpoints return standard JSON structures with proper CORS headers and error envelopes:

1. **`GET /projects`**:
   - **Purpose**: Paginated project directory with multi-field filtering.
   - **Query Params**: `page` (default: 1), `page_size` (default: 20), `state`, `agency`, `tier`, `coverage`.
   - **Returns**: Total records, total pages, and array of project summary objects.
2. **`GET /projects/{canonical_project_key}`**:
   - **Purpose**: Unified single-project profile joining baseline metadata, risk scores, top drivers, and intervention recommendations.
   - **Returns**: Complete JSON profile or `404 Not Found`.
3. **`GET /projects/ranking`**:
   - **Purpose**: High-performance leaderboard ordered strictly by `portfolio_rank` ascending.
   - **Query Params**: `limit`, `offset`, `tier`.
4. **`GET /projects/{canonical_project_key}/risk`**:
   - **Purpose**: Detailed risk metrics ($P_c, P_s$, attention score, compound exposure, model architecture identifiers).
5. **`GET /projects/{canonical_project_key}/drivers`**:
   - **Purpose**: Local explainability details for both cost and schedule tasks, including top 3 impact bars, values, directions, and MoSPI source facts.
6. **`GET /projects/{canonical_project_key}/interventions`**:
   - **Purpose**: Operational intervention profile with primary/secondary action protocols, priority reasons, evidence groundings, and governance notes.
7. **`GET /portfolio/summary`**:
   - **Purpose**: Portfolio-wide macro aggregates (total monitored count, tier distribution, coverage breakdown, action protocol distribution, risk focus counts).

### 8.2 Error Handling Standard (RFC 7807)
All 4xx and 5xx errors must return standardized Problem Details:
```json
{
  "type": "https://paimana.mospi.gov.in/errors/project-not-found",
  "title": "Project Record Not Found",
  "status": 404,
  "detail": "Project with key 'proj_99999_invalid' does not exist in the July 2025 cohort.",
  "instance": "/api/v1/projects/proj_99999_invalid"
}
```

---

# 9. Frontend Architecture & UI Specifications

The frontend application provides an intuitive, responsive user experience structured across 5 primary screens:

### 9.1 Screen 1: Portfolio Overview Dashboard
* **Header KPI Cards**:
  - Total Monitored Projects: `437`
  - Tier 1 Priority Projects: `44` (Top 10% attention)
  - Full Coverage Assets: `305` (70%)
  - Partial Coverage Assets: `132` (30% missing schedule baseline)
* **Interactive Visualizations**:
  - Attention Score Quantile Distribution (Histogram showing Tier 1–4 thresholds).
  - Primary Action Distribution (Donut chart illustrating monitoring protocol assignments).
  - Agency Attention Concentration (Horizontal bar chart highlighting CPSEs with multiple Tier 1 assets).

### 9.2 Screen 2: Risk Ranking Table (Leaderboard)
* **Tabular Layout**: Columns for Rank (#1 to #419), Project Name, Agency, State, Coverage Badge, Cost Risk %, Schedule Risk %, Attention Score, Tier Badge, and Primary Action.
* **Controls & Filtering**:
  - Real-time text search across project name and MoSPI ID.
  - Multi-select dropdowns for State and Agency.
  - Coverage toggle (`ALL`, `FULL ONLY`, `PARTIAL ONLY`).
  - Tier filter buttons (`Tier 1`, `Tier 2`, `Tier 3`, `Tier 4`).
* **Pagination**: Server-side pagination controls (20, 50, 100 rows).

### 9.3 Screen 3: Project Detail Profile
* **Project Header**: Official title, CPSE agency, state, baseline cost, cumulative outlay, and recorded physical progress.
* **Multi-Hazard Risk Cards**:
  - **Cost Overrun Risk (>5%)**: Radial gauge displaying $P_c$ as formatted percentage (e.g. `99.8%`), model badge (`RandomForestClassifier`).
  - **Schedule Slippage Risk (>=3M)**:
    - If `FULL`: Radial gauge displaying $P_s$ (e.g. `97.0%`).
    - If `PARTIAL`: Prominently framed amber warning box:  
      *“Schedule Outcome Unavailable: Baseline milestone completion dates unobserved in canonical MoSPI reporting. Cost risk serves as sole attention score.”*
  - **Compound Exposure**: Gauge displaying concurrent risk ($\min(P_c, P_s)$) for full coverage projects, with mandatory footnote: *“Heuristic indicator of simultaneous distress; strictly NOT a joint mathematical probability.”*

### 9.4 Screen 4: Explainable Risk Drivers Panel
* **Tabbed Interface**: `Cost Overrun Drivers` vs. `Schedule Slippage Drivers`.
* **Top 3 Driver Cards**: For each driver rank (1, 2, 3):
  - Standardized feature title (e.g., *Physical vs. Financial Outlay Divergence*).
  - Directional Badge (`Increases Risk` in red, `Decreases Risk` in green).
  - Impact magnitude bar chart visualizing local marginal reference perturbation ($\Delta$).
  - Observed Source Fact callout box highlighting verified MoSPI figures.
* **Persistent Footer Disclaimer**:  
  *“Statistical feature associations from historical MoSPI snapshots. These indicators highlight monitoring focus areas and do not establish causal fault.”*

### 9.5 Screen 5: Intervention Action Panel
* **Priority Header**: Prominent urgency badge (`PRIORITY_1` — 14-day executive review recommended).
* **Protocol Action Cards**:
  - Primary Action card detailing the specific operational inspection procedure.
  - Secondary Action card outlining follow-up milestone verifications.
* **Evidence Grounding Section**: Displays the exact trigger feature and numerical value that generated the assignment.
* **Official Governance Notice**:  
  *“Advisory decision support for supervisory review. Automated administrative sanctions, budget penalties, or contract cancellations are strictly prohibited.”*

---

# 10. Recommended Repository Structure

To maintain a clean boundary between the frozen data science pipeline and future application source code, the following repository layout is recommended for Module 5:

```text
paimana-predictive-risk/
│
├── data/                          # [FROZEN] Canonical, interim, and processed CSV datasets
│   ├── raw/
│   ├── interim/                   # pit_features, project_risk_explanations
│   └── processed/                 # project_risk_scores, project_intervention_priorities
│
├── src/                           # [FROZEN] Data engineering, modeling, and scoring scripts
│   ├── data/
│   ├── features/
│   ├── models/
│   ├── scoring/
│   ├── explainability/
│   └── interventions/
│
├── reports/                       # [FROZEN] Authoritative PRD, schemas, and specifications
│   ├── MASTER_PRD.md
│   ├── MODULE5_APPLICATION_ARCHITECTURE.md
│   ├── module4_product_contract.md
│   └── module4_frontend_backend_handoff.md
│
├── tests/                         # [ACTIVE] Unit and regression test suites (303+ passing tests)
│   ├── test_master_prd.py
│   ├── test_module5_application_architecture.py
│   └── ...
│
├── backend/                       # [PROPOSED - FUTURE MODULE 5 IMPLEMENTATION]
│   ├── app/
│   │   ├── api/v1/endpoints/      # 7 FastAPI router modules
│   │   ├── core/                  # App configuration, database settings, CORS
│   │   ├── models/                # SQLAlchemy database models
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── services/              # Domain logic & aggregation services
│   │   └── db/                    # Session management & database seeding scripts
│   ├── tests/                     # Backend API integration tests
│   ├── requirements.txt           # FastAPI, SQLAlchemy, Pydantic, Uvicorn
│   └── Dockerfile
│
└── frontend/                      # [PROPOSED - FUTURE MODULE 5 IMPLEMENTATION]
    ├── src/
    │   ├── components/            # Reusable UI primitives (badges, cards, tables)
    │   ├── views/                 # 5 core screens (Portfolio, Ranking, Detail, Drivers, Interventions)
    │   ├── services/              # Axios API client functions
    │   ├── types/                 # TypeScript interfaces matching OpenAPI schemas
    │   ├── hooks/                 # Custom React hooks for data fetching
    │   ├── App.tsx
    │   └── main.tsx
    ├── package.json
    ├── tailwind.config.js
    ├── vite.config.ts
    └── Dockerfile
```

> [!IMPORTANT]
> **Implementation Scope Notice**: The `backend/` and `frontend/` trees above represent proposed future implementation directories. In Phase 9B.1, **no application code or directories have been created**.

---

# 11. Team Responsibility Matrix

| Role / Workstream | Primary Assignee | Core Responsibilities |
| :--- | :--- | :--- |
| **Data & AI Lead** | Data/AI Specialist | Maintain integrity of frozen ML artifacts (`pit_features`, `risk_scores`, `explanations`, `interventions`), verify SHA-256 hashes, review scoring logic, and validate statistical contracts. |
| **Backend Engineer** | Backend Developer | Provision PostgreSQL schema, write database seed script from frozen CSVs, implement the 7 FastAPI endpoints, write API unit tests, and handle errors. |
| **Frontend Engineer** | Frontend Developer | Bootstrap React/Vite/TypeScript project, build the 5 responsive dashboard screens, integrate Tailwind styling, implement TanStack Query API client, and enforce coverage badge rules. |
| **Integration & QA** | Joint Engineering | Orchestrate Docker compose local environment, run full end-to-end regression tests, verify cross-tier contract consistency, and benchmark API latency. |
| **Product & Pitch** | Product/Pitch Lead | Structure the 10-step hackathon demo flow, align slide decks with safe claims guidelines, and rehearse the technical narrative with jury-ready storytelling. |

---

# 12. Implementation Sequence (Build Order)

To minimize integration friction and prevent downstream rework, development must proceed in strict dependency order:

```text
[Phase 9B.1: Architecture Specification (Current Phase - COMPLETE)]
     │
     ▼
[Step 1: Database Provisioning & Schema Creation]
     │ Define PostgreSQL DDL with PK/FK constraints and indexing
     ▼
[Step 2: Data Ingestion & Seeding Script]
     │ Write seed script to populate database directly from frozen Module 4 CSVs
     ▼
[Step 3: Backend API Service Implementation]
     │ Implement FastAPI application, SQLAlchemy models, Pydantic DTOs, and 7 routes
     ▼
[Step 4: Backend API Automated Testing]
     │ Verify all 7 endpoints with pytest against seeded test database
     ▼
[Step 5: Frontend Component Implementation]
     │ Bootstrap React/TypeScript application, create layout, and build 5 screens
     ▼
[Step 6: Frontend / API Client Integration]
     │ Connect TanStack Query hooks to live FastAPI backend endpoints
     ▼
[Step 7: End-to-End System Validation]
     │ Verify filtering, sorting, partial coverage badge states, and responsive layouts
     ▼
[Step 8: Demo & Pitch Preparation]
     │ Rehearse the 10-step demonstration sequence and prepare presentation deck
```

---

# 13. MVP Boundaries & Scope

To ensure delivery within competitive hackathon deadlines, boundaries between MVP and future features are strictly defined:

### 13.1 Included in MVP (Scope)
* Serving the 437 frozen point-in-time projects via PostgreSQL and FastAPI.
* Portfolio Overview Dashboard with aggregate KPIs and distribution charts.
* Interactive Risk Ranking Leaderboard with sorting, searching, and tier filters.
* Single-project profile displaying dual-hazard probabilities ($P_c, P_s$).
* Explainable risk driver panel rendering top 3 local perturbations and MoSPI source facts.
* Evidence-grounded intervention action panel with 7 controlled protocol checklists.
* Explicit `PARTIAL COVERAGE` badge rendering with warning notices for unobserved schedule outcomes.

### 13.2 Excluded from MVP (Out of Scope / Future)
* **No Live Model Retraining**: Models are never retrained on the fly during user requests.
* **No Autonomous Sanctions**: No automated budget de-allocation, contractor blacklisting, or tender cancellations.
* **No Causal Determinism**: No claims of having identified the root causal fault of delays.
* **No Real-Time Streaming**: No live Kafka or IoT telemetry ingestion.
* **No User Auth / Role-Based Access**: Mock administrative access for jury demo.

---

# 14. Governance & Safety Safeguards

All application layers (database constraints, API serialization, and frontend UI components) must enforce the following non-negotiable governance principles:

1. **Non-Causal Language**: Explanations must be titled *"Statistical Risk Associations"* or *"Observed Risk Drivers"*, never *"Root Causes"* or *"Fault Attributions"*.
2. **No Agency or State Blaming**: Visualizations must display objective data divergence without labeling CPSEs or states as "failing" or "corrupt".
3. **Strict Partial Coverage Semantics**: If `is_eligible_schedule_target == 0`, schedule risk MUST be displayed as *"Unobserved (Missing baseline dates)"*, NEVER as *"0.0%"* or *"Low Risk"*. Schedule risk values must remain unobserved, not zero risk.
4. **Compound Exposure Non-Joint Invariant**: Compound exposure ($\min(P_c, P_s)$) is strictly NOT a joint mathematical probability $P(\text{Cost} \cap \text{Schedule})$. It must be accompanied by a footnote clarifying that it is an operational heuristic indicator of concurrent vulnerability.
5. **Quantile Tier Integrity**: Attention Tiers 1 through 4 must be labeled as *"Tier 1 (Top 10% Attention)"*, *"Tier 2 (75th-90th Percentile)"*, etc. They must **never** be renamed *"Critical / High / Medium / Low Risk"*.
6. **Advisory Intervention Notice**: Every intervention panel must prominently feature the mandatory disclaimer:  
   *“Advisory decision support for supervisory review. Automated administrative sanctions or budget penalties are strictly prohibited.”*

---

# 15. Team Handoff Checklist

Before initiating application code implementation, each team must confirm readiness against this checklist:

### For Database Engineers
- [ ] PostgreSQL 15+ instance available locally or via Docker.
- [ ] Database DDL script prepared matching Section 7.2 (entities, types, constraints).
- [ ] Seeding script prepared to read directly from frozen CSVs (`project_risk_scores.csv`, etc.).
- [ ] Foreign key cascade behavior configured (`ON DELETE CASCADE`).
- [ ] B-Tree indexes planned for `portfolio_rank`, `attention_tier`, `state`, and `agency`.

### For Backend Engineers
- [ ] Python 3.11+ environment configured with FastAPI, SQLAlchemy, and Pydantic v2.
- [ ] 7 endpoint routes planned matching Section 8.1 contracts exactly.
- [ ] RFC 7807 error handling middleware planned for 404, 422, and 500 responses.
- [ ] CORS middleware configured to allow requests from `http://localhost:5173` (Vite).
- [ ] Automated API test suite planned using `pytest` and `httpx.AsyncClient`.

### For Frontend Engineers
- [ ] Node.js 18+ and Vite configured with React 18 and TypeScript.
- [ ] Tailwind CSS configured with color scheme supporting attention tiers (Red, Orange, Yellow, Slate).
- [ ] TypeScript interfaces defined matching backend Pydantic schemas.
- [ ] TanStack Query configured for caching and error state handling.
- [ ] Recharts installed for rendering attention histograms and gauge components.
- [ ] Partial coverage warning banners and governance disclaimers drafted.

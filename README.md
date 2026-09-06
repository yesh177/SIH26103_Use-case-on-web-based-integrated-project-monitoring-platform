# PAIMANA — Predictive Risk Intelligence

> **Smart India Hackathon 2026 · Problem Statement SIH26103**<br/>
> *Use Case on Web-Based Integrated Project Monitoring Platform*<br/>
> **Status**: Frozen Data/AI Foundation & Application Contracts · Web Layer Under Active Implementation

---

## 1. Project Overview

**PAIMANA Predictive Risk Intelligence** transitions infrastructure project monitoring from *retrospective descriptive reporting* to *prospective, explainable decision support*.

Rather than merely displaying historical delays and expenditures after projects have already failed, the platform provides early-warning surveillance for public infrastructure projects tracked under the Ministry of Statistics and Programme Implementation (MoSPI). The platform has **constructed and validated a retrospective point-in-time benchmark from authentic PAIMANA/MoSPI reporting snapshots**, evaluating risk across a **437-project July-2025-to-July-2026 evaluation cohort**.

The repository currently contains the **fully completed, frozen, and mathematically verified Data/AI foundation** (356/356 unit and contract tests passing), along with authoritative application architecture contracts. Development teams are currently implementing the PostgreSQL relational database, FastAPI REST backend services, and React 18 frontend web client.

---

## 2. Current Repository State

The repository enforces strict separation between completed offline intelligence and the application implementation currently underway.

| System Layer | Scope / Module | Status | Details |
| :--- | :--- | :--- | :--- |
| **Data Ingestion & Extraction** | Module 1 & 2A | ✅ **FROZEN** | Canonical extraction of June 2025 Table 7, July 2025 Table 4, July 2026 Table 6 snapshots |
| **Project Identity Resolution** | Module 2B | ✅ **FROZEN** | Deterministic cross-snapshot linkage (4,161 observations, 3,633 unique physical projects) |
| **PIT Feature Engineering** | Module 2C | ✅ **FROZEN** | 10 numeric + 2 categorical features at July 31, 2025 cutoff; strict leakage rules (LR-01–LR-07) |
| **Target Construction & Splits** | Module 2C / 3 | ✅ **FROZEN** | 12-month prospective cost (>5%) & schedule (≥3M) targets; temporal embargo splits |
| **Baseline & Benchmark Models**| Module 3 | ✅ **FROZEN** | Deterministic majority baselines, Logistic Regression, Random Forest benchmarks |
| **Probability Calibration** | Module 3 | ✅ **FROZEN** | Raw vs. Sigmoid vs. Isotonic calibration audit across cost and schedule targets |
| **CUF vs. Enhanced Evaluation**| Module 3 | ✅ **FROZEN** | Quantitative proof of enhanced feature efficacy over standard Cost Utilisation Factors |
| **Risk Scoring & Tiers** | Module 4 | ✅ **FROZEN** | Multi-hazard scoring (`attention_score = max(P_c, P_s)`, `compound_exposure = min(P_c, P_s)`) |
| **Explainable Risk Drivers** | Module 4 | ✅ **FROZEN** | Top 3 marginal reference perturbation drivers per task grounded in MoSPI source facts |
| **Intervention Prioritisation**| Module 4 | ✅ **FROZEN** | 7 controlled action protocols, 4 priority levels, non-punitive governance safeguards |
| **Application Architecture & PRD** | Module 5 | ✅ **FROZEN** | Master PRD (`reports/MASTER_PRD.md`), Architecture (`MODULE5_APPLICATION_ARCHITECTURE.md`) |
| **API & Database Contracts** | Module 5 | ✅ **FROZEN** | REST API Contract (`docs/api_contract.md`), Seed Contract (`docs/database_seed_contract.md`) |
| **PostgreSQL Database** | Module 5 | 🔄 **IN PROGRESS** | Relational schema provisioning, Alembic migrations, artifact seeding |
| **FastAPI Backend Services** | Module 5 | 🔄 **IN PROGRESS** | 7 REST endpoints (`/api/v1`), Pydantic v2 schemas, SQLAlchemy ORM queries |
| **React 18 Frontend Client** | Module 5 | 🔄 **IN PROGRESS** | React 18, Vite, TypeScript, Tailwind CSS, TanStack Query, Recharts visualizations |
| **End-to-End Integration** | Module 5 | 🔄 **IN PROGRESS** | Integration testing, full-stack container orchestration, interactive demonstration flow |

> [!NOTE]
> **Methodology Boundaries**:
> 1. The benchmark evaluates a **retrospective holdout cohort of 437 physical projects** observed at July 31, 2025 and evaluated at July 31, 2026. The repository does **not** claim a multi-year monthly continuous history or live real-time synchronization with government databases.
> 2. All model probabilities and feature attributions represent statistical associations in historical data. They do **not** establish causal fault, administrative negligence, or contractor liability.
> 3. The live web application serves pre-computed intelligence and **does NOT execute live model retraining** during user browsing.

---

## 3. End-to-End System Architecture

The PAIMANA production architecture cleanly separates offline intelligence generation from the application serving layer:

```
┌────────────────────────────────────────────────────────────────────────┐
│               OFFLINE DATA & AI PIPELINE (FROZEN)                       │
│  MoSPI Snapshots (Tables 7, 4, 6) → Canonical Extraction & Cleaning    │
│  → Identity Resolution → Longitudinal Panel (N=4,161)                  │
│  → Point-in-Time Features Cohort (N=437, July 2025 Cutoff)             │
│  → Random Forest Multi-Hazard Scoring (Cost & Schedule)                │
│  → Marginal Reference Perturbation Explainability (Top 3 Drivers)      │
│  → Decision-Support Intervention Prioritisation (7 Protocols)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ (Deterministic Seed via docs/database_seed_contract.md)
┌────────────────────────────────────────────────────────────────────────┐
│               APPLICATION SERVING LAYER (IN PROGRESS)                  │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │  PostgreSQL 15+ Relational Database                            │   │
│   │  - projects (N=437)                                            │   │
│   │  - project_risk_scores (N=437)                                 │   │
│   │  - project_risk_explanations (N=874)                           │   │
│   │  - project_intervention_priorities (N=437)                     │   │
│   └───────────────────────────────┬────────────────────────────────┘   │
│                                   │ (SQLAlchemy ORM / Port 5432)       │
│   ┌───────────────────────────────▼────────────────────────────────┐   │
│   │  FastAPI REST API Services (Python 3.11+ / Port 8000)          │   │
│   │  - 7 REST Routes under /api/v1 (docs/api_contract.md)          │   │
│   │  - Pydantic v2 Contract Validation & Error Envelope            │   │
│   └───────────────────────────────┬────────────────────────────────┘   │
│                                   │ (HTTP / JSON / Port 5173)          │
│   ┌───────────────────────────────▼────────────────────────────────┐   │
│   │  React 18 Web Client (Vite / TypeScript 5.x / Tailwind CSS)    │   │
│   │  - Portfolio Overview Dashboard                                │   │
│   │  - Risk Ranking Leaderboard (Standard Competition Ranking)     │   │
│   │  - Project Detail Profile (Cost, Schedule, Metadata)           │   │
│   │  - Explainable Risk Drivers Panel (Top 3 Drivers + Facts)      │   │
│   │  - Intervention Action Panel (Protocols & MoSPI Advisories)    │   │
│   └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Locked Technology Stack

The technology stack is formally locked across all implementation workstreams:

### Frontend Web Client (Authoritative)
* **Framework**: React 18 with Vite build tooling (Fast HMR, optimized bundle)
* **Language**: TypeScript 5.x (strict static typing aligned with OpenAPI schemas)
* **Styling**: Tailwind CSS 3.x (responsive layout, standardized attention tier palettes)
* **Client-Side Routing**: React Router v6
* **Data Fetching & Caching**: TanStack Query (React Query v5) + Axios
* **Data Visualizations**: Recharts (composable SVG charts for distributions, gauges, impact bars)
* **Icons & UI Primitives**: Lucide React + Radix UI
* *(Note: Next.js is explicitly excluded).*

### Backend REST API Services (Authoritative)
* **Framework**: FastAPI 0.110+ (high-performance ASGI, automatic OpenAPI/Swagger docs)
* **Language & Runtime**: Python 3.11+ with Uvicorn server
* **Schema Validation**: Pydantic v2
* **ORM & Database Client**: SQLAlchemy 2.0+
* **Database Migrations**: Alembic
* *(Note: Express and NestJS are explicitly excluded).*

### Database & Storage (Authoritative)
* **RDBMS**: PostgreSQL 15+
* **Schema Design**: 4 relational tables enforcing primary/foreign keys on `canonical_project_key`
* **Integrity Guarantee**: Strictly preserves `PARTIAL` coverage NULL invariants

### Data/AI & Testing Foundation (Authoritative)
* **Runtime**: Python 3.11+ (verified up to Python 3.14)
* **Data Processing & ML**: scikit-learn 1.4+, pandas 2.2+, numpy 1.26+, scipy 1.12+, matplotlib 3.8+
* **Test Runner**: pytest 8.0+ (356/356 unit and contract tests passing)

---

## 5. Key Contracts & Specifications

The repository maintains strict documentation governance. Before modifying or implementing components, developers must consult the authoritative specifications:

| Document Path | Scope & Authority |
| :--- | :--- |
| [`reports/MASTER_PRD.md`](reports/MASTER_PRD.md) | **Authoritative Product Requirements Document** (32 sections covering SIH problem mapping, methodology, metrics, risk formulas, UX requirements, team ownership, and traceability matrix). |
| [`reports/MODULE5_APPLICATION_ARCHITECTURE.md`](reports/MODULE5_APPLICATION_ARCHITECTURE.md) | **Module 5 Application Architecture Specification** (15 sections detailing high-level architecture, tech stack, data flow, DB schema, 7 API endpoints, 5 screens, and build order). |
| [`docs/api_contract.md`](docs/api_contract.md) | **Single Implementation Authority for REST API** (`/api/v1` endpoints, query parameters, sorting, pagination, schemas, errors, enums, and normalization rules). |
| [`docs/database_seed_contract.md`](docs/database_seed_contract.md) | **Authoritative Database Ingestion Contract** (PostgreSQL DDL, SHA-256 verification, row counts, NULL semantics, idempotency, and rollback rules). |
| [`reports/module4_product_contract.md`](reports/module4_product_contract.md) | **Module 4 Product Contract** (Mathematical formulas, non-causal principles, quantile thresholds, action taxonomies, and display invariants). |
| [`reports/module4_frontend_backend_handoff.md`](reports/module4_frontend_backend_handoff.md) | **Cross-Functional Engineering Handoff** (Component wireframes, state management, normalization note, and data dictionaries). |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | **Developer Contributing Guide** (Branching strategy, pull request rules, no-touch invariants, and local setup). |

---

## 6. Repository Directory Structure

```text
paimana-predictive-risk/
├── .github/
│   └── workflows/
│       └── tests.yml                 # Automated CI workflow executing pytest on main
├── docs/                             # Engineering contracts and technical specifications
│   ├── api_contract.md               # Authoritative REST API specification (/api/v1)
│   ├── database_seed_contract.md     # Authoritative PostgreSQL seeding protocol
│   ├── module2b_canonical_schema.md  # Canonical snapshot normalization specification
│   ├── module2c_pit_feature_specification.md # Point-in-Time feature definitions
│   ├── module3_evaluation_protocol.md# Retrospective holdout evaluation protocol
│   ├── project_identity_resolution.md# Cross-snapshot deterministic linkage rules
│   └── ...
├── reports/                          # Formal research reports and architectural blueprints
│   ├── MASTER_PRD.md                 # Complete 32-section Master Product Requirements Document
│   ├── MODULE5_APPLICATION_ARCHITECTURE.md # Full application architecture specification
│   ├── module4_product_contract.md   # Intelligence contract & semantic invariants
│   ├── module4_frontend_backend_handoff.md # Frontend/Backend technical handoff
│   ├── figures/                      # 16 calibration curves (logistic & random forest)
│   └── ...                           # Module 2–4 phase verification and benchmark reports
├── src/                              # Frozen Data/AI engineering and modeling codebase
│   ├── data/                         # Canonical extraction, ingestion, and temporal split
│   ├── features/                     # PIT feature engineering and retrospective target generation
│   ├── models/                       # Baselines, Random Forest benchmark, probability calibration
│   ├── scoring/                      # Multi-hazard risk scoring and partition generation
│   ├── explainability/               # Marginal reference perturbation driver generator
│   ├── interventions/                # Evidence-grounded intervention prioritisation engine
│   └── ...
├── tests/                            # Comprehensive automated unit & contract test suite
│   ├── test_master_prd.py            # Validates PRD invariants, sections, and hashes
│   ├── test_module5_application_architecture.py # Validates application architecture
│   ├── test_module4_product_contract.py # Validates product contracts and semantics
│   ├── test_module4_risk_scoring.py  # Validates multi-hazard formulas and partitions
│   └── ...                           # 22 test suites (356 / 356 tests passing)
├── requirements.txt                  # Minimal clean developer dependencies
├── CONTRIBUTING.md                   # Team collaboration guidelines and branching rules
├── .gitignore                        # Git exclusion rules (*.csv, venv, caches)
└── README.md                         # This repository guide
```

---

## 7. Developer Quickstart

### 7.1 Local Python Setup
```bash
# 1. Clone the repository
git clone https://github.com/yesh177/SIH26103_Use-case-on-web-based-integrated-project-monitoring-platform.git
cd SIH26103_Use-case-on-web-based-integrated-project-monitoring-platform

# 2. Create and activate a virtual environment
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# 3. Install developer dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 7.2 Running Automated Tests
```bash
pytest -q
```
Expected output:
```text
356 passed in ...
```

### 7.3 Verifying Frozen Artifact Checksums
To ensure local data integrity against the authoritative Master PRD:
```bash
python -c "import hashlib; files = {'data/interim/pit_features_july2025_to_july2026.csv': '052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329', 'data/processed/project_risk_scores.csv': '6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d', 'data/interim/project_risk_explanations.csv': '5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2', 'data/processed/project_intervention_priorities.csv': '3dfacd2805610e0a1a9ff3f10461c97322a3bf62ca1dc348fc6baca13e012ec5'}; [print(f'{p}: PASS' if hashlib.sha256(open(p, 'rb').read()).hexdigest() == h else f'{p}: FAIL') for p, h in files.items()]"
```

---

## 8. Mathematical & Semantic Reference Summary

* **Cost Risk ($P_c$)**: Probability of $> 5\%$ cost overrun by July 2026.
* **Schedule Risk ($P_s$)**: Probability of $\ge 3$ months slippage by July 2026 (`null` for 132 partial coverage projects).
* **Attention Score**:
  $$\text{attention\_score} = \max(P_c, P_s)$$
  *Portfolio prioritization index, NOT a joint probability.*
* **Compound Exposure**:
  $$\text{compound\_exposure} = \min(P_c, P_s)$$
  *Dual-hazard co-elevation sentinel, NOT a joint probability.*
* **Quantile Priority Tiers**:
  - **Tier 1** ($\ge 0.9947$): Top 10% supervisory focus ($N=44$)
  - **Tier 2** ($\ge 0.9833$): 75th–90th percentile ($N=73$)
  - **Tier 3** ($\ge 0.9067$): 50th–75th percentile ($N=102$)
  - **Tier 4** ($< 0.9067$): Lower 50% baseline tracking ($N=218$)
  - *(Tiers represent relative supervisory urgency; never label as "Critical/High/Medium/Low Risk").*

---

<sub>Built for Smart India Hackathon 2026 · Ministry of Statistics and Programme Implementation (MoSPI) · SIH26103</sub>

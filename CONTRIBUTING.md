# Contributing to PAIMANA

Thank you for contributing to **PAIMANA Predictive Risk Intelligence** (SIH26103).

This guide outlines our development workflow, branch strategy, testing standards, and architectural boundaries.

---

## 1. Core Invariants & Boundaries

The PAIMANA Data/AI and research methodology is **frozen and verified** (356/356 unit and contract tests passing).

### Absolute No-Touch Rules
When contributing, you MUST NOT modify:
- Target definitions (`cost_overrun_5pct_2026`, `time_overrun_3m_2026`)
- Point-in-Time (PIT) feature definitions and cutoff dates (`2025-07-01`)
- Leakage rules (LR-01 through LR-07)
- Temporal validation splits and embargo periods
- Machine learning benchmark methodology and trained model artifacts
- Probability calibration evaluations and results
- Risk scoring formulas (`attention_score = max(P_c, P_s)`, `compound_exposure = min(P_c, P_s)`)
- Quantile tier definitions (Tier 1..Tier 4)
- Non-causal explainability and intervention taxonomies
- Frozen CSV artifact contents and their authoritative SHA-256 hashes

---

## 2. Branching Strategy & Git Workflow

* **`main`**: Protected integration branch. All code on `main` must pass the full test suite (`pytest -q`). Direct pushes to `main` without review are prohibited.
* **Feature Branches**: Branch from `main` using descriptive prefixes:
  - `feature/backend-<feature-name>`: Backend REST API, database models, or seeders.
  - `feature/frontend-<feature-name>`: React 18 UI components, hooks, or styles.
  - `feature/ml-integration-<feature-name>`: Serving or packaging frozen ML artifacts.
  - `fix/<issue-name>`: Bug fixes for documentation, CI, or tooling.

### PR Requirements
1. Every Pull Request must target `main`.
2. All automated CI checks must pass (`pytest -q` -> 356 passed).
3. API modifications require updating `docs/api_contract.md`.
4. Database schema modifications require an Alembic migration script and updating `docs/database_seed_contract.md`.
5. Frontend changes must consume official API contract endpoints; do not invent calculations or risk formulas on the client.
6. Never force push (`git push --force`) to shared branches.
7. Never commit credentials, secrets, or large data files (`*.csv` is gitignored).

---

## 3. Team Ownership Matrix

| Workstream | Primary Owner | Scope & Authority |
| :--- | :--- | :--- |
| **Data/AI Lead** | Data/AI Team | Frozen methodology, statistical contracts, research reports, feature schemas, model benchmarks, risk semantics. |
| **Backend Engineering** | Backend Team | FastAPI REST services (`/api/v1`), SQLAlchemy models, Alembic migrations, database seeders, API contract compliance. |
| **Database Engineering**| Database Team | PostgreSQL 15+ schema, relational indexes, constraints, database seed verification. |
| **Frontend UI/UX** | Frontend Team | React 18, Vite, TypeScript, Tailwind CSS, TanStack Query, Recharts visualizations, user experience. |
| **ML Integration** | Joint Engineering | Model artifact loading and serving layer without mutating model semantics or retraining. |

---

## 4. Local Development Setup

### 4.1 Prerequisites
- Python 3.11+ (Python 3.11–3.14 supported)
- Node.js 18+ (for frontend development)
- PostgreSQL 15+ (for backend and database development)
- Git

### 4.2 Python Environment Setup
```bash
# Clone the repository
git clone https://github.com/yesh177/SIH26103_Use-case-on-web-based-integrated-project-monitoring-platform.git
cd SIH26103_Use-case-on-web-based-integrated-project-monitoring-platform

# Create and activate virtual environment
python -m venv venv
# On Windows PowerShell:
.env\Scripts\Activate.ps1
# On Linux/macOS:
# source venv/bin/activate

# Install development dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 Running the Test Suite
```bash
pytest -q
```
Expected output:
```text
356 passed in ...
```

---

## 5. Architectural Standards

* **Authoritative Frontend Stack**:
  - React 18, Vite, TypeScript 5.x
  - React Router v6
  - TanStack Query (React Query v5) + Axios
  - Tailwind CSS 3.x
  - Recharts
  - *Next.js is explicitly prohibited.*
* **Authoritative Backend Stack**:
  - FastAPI 0.110+
  - Python 3.11+
  - Pydantic v2
  - SQLAlchemy 2.0+
  - Alembic
  - PostgreSQL 15+
  - *Express and NestJS are explicitly prohibited.*
* **System Architecture**:
  ```
  Frozen Data/AI Artifacts
            ↓
       PostgreSQL
            ↓
         FastAPI
            ↓
       React + Vite
  ```
* **No Live Model Retraining**: The live application serves pre-computed intelligence and does not perform live model training during dashboard browsing.

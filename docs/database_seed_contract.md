# PAIMANA Database & Artifact Seed Contract

**Version**: 1.0.0 (Authoritative)<br/>
**Target RDBMS**: PostgreSQL 15+<br/>
**Status**: Frozen Application Contract<br/>
**Applicability**: Database Engineering & Backend Data Access<br/>
**Date**: September 2026

---

## 1. Executive Summary & Purpose

This contract defines the authoritative, deterministic protocol for ingesting frozen Data/AI artifacts into the PostgreSQL application database for the PAIMANA Predictive Risk Intelligence platform.

### 1.1 Core Architectural Boundary
The database functions exclusively as an **application serving layer** over pre-computed, verified Data/AI intelligence.
* **No Database Reinterpretation**: The database schema, ETL loading scripts, and backend ORM models MUST NOT re-score projects, recalculate probabilities, alter attention tiers, or modify feature importance weights.
* **Separation of Concerns**: Frozen CSV artifacts produced by the offline Data/AI pipeline are the authoritative source of truth. The relational database mirrors this frozen intelligence with relational indexing and foreign key constraints for fast web queries.

---

## 2. Required Frozen Artifacts & Checksum Verification

Before executing any database seeding operation, the seed runner MUST verify the existence and cryptographic SHA-256 hash of all required input artifacts.

### 2.1 Authoritative Seed Artifact Manifest

| Table Name | Source Artifact Path | Exact SHA-256 Checksum | Expected Rows | Ingestion Role |
| :--- | :--- | :--- | :--- | :--- |
| `projects` | `data/interim/pit_features_july2025_to_july2026.csv` | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | 437 | Primary project metadata, physical progress, and financial baseline |
| `project_risk_scores` | `data/processed/project_risk_scores.csv` | `6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d` | 437 | Multi-hazard probabilities, attention scores, compound exposure, tiers, ranks |
| `project_risk_explanations` | `data/interim/project_risk_explanations.csv` | `5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2` | 874 | Top 3 explainable risk drivers & factual MoSPI context (2 rows per project) |
| `project_intervention_priorities`| `data/processed/project_intervention_priorities.csv` | `3dfacd2805610e0a1a9ff3f10461c97322a3bf62ca1dc348fc6baca13e012ec5` | 437 | Intervention urgency, recommended protocols, evidence grounding, governance |

### 2.2 Optional Sidecar Artifact (Model Partitions)
* **Path**: `data/processed/project_risk_score_partitions.csv` (437 rows)
* **Purpose**: Records offline model evaluation partitions (`cost_model_split`, `schedule_model_split`). It may optionally be seeded into an administrative audit table or joined to `project_risk_scores`.

---

## 3. Relational Schema & DDL Specification

The PostgreSQL schema enforces relational integrity with `canonical_project_key` as the primary key of `projects` and foreign keys across all dependent tables.

### 3.1 Entity 1: `projects`
```sql
CREATE TABLE IF NOT EXISTS projects (
    canonical_project_key VARCHAR(64) PRIMARY KEY,
    source_project_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    state VARCHAR(100) NOT NULL,
    agency VARCHAR(150) NOT NULL,
    original_cost_crore NUMERIC(14, 2) NOT NULL,
    cumulative_expenditure_crore NUMERIC(14, 2) NOT NULL,
    expenditure_ratio NUMERIC(10, 4) NOT NULL,
    physical_progress_pct NUMERIC(6, 2) NOT NULL,
    divergence NUMERIC(10, 4) NOT NULL,
    project_age_months NUMERIC(8, 2) NOT NULL,
    remaining_duration_months NUMERIC(8, 2),  -- NULLABLE for missing original completion dates
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_state ON projects(state);
CREATE INDEX IF NOT EXISTS idx_projects_agency ON projects(agency);
CREATE INDEX IF NOT EXISTS idx_projects_source_id ON projects(source_project_id);
```

### 3.2 Entity 2: `project_risk_scores`
```sql
CREATE TABLE IF NOT EXISTS project_risk_scores (
    canonical_project_key VARCHAR(64) PRIMARY KEY REFERENCES projects(canonical_project_key) ON DELETE CASCADE,
    source_project_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    state VARCHAR(100) NOT NULL,
    agency VARCHAR(150) NOT NULL,
    snapshot_date DATE NOT NULL,
    prediction_cutoff_date DATE NOT NULL,
    is_eligible_cost_target SMALLINT NOT NULL,
    is_eligible_schedule_target SMALLINT NOT NULL,
    cost_risk_probability NUMERIC(6, 4) NOT NULL,
    schedule_risk_probability NUMERIC(6, 4),  -- NULLABLE (NULL for N=132 PARTIAL projects)
    risk_coverage VARCHAR(10) NOT NULL,       -- 'FULL' or 'PARTIAL'
    attention_score NUMERIC(6, 4) NOT NULL,
    compound_exposure NUMERIC(6, 4),          -- NULLABLE (NULL for N=132 PARTIAL projects)
    attention_tier VARCHAR(10) NOT NULL,      -- 'Tier 1', 'Tier 2', 'Tier 3', 'Tier 4'
    portfolio_rank INTEGER NOT NULL,
    cost_model_name VARCHAR(50) NOT NULL,
    schedule_model_name VARCHAR(50) NOT NULL,
    cost_probability_variant VARCHAR(50) NOT NULL,
    schedule_probability_variant VARCHAR(50) NOT NULL,
    scoring_method_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_scores_tier ON project_risk_scores(attention_tier);
CREATE INDEX IF NOT EXISTS idx_risk_scores_rank ON project_risk_scores(portfolio_rank);
CREATE INDEX IF NOT EXISTS idx_risk_scores_coverage ON project_risk_scores(risk_coverage);
CREATE INDEX IF NOT EXISTS idx_risk_scores_attention ON project_risk_scores(attention_score DESC);
```

### 3.3 Entity 3: `project_risk_explanations`
```sql
CREATE TABLE IF NOT EXISTS project_risk_explanations (
    id SERIAL PRIMARY KEY,
    canonical_project_key VARCHAR(64) NOT NULL REFERENCES projects(canonical_project_key) ON DELETE CASCADE,
    source_project_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    state VARCHAR(100) NOT NULL,
    agency VARCHAR(150) NOT NULL,
    task VARCHAR(30) NOT NULL,                 -- 'cost_overrun' or 'schedule_slippage'
    is_eligible_task_target SMALLINT NOT NULL,
    predicted_risk_probability NUMERIC(6, 4),  -- NULLABLE (NULL if ineligible task)
    attention_score NUMERIC(6, 4) NOT NULL,
    attention_tier VARCHAR(10) NOT NULL,
    portfolio_rank INTEGER NOT NULL,
    risk_coverage VARCHAR(10) NOT NULL,
    top_1_feature VARCHAR(100),
    top_1_feature_value NUMERIC(14, 4),
    top_1_impact NUMERIC(8, 4),
    top_1_direction VARCHAR(20),
    top_1_source_fact TEXT,
    top_2_feature VARCHAR(100),
    top_2_feature_value NUMERIC(14, 4),
    top_2_impact NUMERIC(8, 4),
    top_2_direction VARCHAR(20),
    top_2_source_fact TEXT,
    top_3_feature VARCHAR(100),
    top_3_feature_value NUMERIC(14, 4),
    top_3_impact NUMERIC(8, 4),
    top_3_direction VARCHAR(20),
    top_3_source_fact TEXT,
    explanation_method VARCHAR(100) NOT NULL,
    explanation_disclaimer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_task UNIQUE (canonical_project_key, task)
);

CREATE INDEX IF NOT EXISTS idx_explanations_key ON project_risk_explanations(canonical_project_key);
CREATE INDEX IF NOT EXISTS idx_explanations_task ON project_risk_explanations(task);
```

### 3.4 Entity 4: `project_intervention_priorities`
```sql
CREATE TABLE IF NOT EXISTS project_intervention_priorities (
    canonical_project_key VARCHAR(64) PRIMARY KEY REFERENCES projects(canonical_project_key) ON DELETE CASCADE,
    cost_risk_probability NUMERIC(6, 4) NOT NULL,
    schedule_risk_probability NUMERIC(6, 4),  -- NULLABLE
    attention_score NUMERIC(6, 4) NOT NULL,
    risk_coverage VARCHAR(10) NOT NULL,
    portfolio_rank INTEGER NOT NULL,
    intervention_priority VARCHAR(20) NOT NULL, -- 'PRIORITY_1'..'PRIORITY_4'
    primary_action VARCHAR(50) NOT NULL,
    secondary_action VARCHAR(50) NOT NULL,
    risk_focus VARCHAR(50) NOT NULL,
    priority_reason TEXT NOT NULL,
    evidence_feature VARCHAR(100) NOT NULL,
    evidence_value NUMERIC(14, 4) NOT NULL,
    evidence_direction VARCHAR(20) NOT NULL,
    data_quality_flag VARCHAR(50) NOT NULL,
    governance_note TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_interventions_priority ON project_intervention_priorities(intervention_priority);
CREATE INDEX IF NOT EXISTS idx_interventions_action ON project_intervention_priorities(primary_action);
CREATE INDEX IF NOT EXISTS idx_interventions_focus ON project_intervention_priorities(risk_focus);
```

---

## 4. Seeding Protocol & Execution Rules

### 4.1 Step-by-Step Seed Sequence
1. **Pre-flight Checksum Verification**:
   - Compute the SHA-256 hash of all 4 input CSV files.
   - If any hash does not match Section 2.1, halt with error code `ERR_CHECKSUM_MISMATCH`.
2. **Transaction Isolation**:
   - The entire seeding process MUST execute inside a single atomic database transaction (`BEGIN ... COMMIT`).
   - If any insert fails, row count check fails, or constraint is violated, execute `ROLLBACK`.
3. **Table Insertion Order**:
   - Order 1: `projects` (Parent entity; 437 records)
   - Order 2: `project_risk_scores` (Child entity; 437 records)
   - Order 3: `project_risk_explanations` (Child entity; 874 records, exactly 2 per project)
   - Order 4: `project_intervention_priorities` (Child entity; 437 records)
4. **Post-Seed Integrity Verification**:
   - Verify row counts:
     - `SELECT COUNT(*) FROM projects` = `437`
     - `SELECT COUNT(*) FROM project_risk_scores` = `437`
     - `SELECT COUNT(*) FROM project_risk_explanations` = `874`
     - `SELECT COUNT(*) FROM project_intervention_priorities` = `437`
   - Verify NULL contract:
     - `SELECT COUNT(*) FROM project_risk_scores WHERE schedule_risk_probability IS NULL` = `132`
     - `SELECT COUNT(*) FROM project_risk_scores WHERE compound_exposure IS NULL` = `132`
     - `SELECT COUNT(*) FROM project_risk_scores WHERE risk_coverage = 'PARTIAL'` = `132`
     - `SELECT COUNT(*) FROM project_risk_scores WHERE risk_coverage = 'FULL'` = `305`
   - Verify Foreign Key Integrity:
     - No orphaned records exist across all three child tables.

### 4.2 Idempotency & Re-Seeding Behavior
* Seeding scripts MUST support idempotent execution.
* Recommended strategy:
  ```sql
  TRUNCATE TABLE project_intervention_priorities, project_risk_explanations, project_risk_scores, projects CASCADE;
  ```
  Followed by sequential bulk insertion, all wrapped within `BEGIN ... COMMIT`.
* Re-seeding with identical frozen CSVs must yield bitwise identical database state without duplicate key errors.

### 4.3 Missing Artifact & Error Handling Policy
* **Missing Artifact**: If any CSV is missing, the script MUST NOT synthesize mock data. It must terminate immediately with exit code 1:
  `Error: Required frozen artifact <path> not found. Run pipeline or acquire verified seed bundle.`
* **Invalid Hash**: If an artifact hash has drifted, terminate immediately:
  `Error: Artifact <path> SHA-256 checksum mismatch. Expected <hash>, found <actual>. Seeding aborted.`
* **Prohibition on Arbitrary Substitution**: Substituting alternative CSV files, test fixtures, or manual overrides into the production database is strictly prohibited.

---

## 5. Artifact Storage & Developer Acquisition Protocol

* **Git Ignore Policy**: The physical CSV files under `data/` are intentionally excluded from Git version control via `.gitignore` (`*.csv`) to maintain lightweight repository size and prevent committing large binary/data artifacts.
* **Developer Acquisition**:
  1. Developers running the full repository can regenerate the bitwise identical frozen artifacts locally at any time by executing the deterministic scoring pipeline:
     ```bash
     python -m src.scoring.generate_project_risk_scores
     ```
  2. Alternatively, backend and database engineers can obtain the verified seed bundle directly from the Data/AI Lead.
  3. Every artifact bundle must pass the SHA-256 checksum gate defined in Section 2.1 before database insertion.

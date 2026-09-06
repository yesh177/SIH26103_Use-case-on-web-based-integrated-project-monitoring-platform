# PAIMANA REST API Contract & Interface Specification

**Version**: 1.0.0 (Authoritative)<br/>
**Base Path**: `/api/v1`<br/>
**Status**: Frozen Application Contract<br/>
**Applicability**: Backend (FastAPI) & Frontend (React 18 / Vite / TypeScript)<br/>
**Date**: September 2026

---

## 1. Executive Overview & Architectural Principles

This document defines the authoritative, single-source-of-truth REST API contract for the PAIMANA Predictive Risk Intelligence platform. It governs all communication between the FastAPI backend service and the React 18 frontend web client.

### 1.1 Core Architectural Principles

1. **Deterministic Serving Over Frozen Intelligence**: The backend serves pre-computed intelligence derived from the frozen Module 2–4 Data/AI pipeline and seeded into PostgreSQL 15+.
2. **No Live Model Retraining**: All predictive inference, calibration evaluation, SHAP/perturbation driver attributions, and intervention assignments are computed offline. The API does not execute live machine learning training or retrain models during request handling.
3. **Strict Field Normalization**:
   - Physical CSV / DB representation: `"Raw / Uncalibrated"`
   - REST / API JSON representation: `"raw_uncalibrated"`
   - The backend MUST normalize internal database representations to the API contract format at the serialization boundary.
4. **Explicit Null Semantics (No Imputation)**:
   - For projects with `PARTIAL` risk coverage ($N=132$), baseline schedule dates were unrecorded in administrative sources.
   - For these projects, `schedule_risk_probability` and `compound_exposure` are strictly `null`.
   - Downstream clients and backend serializers MUST NEVER impute `0.0`, `-1`, or default values for unobserved schedule outcomes.
5. **Non-Causal Statistical Representation**:
   - All model outputs represent empirical statistical associations observed in historical MoSPI holdout cohorts.
   - Risk drivers, probabilities, and intervention protocols do not imply operational negligence, administrative culpability, or contractual breach.
   - Automated sanctions, budget freezes, and contractor blacklisting are strictly prohibited.
6. **Illustrative Mock/Example Key Notice**:
   - The key `"proj_16723_02b9f3d9"` used throughout this document's JSON examples is strictly an **ILLUSTRATIVE MOCK/EXAMPLE `canonical_project_key` only**.
   - **Developer Onboarding Note**: Real seeded database keys come directly from the frozen Data/AI artifacts (`data/processed/project_risk_scores.csv`). Real keys follow the actual `PROJ-PAIMANA-*` format (e.g., `PROJ-PAIMANA-400119`, `PROJ-PAIMANA-400220`, `PROJ-PAIMANA-602099`). Developers must not assume the illustrative example key exists in the database.

---

## 2. Mathematical Semantics & Controlled Vocabularies

### 2.1 Risk Metric Semantics

* **Cost Risk Probability ($P_c$)**: Model-estimated probability of prospective cumulative cost overrun exceeding 5% over a 12-month horizon ($[0.0, 1.0]$). Defined for all 437 projects.
* **Schedule Risk Probability ($P_s$)**: Model-estimated probability of completion date slippage $\ge 3$ months over a 12-month horizon ($[0.0, 1.0]$). Defined for 305 eligible projects; strictly `null` for 132 ineligible projects.
* **Attention Score**:
  $$\text{attention\_score} = \begin{cases} \max(P_c, P_s) & \text{if } \text{risk\_coverage} = \text{"FULL"} \\ P_c & \text{if } \text{risk\_coverage} = \text{"PARTIAL"} \end{cases}$$
  **Crucial Semantic**: `attention_score` is a **comparative portfolio prioritization index**, NOT a joint probability of simultaneous failure.
* **Compound Exposure**:
  $$\text{compound\_exposure} = \begin{cases} \min(P_c, P_s) & \text{if } \text{risk\_coverage} = \text{"FULL"} \\ \text{null} & \text{if } \text{risk\_coverage} = \text{"PARTIAL"} \end{cases}$$
  **Crucial Semantic**: Measures concurrent vulnerability across both cost and schedule hazards simultaneously. It is strictly a dual-hazard co-elevation sentinel, NOT a joint mathematical probability $P(\text{Cost} \cap \text{Schedule})$.

### 2.2 Controlled Enums

#### Attention Tiers (`attention_tier`)
Tiers reflect relative empirical quantile distribution across the 437-project portfolio cohort:
* `"Tier 1"`: Attention score $\ge 0.994667$ (Top 10% supervisory focus, $N=44$)
* `"Tier 2"`: Attention score $\ge 0.983333$ and $< 0.994667$ (75th–90th percentile, $N=73$)
* `"Tier 3"`: Attention score $\ge 0.906667$ and $< 0.983333$ (50th–75th percentile, $N=102$)
* `"Tier 4"`: Attention score $< 0.906667$ (Lower 50% percentile, $N=218$)

> [!WARNING]
> **Prohibited Nomenclature**: Tiers MUST NEVER be labeled as `"Critical Risk"`, `"High Risk"`, `"Medium Risk"`, or `"Low Risk"`. They represent relative supervisory review urgency and resource allocation bands.

#### Risk Coverage (`risk_coverage`)
* `"FULL"`: Both cost and schedule baselines available ($N=305$)
* `"PARTIAL"`: Cost baseline available; schedule completion target unrecorded in source reporting ($N=132$)

#### Intervention Priority (`intervention_priority`)
* `"PRIORITY_1"`: Executive review within 14 business days ($N=44$, maps 1:1 to Tier 1)
* `"PRIORITY_2"`: Monthly committee review ($N=73$, maps 1:1 to Tier 2)
* `"PRIORITY_3"`: Standard quarterly milestone tracking ($N=102$, maps 1:1 to Tier 3)
* `"PRIORITY_4"`: Routine reporting cadence ($N=218$, maps 1:1 to Tier 4)

#### Primary & Secondary Actions (`primary_action`, `secondary_action`)
1. `"DATA_QUALITY_REVIEW"` ($N=128$ primary)
2. `"JOINT_COST_SCHEDULE_REVIEW"` ($N=90$ primary)
3. `"SCHEDULE_REVIEW"` ($N=81$ primary)
4. `"COMPLETION_STATUS_REVIEW"` ($N=79$ primary)
5. `"COST_REVIEW"` ($N=29$ primary)
6. `"PROGRESS_VERIFICATION"` ($N=24$ primary, $N=231$ secondary)
7. `"EXPENDITURE_PROGRESS_REVIEW"` ($N=6$ primary, $N=24$ secondary)

#### Risk Focus (`risk_focus`)
1. `"SCHEDULE_RISK"` ($N=159$)
2. `"UNOBSERVED_SCHEDULE"` ($N=128$)
3. `"JOINT_COST_SCHEDULE"` ($N=90$)
4. `"COST_RISK"` ($N=29$)
5. `"BASELINE_MONITORING"` ($N=24$)
6. `"PROGRESS_FINANCIAL_DIVERGENCE"` ($N=6$)
7. `"COMPLETION_STATUS"` ($N=1$)

#### Driver Direction (`direction`)
* `"INCREASES_RISK"`
* `"DECREASES_RISK"`
* `"NEUTRAL"`

#### Probability Variant (`cost_probability_variant`, `schedule_probability_variant`)
* `"raw_uncalibrated"` (authoritative API serialization)

---

## 3. Standard Error Envelope

All API errors return a standard structured JSON error envelope:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Project with key 'proj_16723_02b9f3d9' was not found.",
    "details": null,
    "timestamp": "2026-09-06T20:30:00Z"
  }
}
```

Standard HTTP Status Codes:
* `200 OK`: Successful request.
* `400 Bad Request`: Invalid query parameters or malformed request syntax.
* `404 Not Found`: Requested project key or resource does not exist.
* `422 Unprocessable Entity`: Validation failure on input parameters.
* `500 Internal Server Error`: Unexpected server-side error.

---

## 4. Canonical REST API Endpoints

### 4.1 `GET /api/v1/projects`

* **Purpose**: Retrieve a paginated, filterable catalog of infrastructure projects with composite risk scores and intervention badges.
* **HTTP Method**: `GET`
* **Path**: `/api/v1/projects`
* **Query Parameters**:
  | Parameter | Type | Default | Constraints / Allowed Values | Description |
  | :--- | :--- | :--- | :--- | :--- |
  | `page` | Integer | `1` | $\ge 1$ | 1-indexed page number |
  | `page_size` | Integer | `20` | $1 \le \text{size} \le 100$ | Items per page |
  | `state` | String | `null` | Valid Indian state name | Filter by geographic state |
  | `agency` | String | `null` | Valid CPSE / agency name | Filter by executing agency |
  | `tier` | String | `null` | `Tier 1`, `Tier 2`, `Tier 3`, `Tier 4` | Filter by attention tier |
  | `coverage` | String | `null` | `FULL`, `PARTIAL` | Filter by data coverage status |
  | `sort_by` | String | `portfolio_rank` | `portfolio_rank`, `attention_score`, `cost_risk_probability`, `project_name` | Sort column |
  | `order` | String | `asc` | `asc`, `desc` | Sort direction |
* **Response Status**: `200 OK`
* **Response Schema**:
```json
{
  "total_records": 437,
  "page": 1,
  "page_size": 20,
  "total_pages": 22,
  "data": [
    {
      "canonical_project_key": "proj_16723_02b9f3d9",
      "source_project_id": 16723,
      "project_name": "LALITPUR-SATNA-REWA-SINGRULI NL",
      "state": "Madhya Pradesh",
      "agency": "WEST CENTRAL RAILWAY",
      "attention_score": 0.9980,
      "attention_tier": "Tier 1",
      "portfolio_rank": 1,
      "risk_coverage": "FULL",
      "cost_risk_probability": 0.9980,
      "schedule_risk_probability": 0.9700,
      "compound_exposure": 0.9700,
      "intervention_priority": "PRIORITY_1",
      "primary_action": "JOINT_COST_SCHEDULE_REVIEW"
    }
  ]
}
```

---

### 4.2 `GET /api/v1/projects/{canonical_project_key}`

* **Purpose**: Retrieve a comprehensive unified profile for a single project, merging administrative metadata, multi-hazard risk scores, explainable drivers, and intervention directives.
* **HTTP Method**: `GET`
* **Path**: `/api/v1/projects/{canonical_project_key}`
* **Path Parameters**:
  | Parameter | Type | Description |
  | :--- | :--- | :--- |
  | `canonical_project_key` | String | Unique project identifier (e.g. `PROJ-PAIMANA-400119`; note: `proj_16723_02b9f3d9` in JSON examples is an illustrative mock key) |
* **Response Status**: `200 OK` (or `404 Not Found`)
* **Response Schema**:
```json
{
  "project": {
    "canonical_project_key": "proj_16723_02b9f3d9",
    "source_project_id": 16723,
    "project_name": "LALITPUR-SATNA-REWA-SINGRULI NL",
    "state": "Madhya Pradesh",
    "agency": "WEST CENTRAL RAILWAY",
    "original_cost_crore": 247.66,
    "cumulative_expenditure_crore": 5214.37,
    "physical_progress_pct": 58.0,
    "divergence": 20.47,
    "project_age_months": 322.0,
    "remaining_duration_months": -120.0,
    "snapshot_date": "2025-07-01"
  },
  "risk": {
    "attention_score": 0.9980,
    "portfolio_rank": 1,
    "attention_tier": "Tier 1",
    "risk_coverage": "FULL",
    "cost_risk_probability": 0.9980,
    "schedule_risk_probability": 0.9700,
    "compound_exposure": 0.9700,
    "is_eligible_cost_target": 1,
    "is_eligible_schedule_target": 1,
    "models": {
      "cost_model": "RandomForestClassifier",
      "cost_probability_variant": "raw_uncalibrated",
      "schedule_model": "RandomForestClassifier",
      "schedule_probability_variant": "raw_uncalibrated"
    },
    "scoring_method_version": "module4_v1"
  },
  "intervention": {
    "intervention_priority": "PRIORITY_1",
    "primary_action": "JOINT_COST_SCHEDULE_REVIEW",
    "secondary_action": "PROGRESS_VERIFICATION",
    "risk_focus": "JOINT_COST_SCHEDULE",
    "priority_reason": "High joint cost and schedule risk. Divergence 20.47 indicates expenditure outpacing physical progress.",
    "evidence_feature": "feat_physical_vs_financial_divergence",
    "evidence_value": 20.47,
    "evidence_direction": "INCREASES_RISK",
    "data_quality_flag": "COMPLETE_BASELINE_DATA",
    "governance_note": "Intervention advisory protocol only. Automated sanctions or budget freezes are strictly prohibited."
  }
}
```

---

### 4.3 `GET /api/v1/projects/ranking`

* **Purpose**: Retrieve the portfolio ranking leaderboard ordered strictly by `portfolio_rank` ascending (1 to 419).
* **HTTP Method**: `GET`
* **Path**: `/api/v1/projects/ranking`
* **Query Parameters**:
  | Parameter | Type | Default | Constraints | Description |
  | :--- | :--- | :--- | :--- | :--- |
  | `limit` | Integer | `50` | $1 \le \text{limit} \le 437$ | Maximum records to return |
  | `offset` | Integer | `0` | $\ge 0$ | Record offset for pagination |
  | `tier` | String | `null` | `Tier 1`, `Tier 2`, `Tier 3`, `Tier 4` | Filter by attention tier |
  | `coverage` | String | `null` | `FULL`, `PARTIAL` | Filter by coverage |
* **Ordering Guarantee**: Results are **strictly guaranteed** to be ordered by `portfolio_rank ASC`, secondary by `canonical_project_key ASC`.
* **Response Status**: `200 OK`
* **Response Schema**:
```json
{
  "total_records": 437,
  "limit": 50,
  "offset": 0,
  "data": [
    {
      "portfolio_rank": 1,
      "canonical_project_key": "proj_16723_02b9f3d9",
      "source_project_id": 16723,
      "project_name": "LALITPUR-SATNA-REWA-SINGRULI NL",
      "state": "Madhya Pradesh",
      "agency": "WEST CENTRAL RAILWAY",
      "attention_score": 0.9980,
      "attention_tier": "Tier 1",
      "risk_coverage": "FULL",
      "cost_risk_probability": 0.9980,
      "schedule_risk_probability": 0.9700,
      "compound_exposure": 0.9700,
      "intervention_priority": "PRIORITY_1",
      "primary_action": "JOINT_COST_SCHEDULE_REVIEW"
    }
  ]
}
```

---

### 4.4 `GET /api/v1/projects/{canonical_project_key}/risk`

* **Purpose**: Retrieve isolated multi-hazard risk evaluation metrics, probabilities, and model execution metadata for a project.
* **HTTP Method**: `GET`
* **Path**: `/api/v1/projects/{canonical_project_key}/risk`
* **Path Parameters**:
  | Parameter | Type | Description |
  | :--- | :--- | :--- |
  | `canonical_project_key` | String | Unique project identifier |
* **Response Status**: `200 OK` (or `404 Not Found`)
* **Response Schema**:
```json
{
  "canonical_project_key": "proj_16723_02b9f3d9",
  "attention_score": 0.9980,
  "portfolio_rank": 1,
  "attention_tier": "Tier 1",
  "risk_coverage": "FULL",
  "cost_risk_probability": 0.9980,
  "schedule_risk_probability": 0.9700,
  "compound_exposure": 0.9700,
  "is_eligible_cost_target": 1,
  "is_eligible_schedule_target": 1,
  "models": {
    "cost_model": "RandomForestClassifier",
    "cost_probability_variant": "raw_uncalibrated",
    "schedule_model": "RandomForestClassifier",
    "schedule_probability_variant": "raw_uncalibrated"
  },
  "scoring_method_version": "module4_v1",
  "snapshot_date": "2025-07-01",
  "prediction_cutoff_date": "2025-07-01"
}
```

> [!NOTE]
> For `PARTIAL` coverage projects, `schedule_risk_probability` is `null`, `compound_exposure` is `null`, and `is_eligible_schedule_target` is `0`.

---

### 4.5 `GET /api/v1/projects/{canonical_project_key}/drivers`

* **Purpose**: Retrieve explainable risk drivers (top 3 marginal reference perturbation signals and factual MoSPI context) for both cost and schedule tasks.
* **HTTP Method**: `GET`
* **Path**: `/api/v1/projects/{canonical_project_key}/drivers`
* **Path Parameters**:
  | Parameter | Type | Description |
  | :--- | :--- | :--- |
  | `canonical_project_key` | String | Unique project identifier |
* **Response Status**: `200 OK` (or `404 Not Found`)
* **Response Schema**:
```json
{
  "canonical_project_key": "proj_16723_02b9f3d9",
  "cost_drivers": {
    "task": "cost_overrun",
    "is_eligible": 1,
    "predicted_risk_probability": 0.9980,
    "top_drivers": [
      {
        "rank": 1,
        "feature": "feat_physical_vs_financial_divergence",
        "feature_value": 20.47,
        "impact": 0.1245,
        "direction": "INCREASES_RISK",
        "source_fact": "Expenditure ratio (21.05) exceeds physical progress (58.00%) by 20.47 divergence index."
      },
      {
        "rank": 2,
        "feature": "feat_project_age_months",
        "feature_value": 322.0,
        "impact": 0.0812,
        "direction": "INCREASES_RISK",
        "source_fact": "Project has been active for 322.0 months since original sanction date."
      },
      {
        "rank": 3,
        "feature": "feat_cumulative_expenditure_crore",
        "feature_value": 5214.37,
        "impact": 0.0543,
        "direction": "INCREASES_RISK",
        "source_fact": "Recorded cumulative expenditure is ₹5,214.37 Crore against ₹247.66 Crore baseline."
      }
    ]
  },
  "schedule_drivers": {
    "task": "schedule_slippage",
    "is_eligible": 1,
    "predicted_risk_probability": 0.9700,
    "top_drivers": [
      {
        "rank": 1,
        "feature": "feat_remaining_original_duration_months",
        "feature_value": -120.0,
        "impact": 0.1420,
        "direction": "INCREASES_RISK",
        "source_fact": "Project is 120.0 months past its originally sanctioned completion date."
      },
      {
        "rank": 2,
        "feature": "feat_physical_progress_pct",
        "feature_value": 58.0,
        "impact": 0.0760,
        "direction": "INCREASES_RISK",
        "source_fact": "Cumulative physical completion is at 58.00%."
      },
      {
        "rank": 3,
        "feature": "feat_expenditure_to_original_cost_ratio",
        "feature_value": 21.05,
        "impact": 0.0410,
        "direction": "INCREASES_RISK",
        "source_fact": "Cumulative expenditure ratio has reached 21.05."
      }
    ]
  },
  "explanation_method": "tree_feature_importance_marginal_perturbation_v1",
  "disclaimer": "Feature attributions reflect statistical associations observed in retrospective MoSPI holdout cohorts; they do not establish causal fault or contractor liability."
}
```

> [!NOTE]
> If `schedule_drivers.is_eligible == 0` (for `PARTIAL` coverage), `predicted_risk_probability` is `null` and `top_drivers` is an empty list `[]`.

---

### 4.6 `GET /api/v1/projects/{canonical_project_key}/interventions`

* **Purpose**: Retrieve concrete monitoring intervention recommendations, protocol checklists, and governance advisory guidelines for a project.
* **HTTP Method**: `GET`
* **Path**: `/api/v1/projects/{canonical_project_key}/interventions`
* **Path Parameters**:
  | Parameter | Type | Description |
  | :--- | :--- | :--- |
  | `canonical_project_key` | String | Unique project identifier |
* **Response Status**: `200 OK` (or `404 Not Found`)
* **Response Schema**:
```json
{
  "canonical_project_key": "proj_16723_02b9f3d9",
  "intervention_priority": "PRIORITY_1",
  "primary_action": "JOINT_COST_SCHEDULE_REVIEW",
  "secondary_action": "PROGRESS_VERIFICATION",
  "risk_focus": "JOINT_COST_SCHEDULE",
  "priority_reason": "High joint cost and schedule risk. Divergence 20.47 indicates expenditure outpacing physical progress.",
  "evidence_feature": "feat_physical_vs_financial_divergence",
  "evidence_value": 20.47,
  "evidence_direction": "INCREASES_RISK",
  "data_quality_flag": "COMPLETE_BASELINE_DATA",
  "governance_note": "Intervention advisory protocol only. Automated sanctions or budget freezes are strictly prohibited."
}
```

---

### 4.7 `GET /api/v1/portfolio/summary`

* **Purpose**: Retrieve portfolio-wide statistical aggregates, coverage distributions, attention tier counts, and action breakdowns for executive surveillance dashboards.
* **HTTP Method**: `GET`
* **Path**: `/api/v1/portfolio/summary`
* **Response Status**: `200 OK`
* **Response Schema**:
```json
{
  "total_projects": 437,
  "coverage_breakdown": {
    "full_coverage": 305,
    "partial_coverage": 132
  },
  "tier_distribution": {
    "Tier 1": 44,
    "Tier 2": 73,
    "Tier 3": 102,
    "Tier 4": 218
  },
  "intervention_priority_distribution": {
    "PRIORITY_1": 44,
    "PRIORITY_2": 73,
    "PRIORITY_3": 102,
    "PRIORITY_4": 218
  },
  "action_distribution": {
    "DATA_QUALITY_REVIEW": 128,
    "JOINT_COST_SCHEDULE_REVIEW": 90,
    "SCHEDULE_REVIEW": 81,
    "COMPLETION_STATUS_REVIEW": 79,
    "COST_REVIEW": 29,
    "PROGRESS_VERIFICATION": 24,
    "EXPENDITURE_PROGRESS_REVIEW": 6
  },
  "risk_focus_distribution": {
    "SCHEDULE_RISK": 159,
    "UNOBSERVED_SCHEDULE": 128,
    "JOINT_COST_SCHEDULE": 90,
    "COST_RISK": 29,
    "BASELINE_MONITORING": 24,
    "PROGRESS_FINANCIAL_DIVERGENCE": 6,
    "COMPLETION_STATUS": 1
  }
}
```

---

## 5. Contractual Invariants for Frontend & Backend Engineers

1. **Do Not Mutate Frozen Semantics**: Frontend and backend implementations must adhere strictly to these 7 endpoints and schemas. Neither team is permitted to invent new calculated risk fields or change mathematical formulas.
2. **Backend Representation Normalization**: The backend data access layer reads `"Raw / Uncalibrated"` from relational stores or CSVs and serializes it as `"raw_uncalibrated"` in all API responses.
3. **Frontend Presentation Rule**:
   - `attention_score` is displayed as an Attention Index (`0.0%` to `100.0%`).
   - Tiers are styled with consistent neutral colors (Tier 1: Red/Urgent Review, Tier 2: Amber/High Attention, Tier 3: Yellow/Elevated Focus, Tier 4: Blue/Standard Cadence).
   - Incomplete schedule observations in `PARTIAL` projects must display an explicit `"PARTIAL COVERAGE"` badge with `"Schedule Unobserved"` callout. Never render `0.0%` or `-`.

# Module 4 — Phase 8: Product Contract & Intelligence Specification

**Project**: SIH26103 — PAIMANA Predictive Risk Intelligence  
**Document Type**: Technical Interface Contract & Data Specification  
**Status**: Frozen & Authoritative  
**Date**: September 2026  
**Pipeline Coverage**: Modules 1 through 4 (Canonical Snapshots, Identity Resolution, PIT Features, Model Evaluation, Calibration, Risk Scoring, Quality Audit, Explainability, Intervention Prioritisation)

---

## 1. Executive Summary & Purpose

This document constitutes the formal **Product Contract** governing the data interfaces, statistical interpretations, semantic boundaries, and display rules for the PAIMANA Predictive Risk Intelligence system.

The PAIMANA system transitions project monitoring from retrospective historical accounting to prospective, point-in-time predictive surveillance. It processes longitudinal infrastructure project snapshots from the Ministry of Statistics and Programme Implementation (MoSPI) and produces calibrated, auditable risk intelligence.

### 1.1 Core Mission
The system answers three operational questions for infrastructure monitoring executives:
1. **Which projects demand immediate monitoring attention?** (Ranked by prospective risk severity)
2. **What observable project attributes are statistically driving that risk?** (Explainable feature contributions grounded in point-in-time observed facts)
3. **What concrete monitoring interventions should portfolio managers deploy?** (Evidence-grounded action prioritization)

### 1.2 Core Invariants & Boundaries
* **Non-Causal Principle**: All model probabilities and feature attributions represent statistical associations observed in historical retrospective holdout data. They do **not** imply causality, culpability, or operational incompetence.
* **No Automated Decisions or Punitive Actions**: The system is an advisory surveillance layer. It **never** automates budget sanctions, contractor blacklisting, contractual penalties, or fund de-allocation.
* **Point-in-Time Integrity**: All predictions reflect data available strictly on or before the July 2025 snapshot date. No future data leaks into the intelligence layer.
* **Explicit Uncertainty**: Incomplete information (such as missing schedule milestones) is explicitly surfaced as `PARTIAL` coverage and unobserved status, never hidden behind zero-risk or default assumptions.

---

## 2. Canonical Data Lineage & Frozen Artifact Manifest

The entire Module 4 intelligence chain is generated from frozen upstream artifacts. Any modification to these files violates system integrity.

```
[Canonical Monthly Snapshots (Tables 7, 4, 6)]
                     │
                     ▼
       [Canonical Snapshot Panel]
                     │
                     ▼
          [PIT Feature Dataset]
     (July 2025 Features -> July 2026 Targets)
                     │
                     ▼
    ┌─────────────────────────────────┐
    │  ML Risk Scoring Engine (M4.4)  │
    │  - Cost RF Model                │
    │  - Schedule RF Model            │
    └────────────────┬────────────────┘
                     │
                     ▼
     data/processed/project_risk_scores.csv (N=437, 21 cols)
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
data/interim/           data/processed/
project_risk_           project_intervention_
explanations.csv        priorities.csv
(N=874, 29 cols)        (N=437, 16 cols)
```

### 2.1 Frozen Artifact Checksums (SHA-256)

| Artifact Path | SHA-256 Checksum | Records | Purpose |
| :--- | :--- | :--- | :--- |
| `data/interim/pit_features_july2025_to_july2026.csv` | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | 437 | Frozen Point-in-Time features & retrospective targets |
| `data/processed/project_risk_scores.csv` | `6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d` | 437 | Multi-hazard risk probabilities, attention score & tiers |
| `data/interim/project_risk_explanations.csv` | `5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2` | 874 | Top 3 explainable risk drivers & source facts (Cost & Schedule) |
| `data/processed/project_intervention_priorities.csv` | `3dfacd2805610e0a1a9ff3f10461c97322a3bf62ca1dc348fc6baca13e012ec5` | 437 | Evidence-grounded intervention prioritization & governance |

---

## 3. Data Dictionary & Entity Specifications

The Module 4 contract exposes four core entities. Downstream consumers (backend APIs, relational stores, frontend clients) must adhere strictly to these schemas.

### 3.1 Entity 1: Canonical Project Metadata (`projects`)
Derived from upstream canonical snapshots and the identity resolution map.

| Field Name | Type | Nullable | Description / Domain |
| :--- | :--- | :--- | :--- |
| `canonical_project_key` | String | No | Primary Key. Formatted as `proj_{normalized_id}_{hash}` (e.g. `proj_16723_02b9f3d9`). |
| `source_project_id` | Integer | No | Original MoSPI project identifier from Table 4 / Table 7. |
| `project_name` | String | No | Official project title as recorded in canonical MoSPI tables. |
| `state` | String | No | Primary state or multi-state jurisdiction where project is located. |
| `agency` | String | No | Central Public Sector Enterprise (CPSE) or executing authority. |
| `original_cost_crore` | Float | No | Baseline sanctioned cost in ₹ Crores (must be $> 0$). |
| `cumulative_expenditure_crore`| Float | No | Cumulative recorded financial outlay in ₹ Crores as of snapshot date. |
| `expenditure_ratio` | Float | No | Ratio of cumulative expenditure to original cost. |
| `physical_progress_pct` | Float | No | Cumulative reported physical progress percentage ($[0.0, 100.0]$). |
| `divergence` | Float | No | Divergence: `expenditure_ratio - (physical_progress_pct / 100.0)`. |
| `project_age_months` | Float | No | Elapsed months since sanction/approval date as of July 2025. |
| `remaining_duration_months` | Float | Yes | Months remaining until original completion date; negative if past completion. |
| `snapshot_date` | String | No | ISO Date: `2025-07-01` (Point-in-Time observation cutoff). |

### 3.2 Entity 2: Project Risk Scores (`project_risk_scores`)
Output of the Phase 4 multi-hazard scoring engine ($N=437$ records).

| Field Name | Type | Nullable | Domain / Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `canonical_project_key` | String | No | Foreign Key $	o$ `projects.canonical_project_key` | Unique identifier. |
| `source_project_id` | Integer | No | Positive integer | MoSPI ID. |
| `project_name` | String | No | String | Project name. |
| `state` | String | No | String | State name. |
| `agency` | String | No | String | Agency name. |
| `snapshot_date` | String | No | `2025-07-01` | Observation snapshot. |
| `prediction_cutoff_date` | String | No | `2025-07-01` | Predictive boundary. |
| `is_eligible_cost_target` | Integer | No | `1` | All 437 projects meet cost target eligibility. |
| `is_eligible_schedule_target` | Integer | No | `0` or `1` | `1` if baseline schedule dates available ($N=305$), `0` if unavailable ($N=132$). |
| `cost_risk_probability` | Float | No | $[0.0, 1.0]$ | Model-estimated probability of prospective cost overrun $> 5\%$. |
| `schedule_risk_probability` | Float | Yes | $[0.0, 1.0]$ for eligible; `NULL` for ineligible | Model-estimated probability of schedule slippage $\ge 3$ months. |
| `risk_coverage` | String | No | `FULL` ($N=305$) or `PARTIAL` ($N=132$) | Coverage status. |
| `attention_score` | Float | No | $[0.0, 1.0]$ | $\max(P_c, P_s)$ if FULL; $P_c$ if PARTIAL. |
| `compound_exposure` | Float | Yes | $[0.0, 1.0]$ if FULL; `NULL` if PARTIAL | $\min(P_c, P_s)$ measuring co-occurring high risk across hazards. |
| `attention_tier` | String | No | `Tier 1`, `Tier 2`, `Tier 3`, `Tier 4` | Quantile-based priority tier. |
| `portfolio_rank` | Integer | No | $1 \le 	ext{rank} \le 419$ | Dense min-rank descending by `attention_score`. |
| `cost_model_name` | String | No | `RandomForestClassifier` | Frozen candidate architecture. |
| `schedule_model_name` | String | No | `RandomForestClassifier` | Frozen candidate architecture. |
| `cost_probability_variant` | String | No | `raw_uncalibrated` | Empirical selection from Phase 6. |
| `schedule_probability_variant` | String | No | `raw_uncalibrated` | Empirical selection from Phase 6. |
| `scoring_method_version` | String | No | `module4_v1` | Scoring formula version tag. |

### 3.3 Entity 3: Project Risk Explanations (`project_risk_explanations`)
Output of the Phase 6 explainability engine ($N=874$ records; exactly 2 rows per project: one for `cost_overrun` and one for `schedule_slippage`).

| Field Name | Type | Nullable | Description / Domain |
| :--- | :--- | :--- | :--- |
| `canonical_project_key` | String | No | Foreign Key $	o$ `projects.canonical_project_key`. |
| `source_project_id` | Integer | No | MoSPI ID. |
| `project_name` | String | No | Project name. |
| `state` | String | No | State name. |
| `agency` | String | No | Agency name. |
| `task` | String | No | `cost_overrun` ($N=437$) or `schedule_slippage` ($N=437$). |
| `is_eligible_task_target` | Integer | No | `1` if task evaluated; `0` if ineligible (e.g. Schedule task for PARTIAL projects). |
| `predicted_risk_probability` | Float | Yes | Task risk probability; `NULL` for ineligible tasks. |
| `attention_score` | Float | No | Overall project attention score. |
| `attention_tier` | String | No | Tier 1 to Tier 4. |
| `portfolio_rank` | Integer | No | Portfolio rank. |
| `risk_coverage` | String | No | `FULL` or `PARTIAL`. |
| `top_1_feature` | String | Yes | Primary statistical driver (e.g. `feat_physical_vs_financial_divergence`). |
| `top_1_feature_value` | Float | Yes | Standardized value of primary feature in PIT dataset. |
| `top_1_impact` | Float | Yes | Local marginal perturbation impact magnitude. |
| `top_1_direction` | String | Yes | `INCREASES_RISK`, `DECREASES_RISK`, or `NEUTRAL`. |
| `top_1_source_fact` | String | Yes | Human-readable explanation grounded in MoSPI snapshot facts. |
| `top_2_feature` | String | Yes | Secondary statistical driver. |
| `top_2_feature_value` | Float | Yes | Standardized value of secondary feature. |
| `top_2_impact` | Float | Yes | Local marginal perturbation impact magnitude. |
| `top_2_direction` | String | Yes | `INCREASES_RISK`, `DECREASES_RISK`, or `NEUTRAL`. |
| `top_2_source_fact` | String | Yes | Human-readable source fact. |
| `top_3_feature` | String | Yes | Tertiary statistical driver. |
| `top_3_feature_value` | Float | Yes | Standardized value of tertiary feature. |
| `top_3_impact` | Float | Yes | Local marginal perturbation impact magnitude. |
| `top_3_direction` | String | Yes | `INCREASES_RISK`, `DECREASES_RISK`, or `NEUTRAL`. |
| `top_3_source_fact` | String | Yes | Human-readable source fact. |
| `explanation_method` | String | No | `tree_feature_importance_marginal_perturbation_v1`. |
| `explanation_disclaimer` | String | No | Mandatory non-causal disclaimer text. |

### 3.4 Entity 4: Project Intervention Priorities (`project_intervention_priorities`)
Output of the Phase 7 intervention engine ($N=437$ records).

| Field Name | Type | Nullable | Domain / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- |
| `canonical_project_key` | String | No | Foreign Key $	o$ `projects.canonical_project_key` | Unique identifier. |
| `cost_risk_probability` | Float | No | $[0.0, 1.0]$ | Cost risk probability. |
| `schedule_risk_probability` | Float | Yes | $[0.0, 1.0]$ or `NULL` | Schedule risk probability. |
| `attention_score` | Float | No | $[0.0, 1.0]$ | Overall attention score. |
| `risk_coverage` | String | No | `FULL` or `PARTIAL` | Coverage indicator. |
| `portfolio_rank` | Integer | No | $1 \le 	ext{rank} \le 419$ | Min-rank descending by attention score. |
| `intervention_priority` | String | No | `PRIORITY_1` ($N=44$), `PRIORITY_2` ($N=73$), `PRIORITY_3` ($N=102$), `PRIORITY_4` ($N=218$) | Action urgency level. |
| `primary_action` | String | No | Controlled action taxonomy (Section 5.1) | Main recommended monitoring protocol. |
| `secondary_action` | String | No | Controlled action taxonomy | Complementary follow-up protocol. |
| `risk_focus` | String | No | Controlled risk focus taxonomy (Section 5.2) | Hazard dimension requiring focus. |
| `priority_reason` | String | No | Text | Clear non-causal explanation of assignment rationale. |
| `evidence_feature` | String | No | Feature name from PIT schema | Top observable feature driving assignment. |
| `evidence_value` | Float | No | Numerical value | Value of evidence feature. |
| `evidence_direction` | String | No | `INCREASES_RISK`, `DECREASES_RISK`, `NEUTRAL` | Impact direction. |
| `data_quality_flag` | String | No | `COMPLETE_BASELINE_DATA` ($N=304$), `SCHEDULE_OUTCOME_UNOBSERVED` ($N=132$), `MISSING_APPROVAL_DATE` ($N=1$) | Data completeness indicator. |
| `governance_note` | String | No | Text | Mandatory non-punitive governance disclaimer. |

---

## 4. Mathematical Semantics & Semantic Invariants

### 4.1 Cost Risk Probability ($P_c$)
$$P_c = P(Y_{	ext{cost}} = 1 \mid X_{	ext{PIT}})$$
Where $Y_{	ext{cost}} = 1$ denotes a prospective cumulative cost overrun $> 5\%$ between the July 2025 baseline and the July 2026 evaluation date. Available for all 437 projects.

### 4.2 Schedule Risk Probability ($P_s$)
$$P_s = P(Y_{	ext{schedule}} = 1 \mid X_{	ext{PIT}})$$
Where $Y_{	ext{schedule}} = 1$ denotes a prospective completion milestone slippage $\ge 3$ months.
* Defined **only** when `is_eligible_schedule_target == 1` ($N=305$).
* **Critical Null Contract**: When `is_eligible_schedule_target == 0` ($N=132$), $P_s$ is strictly `NULL`. Downstream systems MUST NOT impute $0.0$, $-1$, or any arbitrary scalar.

### 4.3 Attention Score
$$\text{attention\_score} = \begin{cases} \max(P_c, P_s) & \text{if } \text{risk\_coverage} = \text{FULL} \\ P_c & \text{if } \text{risk\_coverage} = \text{PARTIAL} \end{cases}$$
The attention score acts as a conservative multi-hazard sentinel: if an asset exhibits critical vulnerability in *either* dimension, it elevates to executive visibility. **$\text{attention\_score} = \max(P_c, P_s)$ is a comparative portfolio prioritization index, not a calibrated probability of joint failure.**

### 4.4 Compound Exposure
$$	ext{compound\_exposure} =  egin{cases} \min(P_c, P_s) & 	ext{if } 	ext{risk\_coverage} = 	ext{FULL} \ 	ext{NULL} & 	ext{if } 	ext{risk\_coverage} = 	ext{PARTIAL} \end{cases}$$
* **Mathematical Semantic**: Measures concurrent vulnerability. High compound exposure indicates that a project is severely distressed across both financial outlays and completion milestones simultaneously.
* **Prohibited Representation**: Compound exposure MUST NEVER be communicated or represented as a joint probability $P(	ext{Cost} \cap 	ext{Schedule})$. In uncalibrated models, $\min(P_c, P_s)$ is an operational heuristic, not the product or joint distribution of independent events.

### 4.5 Portfolio Attention Tiers
Tiers are determined strictly by empirical quantile thresholds on the 437-project portfolio:
* **Tier 1** ($\ge Q90 = 0.994667$): Top 10% highest attention scores ($N=44$).
* **Tier 2** ($\ge Q75 = 0.983333 	ext{ and } < Q90$): 75th to 90th percentile ($N=73$).
* **Tier 3** ($\ge Q50 = 0.906667 	ext{ and } < Q75$): 50th to 75th percentile ($N=102$).
* **Tier 4** ($< Q50$): Lower 50% attention scores ($N=218$).

> [!WARNING]
> **Prohibited Tier Terminology**: Downstream user interfaces, API documentation, and pitch decks MUST NOT label Tiers 1 through 4 as "Critical / High / Medium / Low Risk". Tiers reflect relative quantile prioritization within this specific cohort, not absolute probabilistic severity.

---

## 5. Intervention & Action Taxonomy

### 5.1 Controlled Action Taxonomy
Intervention actions are strictly constrained to the following standardized protocols:

1. **`DATA_QUALITY_REVIEW`** ($N=128$ primary): Audit and update missing baseline milestone dates, approval documents, and completion estimates.
2. **`JOINT_COST_SCHEDULE_REVIEW`** ($N=90$ primary): Convene joint technical committee to address concurrent cost overrun and schedule slippage risks.
3. **`SCHEDULE_REVIEW`** ($N=81$ primary): Review critical path execution milestones and contractor deployment schedules.
4. **`COMPLETION_STATUS_REVIEW`** ($N=79$ primary): Re-baseline completion dates for projects operating past their original completion targets.
5. **`COST_REVIEW`** ($N=29$ primary): Conduct expenditure audit on projects exhibiting high financial outlay escalation.
6. **`PROGRESS_VERIFICATION`** ($N=24$ primary, $N=231$ secondary): Inspect on-site physical progress against reported expenditure milestones.
7. **`EXPENDITURE_PROGRESS_REVIEW`** ($N=6$ primary, $N=24$ secondary): Investigate severe divergence between financial expenditure and physical progress.

### 5.2 Controlled Risk Focus Taxonomy
1. `SCHEDULE_RISK` ($N=159$)
2. `UNOBSERVED_SCHEDULE` ($N=128$)
3. `JOINT_COST_SCHEDULE` ($N=90$)
4. `COST_RISK` ($N=29$)
5. `BASELINE_MONITORING` ($N=24$)
6. `PROGRESS_FINANCIAL_DIVERGENCE` ($N=6$)
7. `COMPLETION_STATUS` ($N=1$)

### 5.3 Priority Mapping Contract
* `PRIORITY_1` ($N=44$): All projects in Tier 1. Demands executive review within 14 business days.
* `PRIORITY_2` ($N=73$): All projects in Tier 2. Demands monthly committee review.
* `PRIORITY_3` ($N=102$): All projects in Tier 3. Demands standard quarterly milestone tracking.
* `PRIORITY_4` ($N=218$): All projects in Tier 4. Standard reporting cadence only.

---

## 6. Frontend Display & Formatting Guidelines

1. **Probability Display**: Render model probabilities as percentages rounded to one decimal place (e.g. `0.9973` $	o$ `99.7%`, `0.0210` $	o$ `2.1%`).
2. **Partial Coverage Rendering**:
   - In tables and detail cards, never show blank or 0% for unobserved schedule risk.
   - Display a distinct badge: `PARTIAL COVERAGE`.
   - In place of schedule probability, display: `Unobserved (Baseline dates missing)`.
   - In place of compound exposure, display: `N/A (Schedule unobserved)`.
3. **Governance Badges**:
   - Every intervention recommendation card MUST feature an immutable governance notice:  
     *“Advisory intelligence for human oversight. Automated sanctions or budget reallocations are strictly prohibited.”*
4. **Driver Panel Rendering**:
   - For every driver, display the human-readable source fact alongside the statistical direction badge (`Increases Attention` or `Decreases Attention`).
   - Clearly display the disclaimer: *“Statistical associations derived from historical MoSPI snapshots. These indicators highlight monitoring focus areas and do not establish causal fault.”*

---

## 7. Data Lineage, Security & Auditing

* **Immutable Run Records**: Every scoring run must preserve `scoring_method_version`, `prediction_cutoff_date`, and model architecture identifiers.
* **Audit Trail**: Any manual modification of a project's intervention status by an analyst in the future UI must record: `analyst_id`, `timestamp`, `original_action`, `modified_action`, `justification_notes`.
* **Reproducibility**: Feeding the frozen PIT dataset into the Module 4 scripts must yield bitwise identical output CSVs matching the frozen SHA-256 hashes.

# Module 4 — Phase 7: Intervention Prioritisation Architecture

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 4 — Risk Scoring & Decision Intelligence  
**Phase:** 7 — Intervention Prioritisation  
**Document:** `reports/module4_intervention_prioritisation.md`  
**Dataset Reference:** `data/processed/project_intervention_priorities.csv`  
**Evaluation Date:** September 5, 2026  
**Status:** **FROZEN DECISION-SUPPORT SPECIFICATION & INTERVENTION ARTIFACT**  

---

## 1. Objective

Module 4 Phase 7 operationalizes the predictive scores (Phase 4), quality audit (Phase 5), and explainable drivers (Phase 6) into an evidence-grounded **Intervention Prioritisation Layer**.

The objective of this layer is to answer five critical administrative monitoring questions for infrastructure stakeholders:
1. **What type of risk requires attention?** (Cost overrun, schedule slippage, joint exposure, or unobserved trajectory).
2. **Why is this project being prioritised?** (Traceable statistical model elevation and specific physical signals).
3. **What monitoring/action category is appropriate?** (Targeted reviews, e.g., `COST_REVIEW`, `SCHEDULE_REVIEW`, `COMPLETION_STATUS_REVIEW`).
4. **What observable evidence supports that recommendation?** (Explicit point-in-time features and observed values).
5. **What information is missing or uncertain?** (Missing schedule outcomes or unrecorded approval dates).

> [!IMPORTANT]
> **Governance Declaration:**  
> These intervention priorities are monitoring recommendations derived from evaluated model signals and observed point-in-time data. They are **not** autonomous administrative decisions, engineering certifications, causal conclusions, or guaranteed outcomes.

---

## 2. Input Artifacts & Immutability

The intervention prioritisation engine operates deterministically over frozen inputs without training new machine learning models:

| Input Artifact | Role | Verified SHA-256 | Immutability Status |
|---|---|---|:---:|
| `data/interim/pit_features_july2025_to_july2026.csv` | Observed Point-in-Time Features | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | FROZEN |
| `data/processed/project_risk_scores.csv` | Probabilities, Attention Tiers, & Portfolio Ranks | `6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d` | FROZEN |
| `data/interim/project_risk_explanations.csv` | Local Feature Impacts & Observable Source Facts | `5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2` | FROZEN |

---

## 3. Deterministic Intervention Logic & Action Taxonomy

### 3.1 Permitted Operational Actions (Conservative Review Categories)
To prevent operational overreach and preserve domain judgment, the action space is restricted strictly to procedural monitoring actions:

1. **`JOINT_COST_SCHEDULE_REVIEW`:** Coordinated inter-departmental supervisory review for projects where both cost escalation and schedule slippage risks are simultaneously elevated.
2. **`COST_REVIEW`:** Detailed financial audit and budget utilization examination focused on expenditure escalation, contract variations, and cost commitments.
3. **`SCHEDULE_REVIEW`:** Timeline and critical-path review assessing contractor milestones, procurement delays, and physical commissioning readiness.
4. **`COMPLETION_STATUS_REVIEW`:** Field-level milestone review triggered specifically when a project is past its original scheduled completion date (`feat_is_past_original_completion == 1`).
5. **`EXPENDITURE_PROGRESS_REVIEW`:** Technical and financial alignment review triggered when expenditure ratio heavily diverges from reported physical progress.
6. **`PROGRESS_VERIFICATION`:** Periodic standard physical inspection and progress milestone verification.
7. **`DATA_QUALITY_REVIEW`:** Administrative reporting audit triggered when schedule outcomes are unobserved or key project metadata is missing.

### 3.2 Prohibited Recommendations (Hard Safety Safeguards)
The engine strictly prohibits:
- Budget withholding or funding penalties
- Contract termination or cancellation recommendations
- Causal blame attributed to executing agencies or states
- Engineering fault certifications or contractor liability conclusions
- Autonomous administrative sanctions

---

## 4. Intervention Priority Architecture

The intervention priority categorizes operational urgency without altering the model-derived `portfolio_rank`:

| Intervention Priority | Portfolio Segment | Attention Score Range | Portfolio Projects | Operational Definition |
|:---:|:---:|:---:|:---:|---|
| **`PRIORITY_1`** | Tier 1 (Top 10%) | $A_i \ge 0.994667$ | **44 (10.1%)** | Urgent Supervisory Monitoring: Immediate joint or focused review warranted. |
| **`PRIORITY_2`** | Tier 2 (Next 15%) | $0.983333 \le A_i < 0.994667$ | **73 (16.7%)** | Focused Monitoring: Targeted schedule or expenditure review recommended. |
| **`PRIORITY_3`** | Tier 3 (Next 25%) | $0.906667 \le A_i < 0.983333$ | **102 (23.3%)** | Routine Monitoring: Periodic multi-axis verification recommended. |
| **`PRIORITY_4`** | Tier 4 (Bottom 50%) | $A_i < 0.906667$ | **218 (49.9%)** | Standard Baseline Monitoring & Data Quality Review. |

---

## 5. Output Portfolio Distribution

Audited across all $N=437$ physical projects in `data/processed/project_intervention_priorities.csv`:

### 5.1 Primary Action Distribution

| Primary Action | Total Count | Percentage | Primary Operational Focus |
|---|:---:|:---:|---|
| **`DATA_QUALITY_REVIEW`** | **128** | 29.29% | Schedule outcome unobserved; data hygiene review. |
| **`JOINT_COST_SCHEDULE_REVIEW`** | **90** | 20.59% | Both cost and schedule risks simultaneously elevated ($P_c \ge 0.50, P_s \ge 0.75$). |
| **`SCHEDULE_REVIEW`** | **81** | 18.54% | Elevated schedule risk with future target date ($P_s \ge 0.75, \text{past}=0$). |
| **`COMPLETION_STATUS_REVIEW`** | **79** | 18.08% | Elevated schedule risk where original completion date had already passed. |
| **`COST_REVIEW`** | **29** | 6.64% | Elevated cost risk without joint schedule elevation ($P_c \ge 0.50, P_s < 0.75$). |
| **`PROGRESS_VERIFICATION`** | **24** | 5.49% | Standard baseline monitoring for un-elevated projects. |
| **`EXPENDITURE_PROGRESS_REVIEW`** | **6** | 1.37% | Extreme physical-financial divergence ($\ge 25\%$ points) in lower-risk projects. |
| **Total** | **437** | **100.00%** | Comprehensive reference portfolio coverage. |

### 5.2 Risk Focus Distribution

| Risk Focus Category | Total Count | Percentage | Description |
|---|:---:|:---:|---|
| **`SCHEDULE_RISK`** | **159** | 36.38% | Schedule risk elevated ($P_s \ge 0.75$). |
| **`UNOBSERVED_SCHEDULE`** | **128** | 29.29% | Schedule outcome unobserved; cost risk un-elevated ($P_c < 0.50$). |
| **`JOINT_COST_SCHEDULE`** | **90** | 20.59% | Dual elevated risk across both monitored dimensions. |
| **`COST_RISK`** | **29** | 6.64% | Cost risk elevated ($P_c \ge 0.50$). |
| **`BASELINE_MONITORING`** | **24** | 5.49% | Standard parameters without elevated signals. |
| **`PROGRESS_FINANCIAL_DIVERGENCE`** | **6** | 1.37% | Divergence anomaly in otherwise un-elevated project. |
| **`COMPLETION_STATUS`** | **1** | 0.23% | Milestone verification for past-due baseline project. |
| **Total** | **437** | **100.00%** | Exact portfolio accounting. |

### 5.3 Data Quality Flag Breakdown

| Data Quality Flag | Count | Meaning |
|---|:---:|---|
| **`COMPLETE_BASELINE_DATA`** | **304** | Both dimensions active and approval date recorded. |
| **`SCHEDULE_OUTCOME_UNOBSERVED`** | **132** | MoSPI report contains `(-)` for revised date of commissioning. |
| **`MISSING_APPROVAL_DATE`** | **1** | Government sanction/approval date is missing in official record. |

---

## 6. Manual Audit of Representative Cases

In accordance with Phase 7 audit protocol, 12 specific representative projects were inspected across 4 core operational segments:

### 6.1 High Cost-Risk Projects ($P_c \ge 0.75, P_s < 0.75$ or PARTIAL)

1. **`PROJ-PAIMANA-705481`** (Ramganjmandi-Bhopal New Line Project | West Central Railway [WCR])
   - *Risk Scores:* $P_c = 0.9867$, $P_s = 0.6600$, Attention: `0.9867` (Tier 2, Rank 52)
   - *Intervention:* `COST_REVIEW` (Secondary: `EXPENDITURE_PROGRESS_REVIEW`, Priority: `PRIORITY_2`)
   - *Evidence:* `feat_expenditure_to_original_cost_ratio` = 1.185 (Cumulative expenditure reached 118.5% of sanctioned cost).
   - *Priority Reason:* *"Elevated cost risk is accompanied by expenditure to original cost ratio; cost review is recommended."*
2. **`PROJ-PAIMANA-705358`** (Khurda-Bolangir New Broad Gauge Line | East Coast Railway [ECoR] - I)
   - *Risk Scores:* $P_c = 0.9833$, $P_s = 0.5667$, Attention: `0.9833` (Tier 2, Rank 74)
   - *Intervention:* `COST_REVIEW` (Secondary: `EXPENDITURE_PROGRESS_REVIEW`, Priority: `PRIORITY_2`)
   - *Evidence:* `feat_expenditure_to_original_cost_ratio` = 1.314 (Cumulative expenditure reached 131.4% of sanctioned cost).
3. **`PROJ-PAIMANA-705515`** (3rd & 4th Railway Line Project | Central Railway [CR] - II)
   - *Risk Scores:* $P_c = 0.9767$, $P_s = 0.2367$, Attention: `0.9767` (Tier 3, Rank 94)
   - *Intervention:* `COST_REVIEW` (Secondary: `EXPENDITURE_PROGRESS_REVIEW`, Priority: `PRIORITY_3`)
   - *Evidence:* `feat_expenditure_to_original_cost_ratio` = 1.680 (Cumulative expenditure reached 168.0% of sanctioned cost).

### 6.2 High Schedule-Risk Projects ($P_s \ge 0.85, P_c < 0.30$)

1. **`PROJ-PAIMANA-0609996`** (Construction of Precast housing... | IIT Hyderabad)
   - *Risk Scores:* $P_c = 0.0933$, $P_s = 1.0000$, Attention: `1.0000` (Tier 1, Rank 1)
   - *Intervention:* `COMPLETION_STATUS_REVIEW` (Secondary: `SCHEDULE_REVIEW`, Priority: `PRIORITY_1`)
   - *Evidence:* `feat_is_past_original_completion` = 1.
   - *Priority Reason:* *"Elevated schedule risk is supported by a past-original-completion signal; completion status review is recommended."*
2. **`PROJ-PAIMANA-0612885`** (Construction and Developement of NIT Meghalaya)
   - *Risk Scores:* $P_c = 0.2333$, $P_s = 1.0000$, Attention: `1.0000` (Tier 1, Rank 1)
   - *Intervention:* `COMPLETION_STATUS_REVIEW` (Secondary: `SCHEDULE_REVIEW`, Priority: `PRIORITY_1`)
   - *Evidence:* `feat_is_past_original_completion` = 1.
3. **`PROJ-PAIMANA-0612894`** (Construction of Permanent Campus of CU Himachal Pradesh)
   - *Risk Scores:* $P_c = 0.1700$, $P_s = 1.0000$, Attention: `1.0000` (Tier 1, Rank 1)
   - *Intervention:* `COMPLETION_STATUS_REVIEW` (Secondary: `SCHEDULE_REVIEW`, Priority: `PRIORITY_1`)
   - *Evidence:* `feat_is_past_original_completion` = 1.

### 6.3 Joint-Risk Projects ($P_c \ge 0.80, P_s \ge 0.90$)

1. **`PROJ-PAIMANA-0400119`** (Life Extension of 48 well platforms... | ONGC)
   - *Risk Scores:* $P_c = 0.8033$, $P_s = 1.0000$, Compound: `0.8033`, Attention: `1.0000` (Tier 1, Rank 1)
   - *Intervention:* `JOINT_COST_SCHEDULE_REVIEW` (Secondary: `COMPLETION_STATUS_REVIEW`, Priority: `PRIORITY_1`)
   - *Evidence:* `feat_agency` (ONGC historical cost profile) and `feat_is_past_original_completion` = 1.
   - *Priority Reason:* *"Both evaluated cost and schedule risk are elevated; coordinated cost and schedule review is recommended."*
2. **`PROJ-PAIMANA-0705366`** (Hajipur-Sagauli New line | East Central Railway [ECR] - I)
   - *Risk Scores:* $P_c = 0.9900$, $P_s = 1.0000$, Compound: `0.9900`, Attention: `1.0000` (Tier 1, Rank 1)
   - *Intervention:* `JOINT_COST_SCHEDULE_REVIEW` (Secondary: `COMPLETION_STATUS_REVIEW`, Priority: `PRIORITY_1`)
   - *Evidence:* `feat_project_age_months` = 260 months and `feat_is_past_original_completion` = 1.
3. **`PROJ-PAIMANA-0705450`** (Jogbani-Biratnagar New Rail Line project | IRCON)
   - *Risk Scores:* $P_c = 0.8100$, $P_s = 1.0000$, Compound: `0.8100`, Attention: `1.0000` (Tier 1, Rank 1)
   - *Intervention:* `JOINT_COST_SCHEDULE_REVIEW` (Secondary: `COMPLETION_STATUS_REVIEW`, Priority: `PRIORITY_1`)
   - *Evidence:* Rail cross-border infrastructure trajectory and schedule elapsed status.

### 6.4 PARTIAL Projects (Missing Schedule Target in Source Data)

1. **`PROJ-PAIMANA-0400087`** (Redevelopment of Sobhasan Complex | ONGC)
   - *Risk Scores:* $P_c = 0.8967$, $P_s = \text{NaN}$, Attention: `0.8967` (Tier 4, Rank 141)
   - *Intervention:* `COST_REVIEW` (Secondary: `DATA_QUALITY_REVIEW`, Priority: `PRIORITY_4`)
   - *Evidence:* `feat_agency` = ONGC; `data_quality_flag`: `SCHEDULE_OUTCOME_UNOBSERVED`.
   - *Priority Reason:* *"Elevated cost risk is supported by budget expenditure signals; schedule outcome is unobserved, cost review is recommended."*
2. **`PROJ-PAIMANA-0400151`** (NORTH URIMARI EXPANSION OCP | Central Coalfields Limited [CCL])
   - *Risk Scores:* $P_c = 0.6733$, $P_s = \text{NaN}$, Attention: `0.6733` (Tier 4, Rank 188)
   - *Intervention:* `COST_REVIEW` (Secondary: `DATA_QUALITY_REVIEW`, Priority: `PRIORITY_4`)
   - *Evidence:* `feat_agency` = CCL; `data_quality_flag`: `SCHEDULE_OUTCOME_UNOBSERVED`.
3. **`PROJ-PAIMANA-0617225`** (PCMC To Nigdi- Extension Of North-South Corridor | Maharashtra Metro Rail Corp)
   - *Risk Scores:* $P_c = 0.6467$, $P_s = \text{NaN}$, Attention: `0.6467` (Tier 4, Rank 198)
   - *Intervention:* `COST_REVIEW` (Secondary: `DATA_QUALITY_REVIEW`, Priority: `PRIORITY_4`)
   - *Evidence:* Metro transit early-stage expenditure profile; `data_quality_flag`: `SCHEDULE_OUTCOME_UNOBSERVED`.

---

## 7. Output Dataset Schema (`data/processed/project_intervention_priorities.csv`)

The output dataset contains exactly $N=437$ physical project records with 16 columns:

| Column Name | Data Type | Nullable | Description |
|---|---|:---:|---|
| `canonical_project_key` | String (UUID) | No | Unique physical project identifier |
| `cost_risk_probability` | Float64 | No | Model-predicted cost escalation probability $\in [0, 1]$ |
| `schedule_risk_probability` | Float64 | Yes | Model-predicted schedule slippage probability (null for PARTIAL) |
| `attention_score` | Float64 | No | Portfolio upper-envelope attention score $\in [0, 1]$ |
| `risk_coverage` | String | No | Coverage scope (`FULL` or `PARTIAL`) |
| `portfolio_rank` | Integer | No | Model-derived portfolio priority rank ($1 \dots 395$) |
| `intervention_priority` | String | No | Operational urgency tier (`PRIORITY_1` to `PRIORITY_4`) |
| `primary_action` | String | No | Recommended primary monitoring review action |
| `secondary_action` | String | No | Recommended secondary verification action |
| `risk_focus` | String | No | Core risk dimension requiring attention |
| `priority_reason` | String | No | Evidence-grounded non-causal explanation of the priority |
| `evidence_feature` | String | No | Observable PIT predictor anchoring the recommendation |
| `evidence_value` | String | No | Observed point-in-time value of the evidence feature |
| `evidence_direction` | String | No | Directional model risk impact (`ELEVATES_RISK`, `ATTENUATES_RISK`, `NEUTRAL`) |
| `data_quality_flag` | String | No | Completeness flag (`COMPLETE_BASELINE_DATA`, `SCHEDULE_OUTCOME_UNOBSERVED`) |
| `governance_note` | String | No | Regulatory disclaimer: Decision support only; not an administrative penalty |

---

## 8. Cryptographic Checksum Manifest

All upstream frozen inputs and generated artifacts were verified:

| File Name | Expected SHA-256 Checksum | Verified Hash | Status |
|---|---|---|:---:|
| `data/interim/pit_features_july2025_to_july2026.csv` | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | PASS |
| `data/processed/table7_june_2025_projects.csv` | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` | PASS |
| `data/processed/table4_july_2025_projects.csv` | `ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3` | `ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3` | PASS |
| `data/processed/table6_july_2026_projects.csv` | `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` | `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` | PASS |
| `data/processed/project_identity_map.csv` | `16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb` | `16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb` | PASS |
| `data/processed/project_snapshot_panel.csv` | `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47` | `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47` | PASS |
| `data/processed/project_risk_scores.csv` | `6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d` | `6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d` | PASS |
| `data/interim/project_risk_explanations.csv` | `5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2` | `5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2` | PASS |
| `data/processed/project_intervention_priorities.csv` | *(New Output Artifact)* | Computed & Verified | PASS |
| `reports/module4_intervention_prioritisation.md` | *(New Specification Report)* | Computed & Verified | PASS |

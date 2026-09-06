# Module 4 — Phase 6: Explainable Risk Drivers Validation Report

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 4 — Risk Scoring & Decision Intelligence  
**Phase:** 6 — Explainable Risk Drivers (Explanation & Feature Attribution)  
**Document:** `reports/module4_explainability_validation.md`  
**Artifact Reference:** `data/interim/project_risk_explanations.csv`  
**Evaluation Date:** September 5, 2026  
**Status:** **VALIDATION COMPLETE — EXPLAINABILITY ENGINE FROZEN**  

---

## 1. Executive Summary & Core Architectural Distinctions

Module 4 Phase 6 establishes the prototype explanation layer of the PAIMANA platform. Its purpose is to explain **WHY** specific infrastructure projects receive elevated or attenuated risk scores without resorting to black-box assertions or ungrounded causal claims.

To ensure rigorous scientific integrity, this implementation enforces three strict ontological boundaries:

1. **Model Prediction vs. Physical Reality:** The model output ($P_c$ or $P_s$) is a statistical score derived from historical data correlations; it is NOT a physical guarantee of project failure.
2. **Feature Association vs. Causal Attribution:** Feature importance and local impacts measure statistical associations in historical data. They do **NOT** imply that a feature (e.g., executing agency or state) caused the project delay or cost escalation.
3. **Source-Observed Facts vs. Model Inferences:** Observed values from the point-in-time snapshot (e.g., ₹250 Cr expenditure, 15 months elapsed) are factual administrative records. The model's risk weighting of those values is an algorithmic inference.

---

## 2. Evaluation of Explainability Methodologies

Prior to implementation, candidate explanation methodologies were evaluated against project constraints:

| Methodology | Pros | Cons / Pipeline Incompatibilities | Recommendation |
|---|---|---|:---:|
| **TreeSHAP (`shap.TreeExplainer`)** | Strong theoretical properties (Shapley efficiency, local additivity) | External dependency not present in execution environment; high computational overhead across complex pipelines; frequent user misinterpretation of Shapley values as causal impacts | **REJECTED** |
| **TreeInterpreter (Saabas path decomposition)** | Direct tree path decomposition | External library not installed; does not naturally integrate with pre-tree `ColumnTransformer` (OHE dummy scattering) | **REJECTED** |
| **Global Mean Decrease in Impurity (MDI / Gini)** | Fast, native to Random Forest, directly accessible via `clf.feature_importances_`, deterministic | Measures global split importance only; tends to favor high-cardinality features; non-directional | **ADOPTED for Global Analysis** (with parent feature aggregation) |
| **Local Marginal Reference Perturbation (Baseline Attribution)** | **100% dependency-free**; operates directly on the end-to-end scikit-learn `Pipeline`; preserves OHE preprocessing; **directional** (signed impact relative to neutral portfolio baseline); **zero target leakage**; exact and deterministic | Captures marginal 1D feature impact without full multi-way interaction decomposition | **ADOPTED for Local Explanations** |

### Selected Methodological Combination:
1. **Global Model Drivers:** Aggregated native Random Forest MDI importance, grouping one-hot encoded categories back to their governing parent features (`feat_state` and `feat_agency`).
2. **Local Project Explanations:** Local Marginal Reference Perturbation, evaluating the directional risk shift $\Delta_{i,j} = \hat{P}(x_i) - \hat{P}(x_{i, j \leftarrow \text{ref}_j})$ relative to the portfolio reference baseline (median for numeric features, mode for categorical features).

---

## 3. Global Model-Driver Analysis

The table below presents global feature importance across the 12 authorized predictors, with one-hot encoded indicators aggregated back to their parent features:

| Rank | Cost Overrun Feature ($Y = \text{cost\_overrun\_5pct\_2026}$) | MDI Share | Schedule Slippage Feature ($Y = \text{time\_overrun\_3m\_2026}$) | MDI Share |
|:---:|---|:---:|---|:---:|
| 1 | `feat_agency` | **15.64%** | `feat_agency` | **19.03%** |
| 2 | `feat_expenditure_to_original_cost_ratio` | **15.28%** | `feat_remaining_original_duration_months` | **16.76%** |
| 3 | `feat_cumulative_expenditure_crore` | **11.26%** | `feat_state` | **11.54%** |
| 4 | `feat_physical_vs_financial_divergence` | **11.15%** | `feat_project_age_months` | **8.00%** |
| 5 | `feat_project_age_months` | **9.75%** | `feat_is_past_original_completion` | **7.12%** |
| 6 | `feat_physical_progress_pct` | **9.70%** | `feat_original_cost_crore` | **6.73%** |
| 7 | `feat_state` | **9.33%** | `feat_cumulative_expenditure_crore` | **6.42%** |
| 8 | `feat_remaining_original_duration_months` | **6.36%** | `feat_log_original_cost` | **6.25%** |
| 9 | `feat_log_original_cost` | **4.82%** | `feat_expenditure_to_original_cost_ratio` | **6.05%** |
| 10 | `feat_original_cost_crore` | **4.74%** | `feat_physical_progress_pct` | **5.97%** |
| 11 | `feat_is_past_original_completion` | **1.98%** | `feat_physical_vs_financial_divergence` | **5.56%** |
| 12 | `feat_is_missing_approval_date` | **0.00%** | `feat_is_missing_approval_date` | **0.56%** |
| **Total** | **All 12 Authorized Predictors** | **100.00%** | **All 12 Authorized Predictors** | **100.00%** |

### Critical Global Invariants:
- **Zero Unauthorized Features:** Sector features (`sector`, `feat_sector`, `cat_sector`) are strictly absent (0.00% importance).
- **Dominant Cost Drivers:** Budget utilization (`feat_expenditure_to_original_cost_ratio`, 15.3%), absolute expenditure volume (11.3%), and physical vs. financial divergence (11.2%) dominate prospective cost escalation.
- **Dominant Schedule Drivers:** Remaining timeline buffer (`feat_remaining_original_duration_months`, 16.8%) and executing agency portfolio patterns (19.0%) dominate schedule slippage risk.

---

## 4. Local Project-Level Explanation Methodology

### Mathematical Formulation
For a project $i$ with feature vector $x_i$:
1. The model predicts raw risk probability $\hat{P}(x_i)$.
2. For each authorized feature $j \in \{1, \dots, 12\}$, a perturbed feature vector $x_{i, j \leftarrow \text{ref}_j}$ is created where feature $j$ is substituted by the reference portfolio baseline $\text{ref}_j$:
   * **Numeric Features:** Portfolio median $\text{ref}_j = \text{Median}(X_j)$.
   * **Categorical Features:** Portfolio modal category $\text{ref}_j = \text{Mode}(X_j)$.
3. The marginal attribution is:
   $$\Delta_{i,j} = \hat{P}(x_i) - \hat{P}(x_{i, j \leftarrow \text{ref}_j})$$
4. **Directionality Interpretation:**
   * $\Delta_{i,j} > +0.0001$: **`ELEVATES_RISK`** — Project's observed value pushes predicted risk higher than reference baseline.
   * $\Delta_{i,j} < -0.0001$: **`ATTENUATES_RISK`** — Project's observed value pulls predicted risk lower than reference baseline.
   * $|\Delta_{i,j}| \le 0.0001$: **`NEUTRAL`** — Project's value matches baseline impact.
5. The top 3 features by absolute impact $|\Delta_{i,j}|$ are identified and mapped to verified source facts.

---

## 5. Audit of Local Explanations (Deterministic Sample)

### 5.1 High-Priority Projects (Tier 1 Sample from Top 20)

#### Case 1: `PROJ-PAIMANA-0400119` (MoSPI ID: `400119`)
* **Project Name:** Life Extension of 48 well platforms...
* **State / Agency:** Offshore | Oil and Natural Gas Corporation Limited [ONGC]
* **Risk Scores:** Cost Prob: `0.8033`, Schedule Prob: `1.0000`, Attention Score: `1.0000` (Tier 1, Rank 1)
* **Cost Risk Drivers:**
  1. `feat_agency` ($\Delta = +0.2233$, `ELEVATES_RISK`): Executing agency is ONGC.
  2. `feat_expenditure_to_original_cost_ratio` ($\Delta = +0.1800$, `ELEVATES_RISK`): Cumulative expenditure reached 102.4% of original sanctioned budget.
  3. `feat_physical_progress_pct` ($\Delta = -0.1133$, `ATTENUATES_RISK`): Reported physical progress reached 98.0%, which moderates cost risk slightly relative to lower-progress projects.
* **Schedule Risk Drivers:**
  1. `feat_remaining_original_duration_months` ($\Delta = +0.1867$, `ELEVATES_RISK`): Remaining original duration was -12 months (past due) as of July 2025.
  2. `feat_is_past_original_completion` ($\Delta = +0.1200$, `ELEVATES_RISK`): Project had passed its original completion date as of July 2025 cutoff.
  3. `feat_agency` ($\Delta = +0.0867$, `ELEVATES_RISK`): Model associates this agency category with higher schedule slippage risk within evaluated data.

#### Case 2: `PROJ-PAIMANA-0705366` (MoSPI ID: `705366`)
* **Project Name:** Hajipur-Sagauli New line
* **State / Agency:** Bihar | East Central Railway [ECR] - I
* **Risk Scores:** Cost Prob: `0.9900`, Schedule Prob: `1.0000`, Attention Score: `1.0000` (Tier 1, Rank 1)
* **Cost Risk Drivers:**
  1. `feat_project_age_months` ($\Delta = +0.2933$, `ELEVATES_RISK`): Project age was 260 months (over 21 years) since approval.
  2. `feat_expenditure_to_original_cost_ratio` ($\Delta = +0.2467$, `ELEVATES_RISK`): Cumulative expenditure reached 380.5% of original cost.
  3. `feat_physical_vs_financial_divergence` ($\Delta = +0.1933$, `ELEVATES_RISK`): Financial expenditure ratio exceeds physical progress by +335.5% points.
* **Schedule Risk Drivers:**
  1. `feat_is_past_original_completion` ($\Delta = +0.2100$, `ELEVATES_RISK`): Original completion date had passed as of July 2025 cutoff.
  2. `feat_remaining_original_duration_months` ($\Delta = +0.1767$, `ELEVATES_RISK`): Remaining original duration was -188 months.
  3. `feat_agency` ($\Delta = +0.0933$, `ELEVATES_RISK`): Historical delay association with rail infrastructure enterprises in evaluated data.

---

### 5.2 Representative Lower-Risk Projects (Tier 2, 3, and 4)

#### Case 3: `PROJ-PAIMANA-0617269` (MoSPI ID: `617269`) — Tier 1 Schedule / Tier 4 Cost
* **State / Agency:** Uttar Pradesh | Power Grid Corporation of India Limited [POWERGRID]
* **Cost Prob:** `0.0000` | **Schedule Prob:** `1.0000` | **Attention Score:** `1.0000` (Tier 1)
* **Cost Attenuation Drivers:**
  1. `feat_expenditure_to_original_cost_ratio` ($\Delta = -0.1033$, `ATTENUATES_RISK`): Budget expenditure is 0.0% of original cost.
  2. `feat_agency` ($\Delta = -0.0967$, `ATTENUATES_RISK`): POWERGRID transmission projects exhibit historically minimal cost overrun within evaluated data.
* **Schedule Risk Drivers:**
  1. `feat_remaining_original_duration_months` ($\Delta = +0.2400$, `ELEVATES_RISK`): Remaining duration is under 2 months with low physical completion.

#### Case 4: `PROJ-PAIMANA-0701140` (MoSPI ID: `701140`) — Tier 4 Baseline Risk
* **State / Agency:** Gujarat | Western Railway [WR]
* **Cost Prob:** `0.0033` | **Schedule Prob:** `N/A (PARTIAL)` | **Attention Score:** `0.0033` (Tier 4, Rank 391)
* **Cost Attenuation Drivers:**
  1. `feat_expenditure_to_original_cost_ratio` ($\Delta = -0.1000$, `ATTENUATES_RISK`): Expenditure ratio is 0.01% (early stage).
  2. `feat_project_age_months` ($\Delta = -0.0867$, `ATTENUATES_RISK`): Project age is only 3 months since sanction.
  3. `feat_physical_vs_financial_divergence` ($\Delta = -0.0500$, `ATTENUATES_RISK`): Physical and financial progress are in near-perfect initial alignment.

---

## 6. Categorical Variable Handling Standards

To prevent ungrounded stereotyping or causal overclaiming regarding executing agencies and states:
1. **Mandatory Disclaimer Phrasing:** Explanations never state *"Agency X causes project failure"* or *"State Y is inefficient"*.
2. **Standardized Regulatory Phrasing:**
   * *"The model associates this agency category with higher predicted risk within the evaluated data."*
   * *"The model associates this state category with lower historical cost overrun in the reference dataset."*
3. **MDI Aggregation Invariant:** One-hot encoded agency indicators (e.g. `cat__feat_agency_AAI`, `cat__feat_agency_ONGC`) are reported as sub-components under the unified parent feature `feat_agency`.

---

## 7. Explanation Dataset Schema (`data/interim/project_risk_explanations.csv`)

The generated artifact contains exactly **874 rows** ($437 \text{ projects} \times 2 \text{ tasks}$), uniquely keyed by `(canonical_project_key, task)`:

| Column Name | Data Type | Nullable | Description |
|---|---|:---:|---|
| `canonical_project_key` | String (UUID) | No | Unique physical project identifier |
| `source_project_id` | String | No | MoSPI / OCMS project identifier |
| `project_name` | String | No | Official infrastructure project name |
| `state` | String | No | Primary executing state / UT |
| `agency` | String | No | Executing agency / enterprise |
| `task` | String | No | Target task (`cost_overrun` or `schedule_slippage`) |
| `is_eligible_task_target` | Integer (0/1) | No | Eligibility flag (1 = eligible, 0 = censored) |
| `predicted_risk_probability` | Float64 | Yes | Model-estimated risk probability (null if ineligible) |
| `attention_score` | Float64 | No | Portfolio upper-envelope attention score |
| `attention_tier` | String | No | Attention tier (`Tier 1` to `Tier 4`) |
| `portfolio_rank` | Integer | No | Portfolio monitoring priority rank |
| `risk_coverage` | String | No | Surveillance scope (`FULL` or `PARTIAL`) |
| `top_1_feature` | String | Yes | Name of #1 most impactful feature |
| `top_1_feature_value` | String | Yes | Observed feature value in PIT data |
| `top_1_impact` | Float64 | Yes | Signed marginal risk shift ($\Delta$) |
| `top_1_direction` | String | Yes | Direction (`ELEVATES_RISK`, `ATTENUATES_RISK`, `NEUTRAL`) |
| `top_1_source_fact` | String | No | Verified factual statement grounded in PIT data |
| `top_2_feature` | String | Yes | Name of #2 most impactful feature |
| `top_2_feature_value` | String | Yes | Observed feature value in PIT data |
| `top_2_impact` | Float64 | Yes | Signed marginal risk shift ($\Delta$) |
| `top_2_direction` | String | Yes | Direction |
| `top_2_source_fact` | String | Yes | Verified factual statement |
| `top_3_feature` | String | Yes | Name of #3 most impactful feature |
| `top_3_feature_value` | String | Yes | Observed feature value in PIT data |
| `top_3_impact` | Float64 | Yes | Signed marginal risk shift ($\Delta$) |
| `top_3_direction` | String | Yes | Direction |
| `top_3_source_fact` | String | Yes | Verified factual statement |
| `explanation_method` | String | No | Methodology: `Local Marginal Reference Perturbation` |
| `explanation_disclaimer` | String | No | Governance disclaimer: Statistical association; not causal |

---

## 8. Limitations & Non-Causality Governance

1. **Non-Causal Interpretation:** Explanations reflect statistical correlations present in the historical MoSPI transition (July 2025 $\rightarrow$ July 2026). A positive impact $\Delta > 0$ means the model predicts higher risk for projects with that feature value; it does NOT prove that modifying that feature will avert delay or cost escalation.
2. **Marginal 1D Assumption:** Local marginal reference perturbation evaluates one feature shift at a time holding all other covariates constant. It does not measure high-order multi-way non-linear feature interactions.
3. **Censored Schedule Explanations:** For the 132 projects lacking reported revised completion dates, schedule explanations are explicitly omitted. Their records document unobserved schedule status rather than fabricating neutral predictions.
4. **Prototype Status:** This explainability engine is designed for diagnostic decision-support, model interpretability audit, and transparency inspection. It is **NOT** approved for punitive administrative actions, contractor liability claims, or autonomous budget cuts.

---

## 9. Cryptographic Verification & Invariants

All upstream datasets and previously frozen artifacts were verified:

| File / Artifact | Expected SHA-256 Checksum | Verified Hash | Status |
|---|---|---|:---:|
| `data/interim/pit_features_july2025_to_july2026.csv` | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | Identical | PASS |
| `data/processed/table7_june_2025_projects.csv` | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` | Identical | PASS |
| `data/processed/table4_july_2025_projects.csv` | `ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3` | Identical | PASS |
| `data/processed/table6_july_2026_projects.csv` | `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` | Identical | PASS |
| `data/processed/project_identity_map.csv` | `16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb` | Identical | PASS |
| `data/processed/project_snapshot_panel.csv` | `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47` | Identical | PASS |
| `data/processed/project_risk_scores.csv` | `6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d` | Identical | PASS |

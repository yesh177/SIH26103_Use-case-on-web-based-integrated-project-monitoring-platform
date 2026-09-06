# Module 4 — Project Risk Scoring Schema & Attention Priority Architecture

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 4 — Risk Scoring & Decision Intelligence  
**Document:** `reports/module4_risk_scoring_schema.md`  
**Dataset Reference:** `data/processed/project_risk_scores.csv`  
**Governing Inputs:**
* `data/interim/pit_features_july2025_to_july2026.csv` (SHA-256: `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329`)
* `reports/module3_probability_calibration_validation.md` (SHA-256: `2438b0c8ac801d47bc2ae7fd7b678bf83d62585d878ff533e45496ded10650c1`)  
**Status:** **FROZEN PROTOTYPE SCORING SPECIFICATION**  
**Execution Date:** September 5, 2026  

---

## 1. Executive Overview

Module 4 implements the operational scoring layer of the PAIMANA Predictive Risk Intelligence platform. It operationalizes the candidate models approved at the conclusion of Module 3 Phase 7 into unified, interpretable project-level risk metrics.

The scoring architecture computes:
1. **Cost Risk Probability ($P_c$):** Probability of prospective $>5\%$ cost escalation over 12 months.
2. **Schedule Risk Probability ($P_s$):** Probability of prospective $\ge 3$ months completion slippage over 12 months (evaluated exclusively for schedule-eligible projects).
3. **Attention Score ($A$):** Upper-envelope priority metric integrating available risk dimensions.
4. **Risk Coverage Flag:** Categorization of projects as `FULL` (dual-dimension monitoring) or `PARTIAL` (cost-only monitoring).
5. **Compound Exposure Indicator ($C$):** Descriptive co-elevation index for projects with complete multi-risk coverage.
6. **Portfolio Attention Tiers (Tiers 1–4):** Deterministic priority classifications based on empirical portfolio quantile thresholds.
7. **Portfolio Priority Rank:** Descending ordinal ranking across the entire reference portfolio.

---

## 2. Selected Baseline Models & Upstream Provenance

In accordance with the frozen Module 3 Phase 7 validation protocol:

| Dimension | Selected Candidate Model | Probability Variant | Source Data | Target Population | Evaluated Holdout Metrics |
|---|---|---|---|:---:|---|
| **Cost Overrun (>5%)** | Random Forest (`n_estimators=300`, `random_state=42`, `n_jobs=1`) | Raw / Uncalibrated | `pit_features_july2025_to_july2026.csv` | $N=437$ (100% eligible) | Brier: 0.1330, Log Loss: 0.4102, ROC-AUC: 0.8552, PR-AUC: 0.8038 |
| **Schedule Slippage ($\ge$3M)** | Random Forest (`n_estimators=300`, `random_state=42`, `n_jobs=1`) | Raw / Uncalibrated | `pit_features_july2025_to_july2026.csv` | $N=305$ (69.8% eligible) | Brier: 0.1050, Log Loss: 0.3118, ROC-AUC: 0.8961, PR-AUC: 0.9806 |

*(Note: Evaluated holdout metrics were measured on the 20% test holdout partition ($N=88$ cost, $N=61$ schedule) during Module 3 validation, rather than on the full scoring population. The exact per-project partition classification is tracked in `data/processed/project_risk_score_partitions.csv`).*

---

## 3. Exact Mathematical Scoring Formulas

### 3.1 Attention Score ($A$)
The Attention Score represents the primary operational index determining administrative monitoring priority. It operates as a conservative upper-envelope across monitored risk dimensions:

$$A_i = \begin{cases} \max(P_{c,i}, \, P_{s,i}) & \text{if } \text{Coverage}_i = \text{FULL} \\[6pt] P_{c,i} & \text{if } \text{Coverage}_i = \text{PARTIAL} \end{cases}$$

Where:
* $P_{c,i} \in [0, 1]$ is the cost overrun risk probability for project $i$.
* $P_{s,i} \in [0, 1]$ is the schedule slippage risk probability for project $i$.

> [!NOTE]
> **Operational Interpretation**: $\text{attention\_score} = \max(P_c, P_s)$ is a comparative portfolio prioritization index, not a calibrated probability of joint failure. High values reflect the upper envelope of distress across tracked dimensions, where schedule probabilities reflect an empirical 84.3% historical baseline delay rate in central projects.

### 3.2 Missing Schedule Prediction & Risk Coverage Handling
* Exactly 132 projects in the reference cohort lack reported revised commissioning dates in official MoSPI reports (`is_eligible_schedule_target == 0`).
* **Zero-Imputation Prohibition:** A missing schedule probability is **NEVER** treated as zero ($P_s \neq 0$). Setting $P_s = 0$ would falsely depress the attention score and introduce severe negative bias.
* **Missing Value Representation:** For these 132 projects, `schedule_risk_probability` is explicitly represented as `NaN` (null).
* **Coverage Categorization:**
  $$\text{Coverage}_i = \begin{cases} \text{FULL} & \text{if } P_{s,i} \text{ is present} \\[4pt] \text{PARTIAL} & \text{if } P_{s,i} \text{ is missing / unobserved} \end{cases}$$
* When coverage is `PARTIAL`, the Attention Score defaults strictly to the available cost risk probability ($A_i = P_{c,i}$).

### 3.3 Compound Exposure Indicator ($C$)
The Compound Exposure Indicator measures the degree of simultaneous risk elevation across both cost and schedule dimensions:

$$C_i = \begin{cases} \min(P_{c,i}, \, P_{s,i}) & \text{if } \text{Coverage}_i = \text{FULL} \\[6pt] \text{NaN (null)} & \text{if } \text{Coverage}_i = \text{PARTIAL} \end{cases}$$

#### Critical Interpretative Safeguards:
* **NOT a Joint Probability:** $C_i$ is **NOT** a joint probability of simultaneous occurrence ($P(\text{Cost} \cap \text{Schedule})$). It assumes neither conditional independence nor any specific joint copula structure.
* **Descriptive Floor Metric:** $C_i$ serves purely as a descriptive indicator of the lower bound of risk elevation across both tracked axes. A high $C_i$ signifies that a project is substantially exposed on *both* fronts simultaneously.
* **Null Invariance:** $C_i$ is undefined and set to `NaN` for any project lacking dual-dimension coverage.

---

## 4. Portfolio Attention Tier Methodology

To avoid arbitrary risk cutoffs (such as arbitrary 0.33 / 0.66 rules), portfolio attention tiers are established empirically using the sample quantile distribution of the reference scoring portfolio ($N=437$).

### 4.1 Empirical Quantile Thresholds (Portfolio Reference N=437)
The empirical quantiles of $A$ across the complete reference portfolio are:
* **$Q_{50}$ (Median):** `0.906667`
* **$Q_{75}$ (75th Percentile):** `0.983333`
* **$Q_{90}$ (90th Percentile):** `0.994667`

### 4.2 Tier Definitions & Partition Rules

| Attention Tier | Mathematical Boundary | Portfolio Meaning | Empirical Cohort Count | Percentage of Portfolio |
|:---:|---|---|:---:|:---:|
| **Tier 1** | $A_i \ge Q_{90}$ ($A_i \ge 0.994667$) | Highest Portfolio Monitoring Priority (Top 10%) | 44 | 10.07% |
| **Tier 2** | $Q_{75} \le A_i < Q_{90}$ ($0.983333 \le A_i < 0.994667$) | Elevated Portfolio Monitoring Priority (Next 15%) | 73 | 16.70% |
| **Tier 3** | $Q_{50} \le A_i < Q_{75}$ ($0.906667 \le A_i < 0.983333$) | Moderate Portfolio Monitoring Priority (Next 25%) | 102 | 23.34% |
| **Tier 4** | $A_i < Q_{50}$ ($A_i < 0.906667$) | Standard Baseline Monitoring Priority (Bottom 50%) | 218 | 49.89% |

### 4.3 Semantic & Categorical Rules
1. **Portfolio Attention Priority vs. Absolute Severity:** Tier labels denote relative portfolio supervisory priority within the monitored cohort, NOT certified physical or financial hazard levels.
2. **Prohibited Terminology:** Tiers must **NEVER** be labeled "Low / Medium / High / Critical Risk". Such labels encourage unjustified causal confidence and imply absolute operational guarantees that retrospective prototypes cannot support.
3. **Strict Tie Handling:** The tier assignment function strictly uses $\ge$ and $<$ boundaries. Projects with identical attention scores are guaranteed to receive identical attention tiers.

---

## 5. Portfolio Priority Ranking Methodology

* **Ordering:** Projects are ranked in descending order of Attention Score ($A$).
* **Tie Handling:** Ties in attention score receive identical ranks using standard minimum competition ranking (`method="min"` in pandas/scikit-learn).
  * Example: If two projects tie for the highest score, both receive `portfolio_rank = 1`, and the project with the next highest score receives `portfolio_rank = 3`.
* **Secondary Sort Key:** For file determinism, ties are sub-sorted by `canonical_project_key` in ascending order without altering the assigned numerical `portfolio_rank`.

---

## 6. Output Dataset Schema (`data/processed/project_risk_scores.csv`)

The output dataset contains exactly $N=437$ records with 20 columns:

| Column Name | Data Type | Nullable | Description |
|---|---|:---:|---|
| `canonical_project_key` | String (UUID) | No | Unique persistent project key across snapshots |
| `source_project_id` | String | No | MoSPI / OCMS project identifier |
| `project_name` | String | No | Official infrastructure project name |
| `state` | String | No | Primary executing state / UT |
| `agency` | String | No | Executing agency / enterprise |
| `snapshot_date` | String (YYYY-MM-DD) | No | Feature snapshot date (`2025-07-31`) |
| `prediction_cutoff_date` | String (YYYY-MM-DD) | No | Retrospective forecast cutoff date (`2025-07-31`) |
| `is_eligible_cost_target` | Integer (0/1) | No | Cost target eligibility flag (100% = 1) |
| `is_eligible_schedule_target` | Integer (0/1) | No | Schedule target eligibility flag (1 = eligible, 0 = censored) |
| `cost_risk_probability` | Float64 | No | Model-estimated probability of >5% cost escalation |
| `schedule_risk_probability` | Float64 | Yes | Model-estimated probability of $\ge 3$M delay (null if ineligible) |
| `risk_coverage` | String | No | Scope of risk coverage (`FULL` or `PARTIAL`) |
| `attention_score` | Float64 | No | Integrated upper-envelope attention metric |
| `compound_exposure` | Float64 | Yes | Multi-risk co-elevation index (null if PARTIAL coverage) |
| `attention_tier` | String | No | Priority classification (`Tier 1`, `Tier 2`, `Tier 3`, `Tier 4`) |
| `portfolio_rank` | Integer | No | Portfolio monitoring priority rank (1 = highest priority) |
| `cost_model_name` | String | No | Model descriptor (`RandomForestClassifier(n_estimators=300, random_state=42)`) |
| `schedule_model_name` | String | No | Model descriptor (`RandomForestClassifier(n_estimators=300, random_state=42)`) |
| `cost_probability_variant` | String | No | Calibration status (`Raw / Uncalibrated`) |
| `schedule_probability_variant` | String | No | Calibration status (`Raw / Uncalibrated`) |
| `scoring_method_version` | String | No | Version of scoring methodology (`1.0.0`) |

---

## 7. Portfolio Distribution Diagnostics

* **Total Portfolio Size:** $N = 437$
* **Risk Coverage Distribution:**
  * `FULL` (Dual Cost + Schedule Monitoring): **305 projects (69.8%)**
  * `PARTIAL` (Cost-Only Monitoring): **132 projects (30.2%)**
* **Cost Risk Probability Summary:**
  * Minimum: `0.0000`
  * Median: `0.2033`
  * Mean: `0.2935`
  * Maximum: `0.9967`
* **Schedule Risk Probability Summary (N=305 Eligible):**
  * Minimum: `0.1100`
  * Median: `0.9400`
  * Mean: `0.8485`
  * Maximum: `1.0000`
* **Attention Score Summary:**
  * Minimum: `0.0000`
  * 25th Percentile ($Q_{25}$): `0.4033`
  * 50th Percentile ($Q_{50}$): `0.9067`
  * 75th Percentile ($Q_{75}$): `0.9833`
  * 90th Percentile ($Q_{90}$): `0.9947`
  * Maximum: `1.0000`
* **Compound Exposure Summary (N=305 Full Coverage):**
  * Minimum: `0.0000`
  * Median: `0.2100`
  * Mean: `0.2917`
  * Maximum: `0.9867`

---

## 8. Limitations & Prototype Status

1. **Retrospective Evaluation Anchor:** Scores are generated using models validated on a single retrospective 12-month window (July 2025 $\rightarrow$ July 2026). They do not reflect multi-year longitudinal drift.
2. **Missing Schedule Censoring:** The 132 projects with `PARTIAL` coverage are not monitored for schedule slippage due to unobserved revised completion dates in MoSPI records. Their attention scores reflect cost escalation risks only.
3. **No Causal Interpretation:** High attention scores and compound exposure values represent empirical statistical associations, not physical causes or contractor culpability.
4. **Prototype Status:** These risk scores are produced for decision-support prototypes and audit inspection. They are **NOT** authorized for autonomous operational intervention, budget allocation penalties, or legal determinations.
5. **In-Sample Catalog Composition:** The scoring models are fitted on ~60% of the reference cohort (modelfit partition: 261 cost, 183 schedule); predictions for this subset are in-sample and serve prototype catalog demonstration. Genuinely out-of-sample holdout predictions comprise 20% of the cohort ($N=88$ cost, $N=61$ schedule), with the remaining 20% comprising calibration holdouts. The exact status of each project is detailed in `data/processed/project_risk_score_partitions.csv`.

# Module 3 — Baseline Modeling Readiness Report (Phase 1)

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 3 — Baseline Predictive Modeling (Phase 1: Evaluation Protocol & Baseline Readiness)  
**Report File:** `reports/module3_baseline_readiness.md`  
**Governing Document:** `docs/module3_evaluation_protocol.md`  
**Audit Date:** September 5, 2026  
**Status:** **PASSED — READY FOR BASELINE EXPERIMENTATION (DOCUMENTATION & TESTING COMPLETE)**  

---

## 1. Executive Summary & Verification Scope

This audit formally certifies that the Point-in-Time (PIT) dataset (`data/interim/pit_features_july2025_to_july2026.csv`) and its governing evaluation protocol satisfy all scientific, methodological, and leak-free prerequisites for prospective baseline modeling.

### Critical Status Constraints
* **DOCUMENTATION + TESTING ONLY:** No machine learning models have been trained.
* **NO PREDICTIONS GENERATED:** No fitted parameters or probability outputs exist.
* **NO TRAIN/TEST SPLITS COMMITTED:** No physical train/test partitions have been written to disk.
* **DATASET IMMUTABILITY PRESERVED:** The interim PIT feature dataset remains byte-for-byte unchanged with SHA-256 hash `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329`.

---

## 2. Core Architectural Distinctions

To ensure clarity and avoid overclaiming, the evaluation protocol establishes clean boundaries:

| Dimension | Architectural Boundary | Operational Definition |
|---|---|---|
| **DATASET** | `data/interim/pit_features_july2025_to_july2026.csv` | Frozen PIT features observable at July 31, 2025, paired with reported July 2026 outcomes ($N=437$). |
| **BASELINE** | Naive Majority-Class Benchmark | Empirical baseline hurdle (predict 0 for cost, predict 1 for schedule) defining the minimum performance floor. |
| **ML MODEL** | Regularized Logistic Regression | Interpretable linear benchmark with odds-ratio driver analysis, to be trained in subsequent phases. |
| **EVALUATION** | Retrospective 12-Month Horizon Evaluation | Preserves prospective temporal direction (July 2025 features $\rightarrow$ July 2026 outcome) with strictly isolated cross-validation. |
| **INTERPRETATION** | Posterior Risk Probabilities | Formally calibrated probabilities supporting Low / Medium / High risk ranking and intervention prioritisation. |
| **LIMITATIONS** | Single 12-Month Transition Window | Exactly one primary transition currently available; multi-period temporal generalization is explicitly not claimed. |

---

## 3. Two Modeling Tasks: Formal Audit & Base Rates

### 3.1 Task A — Cost Overrun Classification

* **Target Name:** `cost_overrun_5pct_2026`
* **Definition:** 1 if `future_total_cost_escalation_2026 > 0.05` else 0
* **Formula:**
  $$\text{future\_total\_cost\_escalation\_2026} = \frac{\text{revised\_cost\_2026} - \text{original\_cost}}{\text{original\_cost}}$$
* **Audit Accounting:**
  * **Total Longitudinal Projects ($N$):** 437
  * **Eligible Cohort (`is_eligible_cost_target == 1`):** 437 (100.0%)
  * **Missing Count:** 0 (0.0%)
  * **Positive Cases ($Y=1$, Escalation $> 5\%$):** 132 (30.21%)
  * **Negative Cases ($Y=0$, Escalation $\le 5\%$):** 305 (69.79%)
  * **Positive Prevalence:** **30.21%**

### 3.2 Task B — Schedule Slippage Classification

* **Target Name:** `time_overrun_3m_2026`
* **Definition:** 1 if `future_schedule_slippage_months_2026 >= 3.0` else 0 (if $< 3.0$)
* **Formula:**
  $$\text{future\_schedule\_slippage\_months\_2026} = \text{DateDiffMonths}(\text{revised\_doc\_2026}, \; \text{original\_doc})$$
* **Audit Accounting:**
  * **Total Longitudinal Projects ($N$):** 437
  * **Eligible Cohort (`is_eligible_schedule_target == 1`):** 305 (69.79%)
  * **Missing / Censored Count (`is_eligible_schedule_target == 0`):** 132 (30.21%)
  * **Positive Cases ($Y=1$, Slippage $\ge 3$ months):** 257 (84.26% of eligible)
  * **Negative Cases ($Y=0$, Slippage $< 3$ months):** 48 (15.74% of eligible)
  * **Positive Prevalence (Eligible Cohort):** **84.26%**
* **Mandatory Censoring Rule:**
  > [!IMPORTANT]
  > The 132 missing schedule outcomes correspond to projects with unrevised completion dates (`-`) in July 2026.  
  > **These 132 projects MUST remain strictly excluded from supervised schedule modeling and evaluation.**  
  > They must **never** be imputed as zeros or negative labels.

---

## 4. Retrospective Evaluation Design & Documented Limitations

The evaluation design is formally specified as a:
**"Retrospective 12-month horizon evaluation."**

### Explicit Research Protocol Constraints:
1. **The current dataset contains one primary 12-month forecast transition:**  
   July 2025 cutoff $\rightarrow$ July 2026 observed outcome.
2. **DO NOT claim multi-period temporal cross-validation.** Multi-period temporal rolling windows are impossible with a single transition pair.
3. **DO NOT claim broad temporal generalisation.** Findings pertain to the 2025–2026 infrastructure portfolio monitoring cycle.
4. **DO NOT randomly mix future observations into the training data.**
5. **Preserve temporal forecasting direction:**
   * **FEATURES:** Information available at or before **July 31, 2025**.
   * **OUTCOME:** Reported **July 2026** result.

---

## 5. Initial Baseline Strategy: Majority-Class Benchmark

A naive majority-class benchmark establishes the empirical performance floor. Any viable ML model must beat these benchmarks.

### 5.1 Naive Benchmark Performance Table

| Metric | Task A: Cost Overrun (Predict All 0) | Task B: Schedule Slippage (Predict All 1) | Baseline Role / Note |
|---|:---:|:---:|---|
| **Accuracy** | **69.79%** | **84.26%** | High baseline accuracy is trivial; **not a headline metric**. |
| **Balanced Accuracy** | **50.00%** | **50.00%** | Pure chance balanced trade-off. |
| **Precision (Positives)** | **0.00%** | **84.26%** | Majority schedule predictor matches positive prevalence. |
| **Recall (Positives)** | **0.00%** | **100.00%** | Detects all schedule delays by predicting everything delayed. |
| **F1-Score (Positives)** | **0.0000** | **0.9146** | Inflated on schedule by majority prevalence without discrimination. |
| **ROC-AUC** | **0.5000** | **0.5000** | Uninformative rank ordering. |
| **PR-AUC (Avg Precision)**| **0.3021** | **0.8426** | Equals the empirical base rate. |
| **Brier Score** | **0.3021** | **0.1574** | Base rate variance. |

### 5.2 Schedule Evaluation Emphasis
For schedule classification, models will **not** be evaluated on accuracy alone. Evaluation will specifically emphasize:
* **PR-AUC**
* **Recall**
* **Precision**
* **F1-Score**
* **Balanced Accuracy**
* **Confusion Matrix**

---

## 6. Logistic Regression Baseline Justification

Logistic Regression is formally designated as the first machine learning baseline for the following scientific reasons:
1. **Interpretability:** Produces transparent, monotonic linear log-odds weights directly inspectable by infrastructure domain experts and auditors.
2. **Strong Conventional Statistical Baseline:** Establishes the standard econometric baseline for binary risk prediction.
3. **Calibrated Posterior Probabilities:** Directly outputs posterior probabilities via the logistic function.
4. **Driver Analysis Support:** Direct odds ratios ($\exp(\beta_j)$) quantify the incremental risk impact of each predictor.
5. **Fulfills Problem Statement Comparison:** Satisfies the SIH problem statement requirement to benchmark advanced techniques against conventional methods.
6. **Execution Status:** **NOT trained in Phase 1.** Model fitting is deferred to subsequent implementation phases.

---

## 7. Feature Policy & Leakage Invariants

### 7.1 Safe Baseline Predictor Catalog (Observed $\le$ July 31, 2025)

| Feature Name | Column Type | Valid ($N$) | Missing ($N$) | Description |
|---|---|:---:|:---:|---|
| `feat_log_original_cost` | Numerical | 437 | 0 | $\ln(1 + \text{original\_cost})$, scale stabilization |
| `feat_expenditure_to_original_cost_ratio` | Numerical | 437 | 0 | Financial burn ratio at cutoff |
| `feat_physical_progress_pct` | Numerical | 437 | 0 | Reported physical completion percentage |
| `feat_physical_vs_financial_divergence` | Numerical | 437 | 0 | Progress % minus expenditure ratio % |
| `feat_project_age_months` | Numerical | 436 | 1 | Months from approval date to July 2025 cutoff |
| `feat_is_missing_approval_date` | Binary | 437 | 0 | Indicator for project missing approval date |
| `feat_remaining_original_duration_months`| Numerical | 437 | 0 | Months from cutoff to original completion date |
| `feat_is_past_original_completion` | Binary | 437 | 0 | 1 if original commissioning date < cutoff date |
| `feat_state` | Categorical | 437 | 0 | Geographical state / jurisdiction |
| `feat_agency` | Categorical | 437 | 0 | Implementing public agency |

**Approved Supporting Numeric Source Variables:**
Where already present in the PIT dataset:
* `feat_original_cost_crore` (Raw sanctioned cost in ₹ Crore)
* `feat_cumulative_expenditure_crore` (Raw cumulative expenditure in ₹ Crore)

### 7.2 Prohibited Features (Strict Leakage Prevention)
* **July 2026 outcome variables:** `future_total_cost_escalation_2026`, `future_schedule_slippage_months_2026`.
* **Target variables:** `cost_overrun_5pct_2026`, `time_overrun_3m_2026`.
* **July 2026 revised status:** Future revised cost, future revised completion date, future expenditure, future physical progress.
* **Pre-cutoff revised metrics:** `revised_cost_cr_2025` and `delay_months_2025` are prohibited from baseline predictors.
* **Sector:** Not included in the first baseline feature contract.
* **State and agency:** Allowed categorical predictors.

---

## 8. Categorical Encoding & Preprocessing Pipeline

### 8.1 Categorical Encoding Protocol
* **Variables:** `feat_state`, `feat_agency`.
* **Preferred Implementation:** **One-Hot Encoding** (`handle_unknown='ignore'`).
* **Isolation Rule:** The encoder **MUST be fitted only on training data**.
* **Prohibition:** Never fit the encoder on the complete dataset before splitting. No target encoding in the first baseline.

### 8.2 Preprocessing Pipeline Steps
1. Separate features ($X$) and targets ($y$).
2. Identify numeric and categorical columns.
3. Impute missing numeric values (`feat_project_age_months`) using the median computed **strictly from training data**.
4. Impute missing categorical values (if any) using training data only.
5. One-hot encode categorical variables using an encoder fitted **strictly on training data**.
6. Transform validation/test data using the fitted training pipeline.

---

## 9. Risk Interpretation & Operational Decision Support

Model probability outputs will eventually represent:
* **Cost Overrun Risk:** $P(\text{cost overrun} > 5\% \mid \text{information available at July 31, 2025})$
* **Schedule Slippage Risk:** $P(\text{schedule slippage} \ge 3\text{ months} \mid \text{information available at July 31, 2025})$

These probabilities will later support **Low / Medium / High** risk tiering and intervention prioritisation.
Final decision thresholds will be decided **after** baseline model calibration and evaluation.

---

## 10. Baseline Readiness Sign-Off

The dataset `data/interim/pit_features_july2025_to_july2026.csv` satisfies all structural, statistical, and methodological requirements.

- [x] Input dataset SHA-256 confirmed (`052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329`).
- [x] Cost target distribution confirmed ($N=437$, 132 positive, 305 negative).
- [x] Schedule target eligibility confirmed ($N=437$, 305 eligible, 132 censored/missing, 257 positive, 48 negative).
- [x] 132 missing schedule outcomes strictly excluded from supervised modeling.
- [x] Safe baseline predictors confirmed (10 core + 2 supporting numeric).
- [x] Prohibited variables (July 2026 outcomes, concurrent revisions, sector) verified excluded.
- [x] Retrospective 12-month horizon evaluation limitations formally documented.
- [x] Majority-class benchmarks and multi-metric criteria formalized.
- [x] Logistic Regression baseline architecture specified (deferred execution).
- [x] Zero machine learning models trained; zero predictions generated; zero splits committed.

**Final Phase 1 Verdict:** **PASSED — READY FOR BASELINE MODELING EXPERIMENTATION**

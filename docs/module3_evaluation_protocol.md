# Module 3 — Baseline Predictive Modeling Evaluation Protocol

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 3 — Baseline Predictive Modeling  
**Document:** `docs/module3_evaluation_protocol.md`  
**Governing Inputs:**
* `data/interim/pit_features_july2025_to_july2026.csv` (SHA-256: `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329`)
* `docs/module2c_pit_feature_specification.md`
* `reports/module2c_pit_dataset_validation.md`  
**Status:** **SPECIFICATION COMPLETE — GOVERNING PROTOCOL FOR BASELINE EXPERIMENTS**  
**Specification Date:** September 5, 2026  

---

## 1. Objective & Core Architectural Distinctions

This protocol establishes the scientific, statistical, and operational guidelines for training, validating, and evaluating prospective machine learning baseline models in **Module 3**.

To ensure scientific rigor and avoid overclaiming, the protocol establishes strict boundaries between distinct architectural layers:

* **DATASET:** Point-in-Time (PIT) feature and target records (`data/interim/pit_features_july2025_to_july2026.csv`), representing features frozen at July 31, 2025 and outcomes observed at July 31, 2026.
* **BASELINE:** A naive, heuristic majority-class benchmark establishing the minimum performance threshold.
* **ML MODEL:** Regularized Logistic Regression as the first statistical/ML baseline.
* **EVALUATION:** A disciplined retrospective 12-month horizon evaluation with leak-free out-of-fold cross-validation.
* **INTERPRETATION:** Calibrated posterior probabilities supporting risk ranking (Low / Medium / High) and feature driver analysis.
* **LIMITATIONS:** Exactly one primary forecast transition is currently available; multi-period temporal generalization is not claimed.

---

## 2. Definition of the Two Modeling Tasks

### 2.1 Task A — Cost Overrun Classification

* **Dataset:** `data/interim/pit_features_july2025_to_july2026.csv`
* **Target Field:** `cost_overrun_5pct_2026`
* **Mathematical Definition:**
  $$Y_{\text{cost}} = \begin{cases} 1 & \text{if } \text{future\_total\_cost\_escalation\_2026} > 0.05 \\ 0 & \text{otherwise} \end{cases}$$
  Where:
  $$\text{future\_total\_cost\_escalation\_2026} = \frac{\text{July 2026 Revised Cost} - \text{Original Cost}}{\text{Original Cost}}$$
* **Cohort Population:**
  * Total longitudinal cohort ($N$): **437**
  * Eligible cohort (`is_eligible_cost_target == 1`): **437 (100.0%)**
  * Missing outcomes: **0 (0.0%)**
  * Positive instances ($Y=1$): **132 (30.21%)**
  * Negative instances ($Y=0$): **305 (69.79%)**
  * Base rate / Prevalence: **30.21%**

### 2.2 Task B — Schedule Slippage Classification

* **Dataset:** `data/interim/pit_features_july2025_to_july2026.csv`
* **Target Field:** `time_overrun_3m_2026`
* **Mathematical Definition:**
  $$Y_{\text{schedule}} = \begin{cases} 1 & \text{if } \text{future\_schedule\_slippage\_months\_2026} \ge 3.0 \\ 0 & \text{if } < 3.0 \end{cases}$$
  Where:
  $$\text{future\_schedule\_slippage\_months\_2026} = \text{DateDiffMonths}(\text{July 2026 Revised DoC}, \; \text{Original DoC})$$
* **Cohort Population & Censoring Rules:**
  * Total longitudinal cohort ($N$): **437**
  * Eligible cohort (`is_eligible_schedule_target == 1`): **305 (69.79%)**
  * Missing / Censored outcomes (`is_eligible_schedule_target == 0`): **132 (30.21%)**
  * Positive instances among eligible ($Y=1$): **257 (84.26%)**
  * Negative instances among eligible ($Y=0$): **48 (15.74%)**
  * Base rate / Prevalence among eligible: **84.26%**
* **Mandatory Censoring Policy:**
  > [!IMPORTANT]
  > In the July 2026 MoSPI Table 6 report, 132 projects contain `(-)` for revised date of commissioning, indicating unrevised or ongoing review schedule status.  
  > **Only rows where `is_eligible_schedule_target == 1` may enter supervised schedule modeling.**  
  > The 132 missing schedule outcomes **MUST remain excluded** from supervised schedule training and evaluation.  
  > They must **never** be imputed as zero slippage or assigned negative labels, which would introduce severe false-negative bias.

---

## 3. Evaluation Design & Limitations

### 3.1 Design Framework: Retrospective 12-Month Horizon Evaluation
The evaluation protocol explicitly characterizes this setup as a:
**"Retrospective 12-month horizon evaluation."**

The protocol preserves the real-world temporal forecasting direction:
* **FEATURES:** Derived exclusively from information available at or before **July 31, 2025**.
* **OUTCOME:** Derived exclusively from the reported **July 2026** official MoSPI snapshot.

### 3.2 Formal Protocol Constraints & Disclaimers
Because the current empirical dataset contains one primary 12-month forecast transition (July 2025 cutoff $\rightarrow$ July 2026 outcome), the following boundaries are mandatory:
1. **DO NOT claim multi-period temporal cross-validation.** Multi-period temporal rolling-window validation cannot be conducted until additional subsequent annual snapshots (e.g., 2027) are available.
2. **DO NOT claim broad temporal generalisation.** The models are validated on the 2025 $\rightarrow$ 2026 macroeconomic and operational window.
3. **DO NOT randomly mix future observations into the training data.** No July 2026 information may enter training feature sets under any circumstances.

---

## 4. Initial Baseline Strategy: Majority-Class Benchmark

Prior to evaluating any machine learning model, a naive majority-class benchmark must be computed to establish the empirical floor.

### 4.1 Cost Overrun Majority Benchmark
* **Rule:** Predict every project as class `0` (no cost overrun $> 5\%$).
* **Empirical Performance:**
  * **Accuracy:** $\frac{305}{437} = 69.79\%$
  * **Balanced Accuracy:** $50.00\%$
  * **Precision (Class 1):** $0.00\%$
  * **Recall (Class 1):** $0.00\%$
  * **F1-Score (Class 1):** $0.0000$
  * **ROC-AUC:** $0.5000$ (random / non-discriminative rank ordering)
  * **PR-AUC (Average Precision):** $0.3021$ (equivalent to positive prevalence)
  * **Brier Score:** $0.3021$

### 4.2 Schedule Slippage Majority Benchmark
* **Rule:** Predict every eligible project as class `1` (slippage $\ge 3$ months).
* **Empirical Performance (on $N=305$ eligible):**
  * **Accuracy:** $\frac{257}{305} = 84.26\%$
  * **Balanced Accuracy:** $50.00\%$
  * **Precision (Class 1):** $\frac{257}{305} = 84.26\%$
  * **Recall (Class 1):** $100.00\%$
  * **F1-Score (Class 1):** $0.9146$
  * **ROC-AUC:** $0.5000$
  * **PR-AUC (Average Precision):** $0.8426$ (equivalent to positive prevalence)
  * **Brier Score:** $0.1574$

### 4.3 Evaluation Reporting Standard
> [!WARNING]
> **Do not present accuracy alone.**  
> High accuracy (e.g., 84.26% on schedule) is trivially achieved by a majority predictor that possesses zero discriminating capability.  
> For schedule classification specifically, evaluation must emphasize:
> **PR-AUC, Recall, Precision, F1-Score, Balanced Accuracy, and the full Confusion Matrix.**

---

## 5. Logistic Regression Baseline Specification

The first machine learning model to be evaluated in Module 3 is **Regularized Logistic Regression**.

### 5.1 Justification
1. **Interpretability:** Provides transparent, monotonic linear log-odds weights directly inspectable by infrastructure domain experts and auditors.
2. **Strong Conventional Benchmark:** Represents the standard econometric and statistical modeling baseline for binary risk events.
3. **Calibrated Probabilities:** Naturally produces posterior probability estimates via the sigmoid link function $\sigma(z) = \frac{1}{1 + e^{-z}}$.
4. **Driver Analysis:** Direct odds-ratio extraction ($\exp(\beta_j)$) satisfies the project objective of ranking primary risk drivers.
5. **Direct Problem Statement Alignment:** Fulfills the requirement to evaluate machine learning improvements against conventional statistical methods.

### 5.2 Status
> [!CAUTION]
> **DO NOT train Logistic Regression in Phase 1.**  
> Model fitting, hyperparameter selection, and validation will take place strictly in subsequent execution phases.

---

## 6. Feature Policy & Leakage Invariants

### 6.1 Safe Baseline Predictors
All baseline predictors must represent information available on or before **July 31, 2025**:

1. `feat_log_original_cost` — $\ln(1 + \text{original\_cost})$ (Numeric, scale control)
2. `feat_expenditure_to_original_cost_ratio` — Financial burn ratio at cutoff (Numeric)
3. `feat_physical_progress_pct` — Reported physical work completion percentage (Numeric)
4. `feat_physical_vs_financial_divergence` — Divergence between physical progress and expenditure ratio (Numeric)
5. `feat_project_age_months` — Project age from sanction/approval date to cutoff (Numeric, 1 missing value)
6. `feat_is_missing_approval_date` — Binary indicator for missing sanction date (Binary)
7. `feat_remaining_original_duration_months` — Months remaining until original target commissioning date (Numeric)
8. `feat_is_past_original_completion` — Binary indicator for project already past original target date at cutoff (Binary)
9. `feat_state` — Geographical jurisdiction / state location (Categorical)
10. `feat_agency` — Implementing central/state public sector agency (Categorical)

**Approved Supporting Numeric Source Variables:**
Where already present in the PIT dataset to support feature construction or scaling:
* `feat_original_cost_crore` — Unlogged original project cost in ₹ Crore.
* `feat_cumulative_expenditure_crore` — Unlogged cumulative expenditure in ₹ Crore.

### 6.2 Strictly Prohibited Fields
To prevent data leakage, the following fields are **strictly prohibited** from the baseline feature matrix ($X$):
* Any **July 2026 variables** (e.g., `revised_cost_cr_2026`, `revised_date_of_commissioning_2026`).
* **Future target variables** (`cost_overrun_5pct_2026`, `time_overrun_3m_2026`).
* **Future outcome fields** (`future_total_cost_escalation_2026`, `future_schedule_slippage_months_2026`).
* **Future physical progress** or **future expenditure** from July 2026.
* **Pre-cutoff revised cost (`revised_cost_cr_2025`)** and **pre-cutoff reported delay (`delay_months_2025`)**: Excluded from baseline predictors because they represent concurrent revisions rather than structural baseline predictors.
* **Sector:** Do not introduce sector into the first baseline unless the existing feature contract explicitly authorizes it (not present in the 26 PIT dataset columns).

---

## 7. Categorical Encoding Policy

* **Target Variables:** `feat_state` and `feat_agency` are approved categorical predictors.
* **Leakage Prevention Rule:**
  * Categorical variables must be encoded **without target leakage**.
  * **Preferred First Implementation:** **One-Hot Encoding** (`OneHotEncoder(handle_unknown='ignore', sparse_output=False)`).
  * The encoder **MUST be fitted only on training data**.
  * **Never fit the encoder on the complete dataset before splitting.**
  * Unseen categories in validation/test folds are mapped to all-zero indicator vectors.
  * **No target encoding** in the first baseline.

---

## 8. Preprocessing Pipeline Protocol

The eventual model pipeline will execute the following disciplined sequence:

```
[ Raw Train Data (Fold k) ]
       │
       ├──> Separate X_train and y_train
       │
       ├──> Identify numeric columns & categorical columns
       │
       ├──> Numeric Imputation: Fit SimpleImputer(strategy='median') on X_train numeric
       │
       ├──> Categorical Imputation: Fit SimpleImputer(strategy='most_frequent') on X_train categorical
       │
       ├──> Categorical Encoding: Fit OneHotEncoder(handle_unknown='ignore') on X_train categorical
       │
       ├──> Feature Scaling (if linear model): Fit StandardScaler() on X_train numeric
       │
       └──> Fit Estimator (LogisticRegression) on transformed X_train
              │
              ▼
[ Apply Fitted Pipeline to Transform Validation / Test Fold k (Zero Leakage) ]
```

1. Separate features ($X$) and targets ($y$).
2. Identify numerical columns and categorical columns.
3. Impute missing numerical values (`feat_project_age_months`) using statistics computed **strictly on training data**.
4. Impute missing categorical values (if any) using training data only.
5. One-hot encode categorical variables using an encoder fitted **strictly on training data**.
6. Transform validation/test data using the fitted training pipeline without re-estimating any parameters.

---

## 9. Metric Policy & Evaluation Hierarchy

### 9.1 Cost Overrun Model (`cost_overrun_5pct_2026`)
* **Primary Metrics:**
  * **ROC-AUC:** Overall discriminatory ranking across all thresholds.
  * **PR-AUC (Average Precision):** Area under the Precision-Recall curve, essential given class imbalance (30.2% positive).
* **Secondary Metrics:**
  * Precision, Recall, F1-Score.
  * Confusion Matrix ($TP, FP, TN, FN$).
  * Brier Score / calibration curve to assess posterior probability reliability.

### 9.2 Schedule Slippage Model (`time_overrun_3m_2026`)
* **Primary Metrics:**
  * **PR-AUC:** Primary ranking metric for positive slippage events.
  * **Recall:** Sensitivity to detect delayed projects.
  * **Precision:** Reliability of slippage alerts.
  * **F1-Score:** Harmonic balance of precision and recall.
  * **Balanced Accuracy:** Macro average of sensitivity and specificity ($\frac{\text{Recall}_1 + \text{Recall}_0}{2}$), penalizing trivial majority predictions.
* **Secondary Metrics:**
  * **ROC-AUC:** Threshold-independent ranking measure.
  * **Confusion Matrix:** Explicit count of true/false positives and negatives.
* **Headline Metric Rule:** **Accuracy must not be the headline metric.**

---

## 10. Risk Interpretation & Operational Decision Support

Model output probabilities will eventually represent formal posterior risks:
1. **Cost Overrun Probability:**
   $$P\big(\text{cost overrun} > 5\% \;\big|\; \text{information available at July 31, 2025}\big)$$
2. **Schedule Slippage Probability:**
   $$P\big(\text{schedule slippage} \ge 3\text{ months} \;\big|\; \text{information available at July 31, 2025}\big)$$

### 10.1 Downstream Risk Tiers
These probabilities will later support tri-tier operational risk ranking:
* **LOW RISK:** Routine automated monitoring.
* **MEDIUM RISK:** Targeted engineering milestone reviews.
* **HIGH RISK:** Priority ministerial intervention, site inspection, and barrier mitigation.

### 10.2 Threshold Calibration Rule
> [!IMPORTANT]
> **Do not define final probability thresholds yet.**  
> Decision thresholds ($\tau_{\text{cost}}, \tau_{\text{sched}}$) must be determined empirically only after baseline model calibration, cost-utility curve analysis, and stakeholder alignment.

---

## 11. Protocol Compliance Verification Summary

This document governs all subsequent modeling scripts in Module 3. Any script or experiment that violates:
* Temporal cutoff (July 31, 2025),
* In-fold preprocessing isolation,
* Schedule censoring exclusion (132 projects), or
* Prohibited variable exclusion,
shall be deemed invalid and rejected by automated quality gates.

# Module 2C — Point-in-Time Feature Dataset Validation Report

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 2C — Point-in-Time Feature Engineering & Predictive Modeling  
**Phase:** Phase 2A — Target Semantics & Baseline Readiness Audit  
**Generated Dataset:** `data/interim/pit_features_july2025_to_july2026.csv`  
**Dataset SHA-256:** `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329`  
**Dataset Size:** 139,647 bytes  
**Input Source:** `data/processed/project_snapshot_panel.csv` (SHA-256: `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47`)  
**Validation Date:** September 5, 2026  
**Final Quality Verdict:** **PASS — CERTIFIED READY FOR BASELINE MODELING**  

---

## 1. Executive Summary

This report certifies the successful execution, target semantic audit, and baseline modeling readiness assessment of the **Module 2C Point-in-Time (PIT) Feature and Target Dataset**.

The dataset establishes the primary prospective machine learning cohort spanning the 12-month monitoring horizon:
* **Prediction Cutoff ($t$):** July 31, 2025 (`snapshot_date = "2025-07"`)
* **Outcome Horizon ($t + 12\text{m}$):** July 31, 2026 (`source_snapshot = "2026-07"`)
* **Physical Project Entity Unit:** `canonical_project_key`

Every predictor $X_t$ was derived strictly from observations certified at or before July 31, 2025. Outcome variables $Y$ and eligibility flags were constructed from the July 2026 monitoring snapshot with strict non-zero missingness preservation.

---

## 2. Cohort Accounting & Key Integrity Checks

| Audit Metric | Certified Result | Target Invariant | Compliance Status |
|---|:---:|:---:|:---:|
| **Total Cohort Records** | **437** | Exactly 437 primary longitudinal projects | **PASS** |
| **Unique Physical Projects** | **437** | 100% unique `canonical_project_key` | **PASS** |
| **Duplicate Entity Keys** | **0** | Exactly 0 duplicates | **PASS** |
| **Prediction Cutoff Value** | `2025-07-31` | Uniform across 100% of rows | **PASS** |
| **Snapshot Reporting Period**| `2025-07` | Uniform across 100% of rows | **PASS** |
| **Total Dataset Columns** | **26** | Exact match with Phase 1A Contract Schema | **PASS** |

### Trajectory Distribution
* **2-Snapshot Continuous PAIMANA (`2_SNAPSHOT_JULY`):** **390** physical projects (89.24%)
* **3-Snapshot Gold Standard (`3_SNAPSHOT`):** **47** physical projects (10.76%)

---

## 3. July 2025 Baseline Feature Availability & Distribution Checks

All 12 feature columns were audited for null counts, bounds, and economic realism across the 437 cohort records:

| Feature Identifier | Feature Family | Available Count | Null Count | Min Value | Max Value | Quality Invariant & Verification |
|---|---|:---:|:---:|:---:|:---:|---|
| `feat_original_cost_crore` | Financial | 437 | 0 | 153.71 | 108,000.00 | **PASS**: All positive $> 0$; no negative costs. |
| `feat_log_original_cost` | Financial | 437 | 0 | 5.04 | 11.59 | **PASS**: Finite real values; normalizes scale skew. |
| `feat_cumulative_expenditure_crore` | Financial | 437 | 0 | 0.00 | 124,623.00 | **PASS**: All $\ge 0$; zero valid for new projects. |
| `feat_expenditure_to_original_cost_ratio` | Financial | 437 | 0 | 0.00 | 8.07 | **PASS**: Finite; values $> 1.0$ reflect historical overrun. |
| `feat_physical_progress_pct` | Progress | 437 | 0 | 0.00% | 99.00% | **PASS**: Strictly bounded in $[0.0, 100.0]$. |
| `feat_physical_vs_financial_divergence` | Progress | 437 | 0 | -94.10 | 709.81 | **PASS**: Exact match for $(\text{Ratio}\times 100) - \text{Progress}$. |
| `feat_project_age_months` | Schedule | 436 | 1 | -10.0 | 482.0 | **PASS**: 1 legitimate source null preserved. |
| `feat_is_missing_approval_date` | Schedule | 437 | 0 | 0 | 1 | **PASS**: Exactly 1 record with missing approval flag. |
| `feat_remaining_original_duration_months` | Schedule | 437 | 0 | -148.0 | 377.0 | **PASS**: Negative indicates overdue original DoC. |
| `feat_is_past_original_completion` | Schedule | 437 | 0 | 0 | 1 | **PASS**: Exactly 163 projects overdue at cutoff (37.3%). |
| `feat_state` | Static | 437 | 0 | — | — | **PASS**: 100% assigned; 0 nulls. |
| `feat_agency` | Static | 437 | 0 | — | — | **PASS**: 100% assigned; 0 nulls. |

---

## 4. Target Semantics & Eligibility Analysis

### 4.1 Cost Target Semantics: `cost_overrun_5pct_2026`
$$\text{future\_total\_cost\_escalation\_2026} = \frac{\text{Reported July-2026 Revised Cost} - \text{Original Project Cost}}{\text{Original Project Cost}}$$

* **Semantic Definition:** `future_total_cost_escalation_2026` represents the reported cumulative budget revision relative to the original government-sanctioned cost.
  * **Positive Values:** Indicate an upward reported cost revision (cost escalation/overrun).
  * **Negative Values:** Indicate a downward reported cost revision.
  * **Critical Economic Precaution:** A negative cost escalation value must **NOT** automatically be interpreted as operational "cost savings" or efficiency gains. In government project monitoring, downward revisions frequently reflect contract de-scoping, split-tendering, transfer of sub-packages, or administrative re-estimation.
* **Binary Target:** `cost_overrun_5pct_2026 = 1` if reported cost escalation exceeds $5.0\%$, else `0`.

| Metric | Certified Count | Percentage of Total Cohort |
|---|:---:|:---:|
| **Total Cohort Size ($N_{\text{total}}$)** | **437** | 100.00% |
| **Eligible Records ($N_{\text{eligible}}$)** | **437** | **100.00%** |
| **Missing Target Records ($N_{\text{missing}}$)** | **0** | 0.00% |
| **Positive Events ($Y=1$, Cost Escalation $> 5\%$)** | **132** | **30.21%** |
| **Negative Events ($Y=0$, Cost Escalation $\le 5\%$)** | **305** | **69.79%** |
| **Effective Target Event Rate** | **30.21%** | Moderately balanced |

---

### 4.2 Schedule Target Semantics & Missingness: `time_overrun_3m_2026`
$$\text{future\_schedule\_slippage\_months\_2026} = \text{DateDiffInMonths}\big(\text{July-2026 Revised DoC}, \; \text{Original DoC}\big)$$

* **Semantic Definition:** Calendar months of schedule slippage from the contractual commissioning deadline to the revised commissioning date reported in July 2026.
* **Governing Rule on Missing Revised Completion Dates:**
  * Total longitudinal cohort: **437 projects**.
  * Eligible schedule target records: **305 projects** (69.79%).
  * Missing schedule target records: **132 projects** (30.21%).
* **Non-Conversion Invariant:** The 132 projects where July 2026 reported `(-)` (unrevised) for completion date must **NOT** be converted into negative labels ($Y=0$) or zero slippage.
* **Supervised Training Policy:**
  > [!IMPORTANT]
  > A missing revised completion date indicates that the future schedule outcome is **unobserved** for standard supervised schedule classification.  
  > These 132 observations remain fully preserved in the longitudinal dataset with `is_eligible_schedule_target = 0`, but must be **excluded from supervised training and evaluation** for the schedule slippage target unless a scientifically justified censoring/survival methodology (e.g. right-censored survival analysis) is explicitly introduced.

| Metric | Certified Count | Percentage |
|---|:---:|:---:|
| **Total Cohort Size ($N_{\text{total}}$)** | **437** | 100.00% |
| **Eligible Records ($N_{\text{eligible}}$)** | **305** | **69.79% of total** |
| **Missing Target Records ($N_{\text{missing}}$, Unrevised `(-)` in 2026)** | **132** | **30.21% of total** |
| **Positive Events ($Y=1$, Slippage $\ge 3\text{M}$)** | **257** | **84.26% of eligible / 58.81% of total** |
| **Negative Events ($Y=0$, Slippage $< 3\text{M}$)** | **48** | **15.74% of eligible / 10.98% of total** |
| **Effective Target Event Rate (Over Eligible Subcohort)** | **84.26%** | Severe class imbalance |

---

## 5. Modeling Readiness & Class Imbalance Warning

The empirical target distributions reveal critical asymmetries that must govern model evaluation in Module 3:

```
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬───────────────────────────┐
│ Prediction Target          │ Eligible N  │ Positives   │ Negatives   │ Baseline Class Imbalance  │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼───────────────────────────┤
│ Cost Overrun (>5%)         │ 437         │ 132 (30.2%) │ 305 (69.8%) │ Moderate (1 : 2.3)        │
│ Schedule Slippage (>=3M)   │ 305         │ 257 (84.3%) │ 48 (15.7%)  │ Severe Inverted (5.4 : 1) │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴───────────────────────────┘
```

### 5.1 Primary Evaluation Metrics (Accuracy Deprecated)
> [!WARNING]
> **Accuracy alone MUST NOT be used as the primary evaluation metric.**  
> In an 84.26% positive schedule environment, a naive dummy model predicting "delayed" for every project achieves an 84.26% accuracy while offering zero discriminatory power.

#### Required Cost Classification Metrics
1. **ROC-AUC:** Overall ranking discrimination across thresholds.
2. **PR-AUC (Average Precision):** Area under the Precision-Recall curve (more informative for minority class).
3. **Precision, Recall, F1-Score:** Evaluated at decision threshold $\tau = 0.5$ and optimal F1 threshold.
4. **Confusion Matrix:** Full $(TP, FP, TN, FN)$ accounting.
5. **Brier Score / Calibration:** To assess probability reliability.

#### Required Schedule Classification Metrics
1. **PR-AUC (Precision-Recall AUC):** Primary ranking metric to prevent majority-class distortion.
2. **Balanced Accuracy:** Macro-averaged recall across both positive and negative classes:
   $$\text{Balanced Accuracy} = \frac{\text{Sensitivity} + \text{Specificity}}{2}$$
3. **Recall (Sensitivity):** Ability to capture genuine slippage events.
4. **Precision:** Minimizing false alarms.
5. **Confusion Matrix:** Explicit accounting of the 48 non-delayed negative cases.

### 5.2 Mandatory Majority-Class Benchmarks

Any trained model in Module 3 must demonstrate statistically significant value added over the following trivial majority-class baselines:

* **Cost Classification Majority-Class Baseline (All Negative):**
  * Predicted Class: $\hat{Y} = 0$ for all projects.
  * Baseline Accuracy: **69.79%** ($305 / 437$).
  * Baseline Recall: **0.00%**.
  * Baseline Precision: **0.00%** (Undefined).
  * Baseline F1: **0.0000**.
  * Baseline ROC-AUC: **0.5000**.
* **Schedule Classification Majority-Class Baseline (All Positive):**
  * Predicted Class: $\hat{Y} = 1$ for all eligible projects.
  * Baseline Accuracy: **84.26%** ($257 / 305$).
  * Baseline Recall: **100.00%** ($257 / 257$).
  * Baseline Precision: **84.26%** ($257 / 305$).
  * Baseline F1: **0.9146**.
  * Baseline Balanced Accuracy: **50.00%** ($\frac{1.0 + 0.0}{2}$).
  * Baseline ROC-AUC: **0.5000**.

---

## 6. Temporal Anti-Leakage Audit

The dataset was audited against the mandatory anti-leakage rules:

1. **Cutoff Boundary Barrier (Rule LR-01):**
   * Maximum date of any predictor source record: `2025-07-31`.
   * July 2026 monitoring records appear strictly in target outcome columns.
2. **Exclusion of Revised Cost Predictor (Rule LR-02):**
   * Neither `revised_cost_crore(2025)` nor `revised_cost_crore(2026)` appears in feature columns $X_t$.
3. **Exclusion of Revised Completion Date Predictor (Rule LR-03):**
   * Neither `revised_completion_date(2025)` nor `revised_completion_date(2026)` appears in feature columns $X_t$.
4. **Exclusion of Forward Deltas:**
   * Zero forward-looking delta variables ($\Delta \text{Cost}$, $\Delta \text{Progress}$) exist in $X_t$.
5. **No Retrospective Imputation (Rule LR-05):**
   * Zero July 2026 values were used to backfill missing July 2025 values (e.g. Serial 525 missing approval date is preserved as `NaN`).

---

## 7. Detailed 10-Project Audit Sample

The table below presents a side-by-side audit of 10 randomly sampled projects comparing the constructed feature dataset directly against the frozen source panel:

| Project Key | Project Name | Agency | Baseline Orig Cost (Cr) | July-26 Rev Cost (Cr) | Cost Escalation % (Flag) | Orig DoC | July-26 Rev DoC | Schedule Slippage (Flag) |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `PROJ-PAIMANA-400010` | Construction of Terminal | AAI | 480.0 | 640.0 | +33.3% (1) | 2021-09 | 2026-07 | +58m (1) |
| `PROJ-PAIMANA-400013` | Saturation 4G mobile cove | DoT | 26,316.0 | 15,392.8 | -41.5% (0) | 2024-06 | 2027-03 | +33m (1) |
| `PROJ-PAIMANA-400018` | HURA C OCP | ECL - CIL | 859.4 | 859.4 | 0.0% (0) | 2029-03 | `(-)` (NA) | **NA (NA)** |
| `PROJ-PAIMANA-400022` | Taranga Hill-Abu Road via | NWR | 2,798.0 | 3,198.2 | +14.3% (1) | 2030-07 | 2030-07 | 0m (0) |
| `PROJ-PAIMANA-400023` | Construction of New BG li | SWR - II | 749.0 | 749.0 | 0.0% (0) | 2028-04 | 2030-03 | +23m (1) |
| `PROJ-PAIMANA-400033` | BHATADI EXPANSION OC | WCL | 580.6 | 580.6 | 0.0% (0) | 2028-03 | `(-)` (NA) | **NA (NA)** |
| `PROJ-PAIMANA-400045` | Proposed 6 nos Road Over | ECoR - II | 168.3 | 168.3 | 0.0% (0) | 2025-03 | 2025-01 | -2m (0) |
| `PROJ-PAIMANA-400062` | Raghunathpur Thermal Powe | DVC | 17,673.0 | 17,673.0 | 0.0% (0) | 2029-06 | `(-)` (NA) | **NA (NA)** |
| `PROJ-PAIMANA-400087` | Redevelopment of Sobhasan | ONGC | 885.6 | 1,347.6 | +52.2% (1) | 2026-02 | `(-)` (NA) | **NA (NA)** |
| `PROJ-PAIMANA-400100` | Sardar Gouthu Latchanna T | Water Res-AP | 353.1 | 1,023.2 | +189.8% (1) | 2019-12 | 2026-06 | +78m (1) |

*Audit Findings:*
* Projects with unrevised completion dates in 2026 (`PROJ-PAIMANA-400018`, `400033`, `400062`, `400087`) correctly receive `NaN` slippage and `is_eligible_schedule_target = 0`.
* Project `PROJ-PAIMANA-400045` was completed 2 months ahead of original target, correctly producing $-2\text{m}$ slippage and binary flag $0$.
* Cost escalations and slippages match source records with 100% precision.

---

## 8. Determinism & Immutability Verification

1. **Deterministic Execution:**
   Re-running `src/features/build_pit_features.py` from scratch produces byte-for-byte identical output:
   $$\text{SHA256}(\text{Run 1}) \equiv \text{SHA256}(\text{Run 2}) \equiv \texttt{052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329}$$
2. **Source Input Immutability:**
   $$\text{SHA256}(\texttt{data/processed/project\_snapshot\_panel.csv}) \equiv \texttt{9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47}$$
   The frozen longitudinal panel was accessed in read-only mode and remains strictly unmodified.

---

## 9. Test Suite Certification

Executed automated test discovery:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

```text
Ran 77 tests in 1.829s

OK
```
All **77 tests passed** across all repository test suites:
* `tests/test_pit_features.py`: **16/16 PASS**
* `tests/test_project_identity_resolution.py`: **19/19 PASS**
* `tests/test_canonical_snapshots.py`: **10/10 PASS**
* `tests/test_extract_table6.py`: **8/8 PASS**
* `tests/test_extract_table4_july2025.py`: **8/8 PASS**
* `tests/test_extract_table7_june2025.py`: **8/8 PASS**
* `tests/test_data_validation.py`: **8/8 PASS**

---

## 10. Final Readiness Determination

**Verdict:** **PASS — CERTIFIED READY FOR BASELINE MODELING**.  
`data/interim/pit_features_july2025_to_july2026.csv` is fully validated, completely leakage-free, and certified for prospective machine learning evaluation in Module 3.

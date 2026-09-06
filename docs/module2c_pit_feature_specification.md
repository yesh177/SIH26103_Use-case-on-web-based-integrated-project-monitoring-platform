# Module 2C — Formal Point-in-Time (PIT) Feature Specification

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 2C — Point-in-Time Feature Engineering & Predictive Modeling  
**Phase:** Phase 1A — Formal Specification (Revised Methodology)  
**Status:** **SPECIFICATION COMPLETE — READY FOR REVIEW (NO CODE/DATA MUTATIONS)**  
**Specification Date:** September 5, 2026  
**Governing Inputs:**
* `data/processed/project_identity_map.csv` (SHA-256: `16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb`)
* `data/processed/project_snapshot_panel.csv` (SHA-256: `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47`)

---

## 1. Executive Summary & Design Principles

Module 2C defines the formal statistical, temporal, and economic feature space for predicting infrastructure project risks (cost escalations and schedule slippages) across central sector infrastructure projects monitored by the Ministry of Statistics and Programme Implementation (MoSPI).

### Non-Negotiable Engineering Principles
1. **Strict Prospective Causality:** An infrastructure risk intelligence system deployed in operational governance must predict outcomes before they occur. Every predictor $X_t$ must be strictly constructible from information published and certified at or before the prediction cutoff date $t$.
2. **Zero Temporal Leakage:** Post-cutoff information, subsequent contract revisions, billing receipts, delayed completion logs, and forward-looking audit reports are strictly barred from entering the feature matrix $X_t$.
3. **Immutability of Frozen Artifacts:** The processed datasets established in Module 2B (`project_identity_map.csv` and `project_snapshot_panel.csv`) are permanent and immutable. Feature engineering code will ingest these files as read-only inputs without altering their contents, schema, or row ordering.
4. **Transparent Governance Over Mechanical Heuristics:** Missing values represent real-world administrative states (e.g. unrevised commissioning targets, unrecorded dates) and must never be masked with arbitrary imputations (e.g. filling missing dates with Unix epoch or missing costs with zero).

---

## 2. Prospective Prediction Task Definition

### 2.1 Prediction Cutoff & Forecast Horizon

```
                                  PREDICTION CUTOFF (t)
                                     July 31, 2025
                                           │
  HISTORICAL / STATUS OBSERVATION WINDOW    │    PROSPECTIVE 12-MONTH OUTCOME WINDOW
  Snapshot: July 2025 (Table 4)             │    Snapshot: July 2026 (Table 6)
  [t - ∞  ───────────────►  t = 2025-07-31] │    [t = 2025-07-31  ───────────────►  t+12m = 2026-07-31]
                                           │
  Feature Vector: X_i(t)                    │    Outcome Targets: Y_i(t -> t+12m)
  (Static baselines, expenditure to date,   │    (12M Future Cost Escalation,
   physical progress, inception duration)   │     12M Future Schedule Slippage)
                                           │
 ──────────────────────────────────────────┴──────────────────────────────────────────────► Time
```

* **Prediction Cutoff ($t$):** **July 31, 2025** (MoSPI Table 4 reporting cutoff period: `2025-07`).
* **Forecast Horizon ($\Delta$):** Exactly **12 months** forward (July 31, 2025 $\rightarrow$ July 31, 2026, MoSPI Table 6 reporting period: `2026-07`).
* **Prediction Unit ($i$):** One resolved physical infrastructure project identified by `canonical_project_key`.
* **Primary Modeling Cohort:** All physical projects $i$ possessing both:
  1. A valid, verified baseline observation at $t = \text{2025-07}$ in `project_snapshot_panel.csv`.
  2. A valid, verified outcome observation at $t + 12\text{m} = \text{2026-07}$ in `project_snapshot_panel.csv`.

### 2.2 Primary Cohort Accounting & Completed Project Sensitivity Rule

From the Module 2B verified longitudinal panel:
* Total July 2025 observations: **791**
* Observations unmerged / review-flagged: **247**
* Single-snapshot July 2025 projects: **349**
* **Total Verified Longitudinal July 2025 $\leftrightarrow$ July 2026 Trajectory Cohort:** Exactly **`437` physical projects**:
  * **390 projects:** Continuous 12-month PAIMANA trajectory (`2025-07 + 2026-07`).
  * **47 projects:** Gold-standard 3-snapshot continuous trajectory (`2025-06 + 2025-07 + 2026-07`).

#### Completed Project Policy (Sensitivity Rule)
* **No Permanent Removal at Specification Stage:** All 437 projects are strictly retained in the primary longitudinal cohort.
* **Sensitivity Cohort Definition:** Projects with $\text{physical\_progress\_pct} \ge 99.0\%$ at July 2025 may optionally be excluded from an "Active Execution Risk" sensitivity analysis during model evaluation. The primary dataset preserves all 437 projects with explicit progress indicators to ensure full reproducibility.

---

## 3. Observation / Label Formalism & Prospective Target Definitions

For every project $i$ in the primary cohort, the prospective learning pair is formulated as:

$$\big(\mathbf{x}_i(t), \; \mathbf{y}_i(t \to t+12\text{m})\big)$$

### 3.1 Feature Vector Formulation $\mathbf{x}_i(t)$
$$\mathbf{x}_i(t) = \mathcal{H}\Big(\big\{ z_i(\tau) \mid \tau \le \text{2025-07-31} \big\}\Big)$$
Where $z_i(\tau)$ denotes project administrative attributes, sanctioned original cost, inception contractual dates, cumulative financial expenditure, and engineer-certified physical progress reported on or before July 31, 2025.

### 3.2 Primary Prospective Cost Target

#### Continuous Target: `future_total_cost_escalation_2026`
$$\text{future\_total\_cost\_escalation\_2026} = \frac{\text{Reported July-2026 Revised Cost} - \text{Original Project Cost}}{\text{Original Project Cost}}$$

* **Future Outcome Source Field:** `revised_cost_crore` reported in the **July 2026 Table 6** snapshot.
* **Baseline Cost Denominator:** `original_cost_crore` established at project sanction.
* **Semantic Interpretation:** `future_total_cost_escalation_2026` is a reported cost revision relative to original sanctioned cost. Positive values indicate an upward reported cost revision (cost escalation). Negative values indicate a downward reported cost revision. A negative value must **NOT** automatically be interpreted as operational "cost savings" because it may reflect project de-scoping, split tendering, transfer of sub-packages, or administrative re-estimation.
* **Non-Zero Missingness Semantics:** Projects with unpopulated, missing, or non-numeric July-2026 revised cost must **NOT** be treated as zero. If July-2026 revised cost is missing, the target is `NaN` and the project is flagged as ineligible for cost-target supervised training.
* **Exclusion of July-2025 Revised Cost from Predictors:** `revised_cost_crore` from July 2025 is **strictly excluded** from baseline predictors because it represents an already-observed cost revision at the prediction cutoff. Using it as a predictor would encode pre-existing status into $X_t$ and distort model evaluation.

#### Binary Target: `cost_overrun_5pct_2026`
$$\text{cost\_overrun\_5pct\_2026} = \begin{cases} 1 & \text{if } \text{future\_total\_cost\_escalation\_2026} > 0.05 \\ 0 & \text{if } \text{future\_total\_cost\_escalation\_2026} \le 0.05 \\ \text{NaN} & \text{if } \text{future\_total\_cost\_escalation\_2026 is null} \end{cases}$$

---

### 3.3 Primary Prospective Schedule Target

#### Continuous Target: `future_schedule_slippage_months_2026`
$$\text{future\_schedule\_slippage\_months\_2026} = \text{DateDiffInMonths}\big(\text{July-2026 Revised Completion Date}, \; \text{Original Completion Date}\big)$$

* **Future Outcome Source Field:** `revised_completion_date` reported in the **July 2026 Table 6** snapshot.
* **Baseline Date Field:** `original_completion_date` established at project sanction.
* **Date Difference Function:** Calendar-month difference between the two dates:
  $$\text{DateDiffInMonths}(D_2, D_1) = (Y_2 - Y_1) \times 12 + (M_2 - M_1)$$
* **Non-Zero Missingness Semantics:** Projects without a valid July-2026 revised completion date (e.g. source reports `(-)` or missing) must **NOT** automatically receive zero slippage. Unrevised status indicates no formal extension was approved, which requires distinct handling.
* **Handling Missing Outcome Labels & Supervised Training Policy:**
  1. Total longitudinal cohort = 437 projects. Eligible schedule target records = 305; missing schedule target records = 132.
  2. The 132 projects with missing or unparseable July-2026 revised completion dates receive `NaN` for this target. Do **NOT** convert these 132 missing schedule outcomes into negative labels or zero slippage.
  3. **Operational Meaning:** Missing revised completion date means the future schedule outcome is **unobserved** for supervised schedule classification.
  4. These observations are **fully preserved** in the longitudinal panel and feature dataset (`is_eligible_schedule_target = 0`), but are **excluded from supervised training and evaluation** for the schedule target unless a future scientifically justified censoring/survival methodology is introduced.
  5. Eligible event distribution: Positive ($\ge 3	ext{M}$) = 257, Negative ($< 3	ext{M}$) = 48. Event rate among eligible = 84.26%.

#### Binary Target: `time_overrun_3m_2026`
$$\text{time\_overrun\_3m\_2026} = \begin{cases} 1 & \text{if } \text{future\_schedule\_slippage\_months\_2026} \ge 3 \\ 0 & \text{if } \text{future\_schedule\_slippage\_months\_2026} < 3 \\ \text{NaN} & \text{if } \text{future\_schedule\_slippage\_months\_2026 is null} \end{cases}$$

---

## 4. Formal Target Eligibility & Accounting Framework

In Phase 2, the pipeline will evaluate target availability across the 437 longitudinal projects using the following formal accounting template:

| Target Name | Total Longitudinal Projects ($N$) | Valid Target Records ($N_{\text{valid}}$) | Missing Target Records ($N_{\text{missing}}$) | Positive Events ($Y=1$) | Negative Events ($Y=0$) | Event Rate ($\%$) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `cost_overrun_5pct_2026` | 437 | 437 | 0 | 132 | 305 | 30.21% |
| `time_overrun_3m_2026` | 437 | 305 | 132 | 257 | 48 | 84.26% (of eligible) |

### Eligibility Flag Columns
* `is_eligible_cost_target`: Binary flag (`1` if `future_total_cost_escalation_2026` is not null, else `0`).
* `is_eligible_schedule_target`: Binary flag (`1` if `future_schedule_slippage_months_2026` is not null, else `0`).

---

## 5. Explicit Date Calculations & Duration Metrics

All calendar intervals are evaluated strictly with respect to the **July 31, 2025 prediction cutoff date** ($t_0 = \text{2025-07-31}$).

Source dates in MoSPI Table 4 report in `MM/YYYY` format (e.g. `03/2021`, `12/2028`). These are converted to standard calendar-month integer coordinates $(Y, M)$.

### 5.1 `feat_project_age_months`
* **Definition:** Calendar months elapsed from administrative approval to the July 31, 2025 cutoff:
  $$\text{feat\_project\_age\_months} = (2025 - Y_{\text{appr}}) \times 12 + (7 - M_{\text{appr}})$$
* **Missingness Semantics:** If `approval_date` is unpopulated in source (e.g. serials 525, 526, 648), the feature is assigned `NaN`. **Do not fabricate missing dates.**
* **Companion Indicator:** `feat_is_missing_approval_date = 1` if `approval_date` is missing, else `0`.

### 5.2 `feat_original_planned_duration_months`
* **Definition:** Total contractual duration sanctioned at inception:
  $$\text{feat\_original\_planned\_duration\_months} = (Y_{\text{orig\_end}} - Y_{\text{appr}}) \times 12 + (M_{\text{orig\_end}} - M_{\text{appr}})$$
* **Missingness Semantics:** Assigned `NaN` if either `approval_date` or `original_completion_date` is missing in source.

### 5.3 `feat_remaining_original_duration_months`
* **Definition:** Calendar months remaining from the July 31, 2025 cutoff to the original contractual completion date:
  $$\text{feat\_remaining\_original\_duration\_months} = (Y_{\text{orig\_end}} - 2025) \times 12 + (M_{\text{orig\_end}} - 7)$$
* **Interpretation:** Negative values indicate that the project has already overshot its original sanctioned deadline as of July 31, 2025.
* **Missingness Semantics:** Assigned `NaN` if `original_completion_date` is missing in source.

### 5.4 `feat_is_past_original_completion`
* **Definition:** Binary indicator of pre-existing overdue status:
  $$\text{feat\_is\_past\_original\_completion} = \begin{cases} 1 & \text{if } \text{feat\_remaining\_original_duration\_months} < 0 \\ 0 & \text{if } \text{feat\_remaining\_original_duration\_months} \ge 0 \\ \text{NaN} & \text{if missing} \end{cases}$$

---

## 6. Sector Feature Governance: Formal Exclusion

* **Status for First Baseline:** **`feat_sector = EXCLUDED`**.
* **Governance Rationale:** In July 2025 Table 4, `sector` was not reported as an independent column. While 47 projects have official historical sector labels from June 2025 OCMS Table 7, the remaining 390 projects do not possess verified source sector classifications.
* **Rule Against Ungoverned Inference:** Sector **must NOT be inferred from executing agency** without a formally governed, documented, and audited cross-walk table.
* **Future Work:** Sector standardization across PAIMANA agencies may be investigated later as a separate, controlled feature-engineering task subject to independent QA review.

---

## 7. Approved First Baseline Predictors (Minimal Safe Space)

To establish a defensible, leakage-free benchmark, the First Baseline Model will utilize **strictly 10 approved initial predictors**:

```
┌────┬──────────────────────────────────────────┬──────────────┬─────────────────────────────────────────┐
│ #  │ Feature Identifier                       │ Family       │ Mathematical / Operational Definition   │
├────┼──────────────────────────────────────────┼──────────────┼─────────────────────────────────────────┤
│ 1  │ feat_log_original_cost                   │ Financial    │ ln(1 + original_cost_crore)             │
│ 2  │ feat_expenditure_to_original_cost_ratio  │ Financial    │ cumulative_expenditure / original_cost  │
│ 3  │ feat_physical_progress_pct               │ Progress     │ Reported certified progress (0% - 100%) │
│ 4  │ feat_physical_vs_financial_divergence    │ Progress     │ (Exp Ratio * 100) - Progress %          │
│ 5  │ feat_project_age_months                  │ Schedule     │ Elapsed calendar months from approval   │
│ 6  │ feat_is_missing_approval_date            │ Schedule     │ Binary indicator (1 if date is missing) │
│ 7  │ feat_remaining_original_duration_months  │ Schedule     │ Contractual months to original DoC      │
│ 8  │ feat_is_past_original_completion         │ Schedule     │ Binary indicator (1 if overdue at cutoff)│
│ 9  │ feat_state                               │ Static       │ Administrative State / UT jurisdiction  │
│ 10 │ feat_agency                              │ Static       │ Implementing Central Agency / PSU       │
└────┴──────────────────────────────────────────┴──────────────┴─────────────────────────────────────────┘
```

### Categorical Encoding Protocol (Leakage Prevention)
* **Strict Cross-Validation Isolation:** Any encoding of `feat_state` and `feat_agency` must be fitted **ONLY on the training fold** during cross-validation.
* **No Naive Target Encoding:** Target encoding is **strictly barred** from the first baseline unless implemented through a rigorous out-of-fold cross-validation scheme.
* **Approved Baseline Encodings:**
  1. **Frequency Encoding:** Frequency of agency/state occurrences computed strictly on `train_fold`.
  2. **One-Hot Encoding:** Top-$K$ high-frequency agencies/states fitted strictly on `train_fold` with an `"OTHER"` fallback category.

---

## 8. Treatment of Sensitive & Prohibited Fields

```
┌───────────────────────────────────────────────┬──────────────────────┬─────────────────────────────────┐
│ Sensitive / Prohibited Field                  │ Safety Status        │ Governance Determination        │
├───────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────┤
│ July-2025 revised_cost_crore                  │ CONDITIONAL          │ EXCLUDED from baseline; encodes │
│                                               │                      │ pre-existing budget revision.   │
├───────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────┤
│ July-2025 revised_completion_date             │ CONDITIONAL          │ EXCLUDED from baseline; encodes │
│                                               │                      │ pre-existing time extension.    │
├───────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────┤
│ July-2026 revised_cost_crore                  │ PROHIBITED FROM X_t  │ Used ONLY as target label (Y).  │
├───────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────┤
│ July-2026 revised_completion_date             │ PROHIBITED FROM X_t  │ Used ONLY as target label (Y).  │
├───────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────┤
│ July-2026 cumulative_expenditure_crore        │ PROHIBITED FROM X_t  │ Future realization (HARD FAIL). │
├───────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────┤
│ July-2026 physical_progress_pct               │ PROHIBITED FROM X_t  │ Future realization (HARD FAIL). │
├───────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────┤
│ July-2026 start_date                          │ PROHIBITED FROM X_t  │ Unobservable at t (HARD FAIL).  │
├───────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────┤
│ June-2025 anticipated_cost_crore              │ PROHIBITED FROM X_t  │ Subjective projection.          │
├───────────────────────────────────────────────┼──────────────────────┼─────────────────────────────────┤
│ June-2025 anticipated_completion_date         │ PROHIBITED FROM X_t  │ Subjective projection.          │
└───────────────────────────────────────────────┴──────────────────────┴─────────────────────────────────┘
```

---

## 9. Missing-Data Governance & Policy

1. **Unavailable-in-Source $\ne$ Zero:**
   * A missing value in `approval_date` or `revised_completion_date` reflects administrative non-reporting or absence of approved revision.
   * Under no circumstances may missing dates be coerced to `1970-01-01`, missing costs coerced to `0.00`, or unrevised dates coerced to zero slippage.
2. **Zero Fabrication & Imputation Across Cutoff:**
   * **No Forward Imputation:** July 2025 missing values must **never** be imputed using values observed in July 2026 Table 6 (e.g. back-filling missing July 2025 approval dates from July 2026). Doing so creates catastrophic retrospective leakage.
   * **No Synthetic Forward-Filling:** Single-snapshot projects cannot be forward-filled to artificially construct longitudinal trajectories.
3. **Explicit Missingness Indicators:**
   * Where a feature possesses missing values in the July 2025 source, the numeric feature must remain `NaN` for tree models natively supporting sparsity, or median-imputed with an **explicit binary missingness indicator column** (`feat_is_missing_approval_date`).

---

## 10. Phase 2 Dataset Construction Contract

The feature engineering pipeline implemented in Phase 2 must produce a single standardized CSV dataset (`data/processed/feature_matrix_pit_july2025.csv` or staged interim equivalent) matching the exact schema below:

### 10.1 Project Identity & Temporal Keys
1. `canonical_project_key`: Resolved physical project identifier (e.g. `PROJ-PAIMANA-400033`). Primary key.
2. `source_project_id`: July-2025 source project identifier. Audit metadata only.
3. `project_name`: Full project title from July 2025. Audit metadata only.
4. `snapshot_date`: Baseline reporting period (`2025-07`).
5. `prediction_cutoff_date`: Standardized cutoff date (`2025-07-31`).

### 10.2 Feature Columns ($X_t$)
6. `feat_log_original_cost`: Float64, log-transformed sanctioned original cost.
7. `feat_original_cost_crore`: Float64, sanctioned original cost in ₹ Crore.
8. `feat_cumulative_expenditure_crore`: Float64, cumulative booked expenditure at $t$.
9. `feat_expenditure_to_original_cost_ratio`: Float64, capital absorption ratio at $t$.
10. `feat_physical_progress_pct`: Float64, certified physical progress percentage at $t$.
11. `feat_physical_vs_financial_divergence`: Float64, expenditure ratio % minus progress %.
12. `feat_project_age_months`: Float64, elapsed calendar months from approval to cutoff.
13. `feat_is_missing_approval_date`: Int64, `1` if approval date missing, else `0`.
14. `feat_remaining_original_duration_months`: Float64, months to original completion date.
15. `feat_is_past_original_completion`: Int64, `1` if overdue original DoC, else `0`.
16. `feat_state`: String / Categorical, administrative State / UT jurisdiction.
17. `feat_agency`: String / Categorical, central implementing agency / PSU.

### 10.3 Cost Target Columns
18. `future_total_cost_escalation_2026`: Float64, $(\text{Cost}_{2026} - \text{Original Cost}) / \text{Original Cost}$.
19. `cost_overrun_5pct_2026`: Int64, binary indicator (`1` if escalation $> 0.05$, `0` if $\le 0.05$, `NaN` if missing).

### 10.4 Schedule Target Columns
20. `future_schedule_slippage_months_2026`: Float64, calendar-month difference ($\text{Revised DoC}_{2026} - \text{Original DoC}$).
21. `time_overrun_3m_2026`: Int64, binary indicator (`1` if slippage $\ge 3\text{M}$, `0` if $< 3\text{M}$, `NaN` if missing).

### 10.5 Target Eligibility Flags
22. `is_eligible_cost_target`: Int64, `1` if `future_total_cost_escalation_2026` is valid, else `0`.
23. `is_eligible_schedule_target`: Int64, `1` if `future_schedule_slippage_months_2026` is valid, else `0`.

### 10.6 Provenance & Lineage Fields
24. `trajectory_type`: String, longitudinal trajectory cohort (`3_SNAPSHOT` or `2_SNAPSHOT_JULY`).
25. `spec_version`: String, specification version (`MODULE_2C_V1`).
26. `generated_at`: String, ISO-8601 UTC timestamp of pipeline execution.

---

## 11. Binding Anti-Leakage Rules (Pipeline Enforcement)

```
┌─────────┬──────────────────────────────┬────────────────────────────────────────────────────────┐
│ Rule ID │ Name                         │ Enforcement Verification Expression                    │
├─────────┼──────────────────────────────┼────────────────────────────────────────────────────────┤
│ LR-01   │ Temporal Cutoff Barrier      │ max(source_snapshot_date in X_t) <= '2025-07-31'       │
│ LR-02   │ Target Separation            │ X_t ∩ Y_(t->t+12m) = ∅ (disjoint feature & label sets)  │
│ LR-03   │ No Post-Cutoff Financials    │ No 2026 expenditures or cost revisions enter X_t       │
│ LR-04   │ No Post-Cutoff Progress      │ No 2026 progress percentages enter X_t                 │
│ LR-05   │ No Retrospective Imputation  │ Imputation models fitted strictly on X_train(t)        │
│ LR-06   │ Disjoint Trajectory Grouping │ GroupKFold by canonical_project_key (no cross-split)   │
│ LR-07   │ Static Key Neutrality        │ canonical_project_key & project_name stripped from X_t │
│ LR-08   │ Categorical Fold Isolation   │ State and Agency encoders fitted strictly on train fold│
└─────────┴──────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 12. Acceptance Criteria for Phase 2 Implementation

Phase 2 (Feature Matrix Construction) may proceed only when the following criteria are verified:

1. **Exact Cohort Size:** The generated feature matrix contains exactly **437 rows** corresponding to the verified longitudinal trajectory projects.
2. **Zero Missingness in Required Baselines:** Key identifiers (`canonical_project_key`), target eligibility flags, and baseline features must have zero unhandled nulls.
3. **Deterministic Output:** Re-running the feature construction pipeline produces identical row order, column schema, and SHA-256 checksum.
4. **Automated Leakage Gate Execution:** Automated test suite verifies that no column derived from July 2026 enters the feature columns $X_t$.
5. **No Mutation of Module 2B Artifacts:** Processed files in `data/processed/` retain identical byte counts and SHA-256 checksums throughout pipeline execution.

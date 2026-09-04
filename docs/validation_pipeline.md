# PAIMANA Panel Data Validation Pipeline & Automated Quality Gates

> **Project:** SIH26103 — Use Case on Web-Based Integrated Project Monitoring Platform  
> **Product:** PAIMANA Predictive Risk Intelligence  
> **Module:** Module 1D — Data Contract Enforcement & Validation Infrastructure  
> **Document:** `docs/validation_pipeline.md`  
> **Implementation Module:** `src/data/validate_panel.py`  
> **Test Suite:** `tests/test_panel_validation.py`  
> **Status:** SPECIFICATION & VALIDATION ENGINE READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING  

---

## 1. Overview & Architecture

The PAIMANA validation infrastructure provides automated quality gate enforcement for incoming longitudinal project monitoring panels. It guarantees that any dataset submitted to downstream feature engineering or predictive modeling strictly adheres to:

1. The **Canonical Data Contract** (`docs/data_contract.md`)
2. The **Point-in-Time Feature Invariants** (`docs/pit_feature_specification.md`)
3. The **Target Non-Leakage Principles** (`docs/target_definition.md`)
4. The **Binding Anti-Leakage Rules LR-01 through LR-07** (`docs/leakage_rules.md`)

```
   Raw CSV / Ingestion Stream
               │
               ▼
┌────────────────────────────────────────────────────────┐
│             src.data.validate_panel                    │
│                                                        │
│  [Gate 1] Schema & Canonical Columns                   │
│  [Gate 2] Identity & (Project, Period) Uniqueness      │
│  [Gate 3] Temporal Ordering & Date Formats             │
│  [Gate 4] Numeric Bounds & Non-Negativity Checks       │
│  [Gate 5] Panel Density & Consecutive Month Audit      │
│  [Gate 6] Point-in-Time Anti-Leakage (LR-01 .. LR-07)  │
│  [Gate 7] Velocity & Derived Lags Validation           │
│  [Gate 8] Future Target Non-Leakage Check              │
└────────────────────────────────────────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
  [HARD FAIL]        [PASS] ──► Feature Engineering & Modeling
(Exit Code 1/2)   (Exit Code 0)
```

---

## 2. CLI Usage & Execution

The validator is directly executable from the repository root as a Python module:

### Basic Panel Validation
```bash
python -m src.data.validate_panel path/to/dataset.csv
```

### Validation with Snapshot Cutoff (Enforcing LR-01 to LR-04)
To ensure no observations past a declared snapshot date $t$ are present:
```bash
python -m src.data.validate_panel path/to/dataset.csv --cutoff 2026-05
```

### Feature Matrix Pre-Flight Mode (Enforcing LR-05 & LR-06)
Checks that target columns (`target`, `future_slip`) and post-outcome realization fields are strictly absent:
```bash
python -m src.data.validate_panel path/to/features.csv --feature-matrix
```

---

## 3. Validation Gates & Enforcement Semantics

The validator operates across eight automated quality gates:

### Gate 1: Schema Invariant Gate
- **Required Fields:** `project_code`, `reporting_period`, `project_name`, `sector`, `line_ministry`, `original_cost_cr`, `original_end_date`, `expenditure_cr`.
- **Optional Fields:** `revised_cost_cr`, `revised_end_date`, `start_date`, `physical_progress_pct`, `agency`, `state`.
- **Hard Fail Condition:** Any required column is missing.
- **Snapshot Detection:** If `reporting_period` is absent but cross-sectional project records exist, the dataset is classified as `SNAPSHOT_ONLY`.

### Gate 2: Identity & Primary Key Gate
- **Rule DC-IDENTITY-01:** `project_code` cannot be null or empty.
- **Rule DC-IDENTITY-02:** `reporting_period` cannot be null or empty.
- **Rule DC-IDENTITY-03:** The composite key `(project_code, reporting_period)` must be strictly unique.
- **Hard Fail Condition:** Any null entity identifier or duplicate project-period combination.

### Gate 3: Temporal Integrity Gate
- **Rule DC-TIME-01:** `reporting_period` must match the standardized format `YYYY-MM`.
- **Rule DC-TIME-02:** Minimum 2 reporting periods required for longitudinal analysis.
- **Rule DC-TIME-03:** Date columns (`start_date`, `original_end_date`, `revised_end_date`) must be parseable calendar dates.
- **Hard Fail Condition:** Malformed dates or unparseable temporal strings.

### Gate 4: Numeric Integrity Gate
- **Rule DC-NUM-01:** `original_cost_cr` must be strictly $> 0.0$.
- **Rule DC-NUM-02:** `expenditure_cr` must be $\ge 0.0$.
- **Rule DC-NUM-03:** `revised_cost_cr` must be $\ge 0.0$ when populated.
- **Rule DC-NUM-04:** `physical_progress_pct` must lie strictly within $[0.0, 100.0]$.
- **Warning (DC-NUM-WARN-01):** `revised_cost < original_cost` logged as an audit warning (de-scoping). Values are flagged, never altered silently.

### Gate 5: Panel Density & Longitudinal Profile Gate
- Evaluates per-project temporal continuity:
  * Counts total observed periods per project.
  * Identifies temporal gaps (e.g. observed in May and July, missing June).
  * Measures consecutive month pairs available for velocity derivation.
- **Hard Fail Condition:** If 0 projects have multi-month observations, flags `SNAPSHOT_ONLY`.

### Gate 6: Point-in-Time (PIT) Anti-Leakage Gate
- **LR-01 to LR-04:** When a prediction cutoff $t$ is declared, flags any observation where $\texttt{reporting\_period} > t$ as a **HARD FAIL**.
- **LR-05 (Target Leakage):** In feature matrix mode (`--feature-matrix`), detects and rejects any column that:
  1. Matches the prefix `^future_` (e.g., `future_slip_days`, `future_cost_change`, `future_schedule_deterioration`).
  2. Matches the suffix `_target$` (e.g., `cost_overrun_target`, `schedule_delay_target`).
  3. Matches explicit target aliases: `target`, `label`, `y`.
  Triggers a **HARD FAIL (LR-05)** if found.
- **LR-06 (Post-Outcome Realizations):** In feature matrix mode, the presence of `actual_completion_date`, `commissioning_date`, `actual_doc`, `final_cost`, or `final_cost_overrun` triggers an immediate **HARD FAIL (LR-06)**.
- **LR-07 (Temporal Validation):** Documented in `docs/leakage_rules.md`. Currently **NOT-YET-IMPLEMENTED** in `validate_panel.py` as it belongs to the future downstream dataset splitting / evaluation module (e.g., `src/data/temporal_split.py`).

### Gate 7: Derived Velocity Feature Gate (Calendar Month Continuity)
- Velocity features (`recent_cost_change`, `recent_expenditure_change`, `recent_progress_change`, `recent_schedule_change`) represent monthly derivatives $\Delta x_t = x_t - x_{t-1}$.
- **One-Calendar-Month Continuity Invariant:** For every project observation at period $t_k$, the velocity feature is valid **only if** the immediately preceding observed record is from exactly **one calendar month prior** ($(t_k.\text{year} - t_{k-1}.\text{year}) \times 12 + (t_k.\text{month} - t_{k-1}.\text{month}) == 1$).
- **Missing Month / Gap Behavior:**
  * For the first observation of any project: velocity **must be `NaN`**.
  * If an intermediate month is missing (e.g. May 2026 $\to$ July 2026, gap of 2 months): velocity in July **must be `NaN`**.
  * Forward-filling, backward-filling, or computing multi-month differences as a single-month velocity is **strictly prohibited**.
- **Hard Fail Condition (DC-DERIVED-01):** Any non-NaN velocity value occurring on a non-consecutive month or first observation halts pipeline execution.

### Gate 8: Target Construction Non-Leakage Gate (Current Status vs. Future Deterioration)
- Evaluates candidate target columns (`target`, `label`, `future_*`, `*_target`):
- **Schedule Current Status Invariant (DC-TARGET-01):** If a candidate target is identical to current delay status ($\texttt{revised\_doc} > \texttt{original\_doc}$), it represents instantaneous state leakage rather than future deterioration. Triggers **HARD FAIL (DC-TARGET-01)**.
- **Cost Current Status Invariant (DC-TARGET-02):** If a candidate target is identical to current cost overrun status ($\texttt{revised\_cost} > \texttt{original\_cost}$), it represents instantaneous state leakage. Triggers **HARD FAIL (DC-TARGET-02)**.
- **Unobservable Future Horizons:** Any project lacking an authentic observation at future horizon $t+\Delta$ must be coded as `NaN` / `UNOBSERVABLE` and masked from model training loss.

---

## 4. Exit Codes & Return Semantics

| Exit Code | Status Label | Semantic Meaning | Action |
|---|---|---|---|
| `0` | **`PASS`** | Dataset satisfies all schema, identity, numeric, and PIT invariants. | Proceed to feature extraction / modeling. |
| `1` | **`FAIL`** | One or more **HARD FAIL** invariants breached (e.g., negative cost, duplicate key, future leakage). | Execution halted; audit log output to stderr. |
| `2` | **`SNAPSHOT_ONLY`** | Dataset is a single cross-sectional snapshot (e.g., `Projects_Report.csv`). | Rejects longitudinal modeling; allows descriptive reporting only if `--allow-snapshot` is set. |

---

## 5. Treatment of Missing Months & Unobservable Targets

1. **Strict Non-Interpolation:** If a project is observed in May and July but missing June, June is **not** interpolated or forward-filled. The velocity for July relative to May cannot be treated as a 1-month change and must remain `NaN`.
2. **Unobservable Future Targets:** If a project observed at cutoff $t$ has no corresponding record at future horizon $t+\Delta$, its target label is marked `UNOBSERVABLE`. The validator verifies that unobservable rows are masked from training loss.
3. **Downstream Temporal Splitting (LR-07):** Forward-chaining temporal partitions (Train $\le t_1$, Val $\in (t_1, t_2]$, Test $> t_2$) will be verified by the dedicated splitting module when longitudinal data is ingested.

---

## 6. Verification Against Cross-Sectional Snapshot (`Projects_Report.csv`)

When executed against the empirically available MoSPI export `C:\Users\Lenovo\Downloads\Projects_Report.csv`:

```text
==============================================================================
PAIMANA DATA CONTRACT & PANEL VALIDATION REPORT
==============================================================================
Target File:       C:\Users\Lenovo\Downloads\Projects_Report.csv
Execution Date:    2026-09-05 02:12:47
Declared Cutoff:   None (Full History)
Overall Status:    SNAPSHOT_ONLY
------------------------------------------------------------------------------
DIMENSIONALITY & IDENTITY:
  Total Rows:             1,981
  Unique Projects:        1,981
  Reporting Periods:      0 []
------------------------------------------------------------------------------
PANEL DENSITY & LONGITUDINAL PROFILE:
  Single-Period Projects: 1,981
  Multi-Period Projects:  0
  Max Observed Periods:   0
  Consecutive Pairs:      0
  Projects with Gaps:     0
------------------------------------------------------------------------------
VALIDATION GATES:  2 Hard Fails, 0 Warnings

HARD FAILS (Blocking Pipeline Execution):
  [1] Gate 1 (Schema) - DC-SCHEMA-01: Missing required canonical columns: ['reporting_period']
  [2] Gate 1 (Schema) - DC-SCHEMA-01: SNAPSHOT_ONLY - INSUFFICIENT FOR LONGITUDINAL PREDICTIVE MODELING: 'reporting_period' column is missing.
==============================================================================
RESULT: [SNAPSHOT_ONLY] Cross-sectional snapshot detected.
        INSUFFICIENT FOR LONGITUDINAL PREDICTIVE MODELING.
==============================================================================
```

The validation pipeline correctly rejected `Projects_Report.csv` with status **`SNAPSHOT_ONLY`** (Exit Code 2), proving that cross-sectional data cannot bypass the longitudinal modeling gate.

---

## 7. Current Status

```text
STATUS: SPECIFICATION & VALIDATION ENGINE READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING
```

*The automated data validation engine is operational. It stands as an active checkpoint ready to inspect and validate any incoming longitudinal data.*

# PAIMANA Module 1 — Historical Dataset Recovery & Validation Report

> **Project:** SIH26103 — Use Case on Web-Based Integrated Project Monitoring Platform  
> **Product:** PAIMANA Predictive Risk Intelligence  
> **Report Document:** `reports/module1_data_validation.md`  
> **Status:** Module 1 Audit Completed  
> **Date:** September 2026  

---

## 1. Executive Summary

This validation audit was conducted to inspect, recover, and validate the historical PAIMANA project-monitoring data required for **Module 1 (Predictive Risk Intelligence)**. 

The primary architectural requirement for Module 1 is the construction of a **leakage-safe, longitudinal point-in-time (PIT) dataset**:
$$\mathcal{X}(\text{project}_i, t_{\text{snapshot}}) \longrightarrow \mathcal{Y}(\text{project}_i, t_{\text{future\_outcome}})$$

Every predictive feature must be strictly observable **at or before** the snapshot timestamp $t_{\text{snapshot}}$. The target label must measure a genuine future outcome realized **strictly after** $t_{\text{snapshot}}$.

### Audit Verdict
**FINAL RECOMMENDATION:** **`NOT READY`** for Module 1 ML Modeling.

**Core Findings:**
1. The longitudinal 3-month dataset `PAIMANA_May_June_July_project_metrics_v2.csv` (and its precursor `PAIMANA_May_June_July_Table6_long.csv`) is **not present** in the repository or local filesystem.
2. The source PDF Flash Reports (`FlashReport_May2026.pdf`, `FlashReport_June_2026.pdf`, `FlashReport_July_2026.pdf`) have **not been ingested or parsed** into structured tabular format on this machine.
3. A single cross-sectional export exists at `C:\Users\Lenovo\Downloads\Projects_Report.csv` (1,981 projects), but it is a **single un-timestamped snapshot** lacking:
   - Longitudinal reporting periods (`reporting_period` / `month`),
   - Physical execution progress (`physical_progress_pct`),
   - Critical project timeline fields (`start_date`),
   - Temporal sequence required for velocity/rate-of-change calculation.
4. Constructing a future schedule-overrun target from the available data without genuine future realizations would constitute **label fabrication or data leakage**.

---

## 2. Dataset Inventory

A comprehensive recursive scan of the project repository, user directories (`Documents`, `Downloads`, `Desktop`), and secondary drives (`D:\`, `E:\`) was executed.

### 2.1 Repository Inventory (`paimana-predictive-risk/`)

| Path | Type | Status | Size | Description |
|---|---|---|---|---|
| `data/raw/` | Directory | Empty | 0 bytes | Designated raw data storage |
| `data/processed/` | Directory | Empty | 0 bytes | Designated processed data storage |
| `notebooks/` | Directory | Empty | 0 bytes | Analysis notebooks directory |
| `src/` (`data/`, `features/`, `models/`, `evaluation/`) | Directories | Empty | 0 bytes | Pipeline source modules |
| `docs/` | Directory | Empty | 0 bytes | Documentation directory |
| `tests/` | Directory | Empty | 0 bytes | Unit & integration tests |
| `.gitignore` | File | Present | 1,065 bytes | Git exclusion rules |
| `README.md` | File | Present | 9,675 bytes | Project architecture & roadmap |

### 2.2 External Files & Data Assets Found on Machine

| File / Location | Size | Rows / Obs | Unique Projects | Time Periods | Status / Usability |
|---|---|---|---|---|---|
| `PAIMANA_May_June_July_project_metrics_v2.csv` | — | — | — | — | **MISSING** (Not found on any drive) |
| `PAIMANA_May_June_July_Table6_long.csv` | — | — | — | — | **MISSING** (Not found on any drive) |
| `FlashReport_May2026.pdf` | — | — | — | — | **MISSING** (Not found on any drive) |
| `FlashReport_June_2026.pdf` | — | — | — | — | **MISSING** (Not found on any drive) |
| `FlashReport_July_2026.pdf` | — | — | — | — | **MISSING** (Not found on any drive) |
| `C:\Users\Lenovo\Downloads\Projects_Report.csv` | 459,344 bytes | 1,981 | 1,981 | None (Single snapshot) | **Found** (Cross-sectional only) |
| `C:\Users\Lenovo\OneDrive\Documents\project_monthly_panel.csv` | 0 bytes | 0 | 0 | None | **Empty directory / Reparse point** |
| `C:\Users\Lenovo\OneDrive\Documents\SIH26103\reserach\PAIMANA_Data_Dictionary.xlsx.xlsx` | 10,010 bytes | 14 entries | N/A | N/A | **Found** (Reference Data Dictionary) |
| `C:\Users\Lenovo\OneDrive\Documents\SIH26103\reserach\researchDATA_SOURCE_NOTES.md.txt` | 1,244 bytes | N/A | N/A | N/A | **Found** (Notes documenting PAIMANA acquisition challenge) |

---

## 3. Inspection of Available Data (`Projects_Report.csv`)

The only usable empirical data file located on the host machine is `C:\Users\Lenovo\Downloads\Projects_Report.csv`, downloaded on `03-09-2026 23:20:38`.

### 3.1 Dimensions & Structure
- **Raw File Lines:** 1,984 lines (Row 0: Title, Row 1: Empty, Row 2: Table Header, Rows 3–1983: Data records).
- **Project Records:** 1,981 rows.
- **Project Codes:** 1,981 unique codes (No duplicate project codes).
- **Format:** Comma-Separated Values (CSV).

### 3.2 Schema Analysis

| # | Column Name in CSV | Normalized Name | Inferred Dtype | Missing Count (%) | Semantic Definition |
|---|---|---|---|---|---|
| 0 | `Sr. No.` | `sr_no` | Integer | 0 (0.0%) | Sequential index |
| 1 | `Sector Name` | `sector_name` | String (Categorical) | 0 (0.0%) | Infrastructure sector (22 unique) |
| 2 | `Line Ministry` | `line_ministry` | String (Categorical) | 0 (0.0%) | Responsible ministry (17 unique) |
| 3 | `Project Code` | `project_code` | String / ID | 0 (0.0%) | Unique project identifier |
| 4 | `Project Name` | `project_name` | String (Text) | 0 (0.0%) | Project title |
| 5 | `Original Cost\n(in cr.)` | `original_cost_cr` | Float (Numeric) | 0 (0.0%) | Initial sanctioned cost in ₹ Crore |
| 6 | `Revised Cost\n(in cr.)` | `revised_cost_cr` | Float (Numeric) | 0 (0.0%) | Latest revised cost in ₹ Crore (0 = unrevised) |
| 7 | `Expenditure\n(in cr.)` | `expenditure_cr` | Float (Numeric) | 0 (0.0%) | Cumulative financial expenditure in ₹ Crore |
| 8 | `Original End Date` | `original_end_date` | Date (`DD/MM/YYYY`) | 0 (0.0%) | Initial target Date of Commissioning (DoC) |
| 9 | `Revised Date` | `revised_doc` | Date (`DD/MM/YYYY`) | 354 (17.87%) | Revised Date of Commissioning (DoC) |

### 3.3 Core Numeric Distributions

```text
Original Cost (in cr.):
  Count: 1,981 | Min: ₹102.00 Cr | 25%: ₹356.00 Cr | Median: ₹791.00 Cr | 75%: ₹1,512.00 Cr | Max: ₹108,000.00 Cr
  Values <= 0: 0

Revised Cost (in cr.):
  Count: 1,981 | Min: ₹0.00 Cr | 25%: ₹0.00 Cr | Median: ₹244.91 Cr | 75%: ₹1,216.90 Cr | Max: ₹188,000.00 Cr
  Values == 0 (Unrevised / Unrecorded): 905 (45.68%)

Expenditure (in cr.):
  Count: 1,981 | Min: ₹0.00 Cr | 25%: ₹35.57 Cr | Median: ₹226.46 Cr | 75%: ₹663.38 Cr | Max: ₹124,623.00 Cr
  Values == 0: 302 (15.24%)
```

### 3.4 Date Ranges
- `Original End Date`: Min = `2005-03-31`, Max = `2056-12-31`. (100% populated, 0 NaT).
- `Revised Date`: Min = `2019-09-30`, Max = `2034-09-30`. (354 missing / unrecorded).

---

## 4. Project Matching & Longitudinal Coverage Analysis

### 4.1 Expected vs. Actual Structure
The task required matching longitudinal project observations across three reporting periods:
- **Period 1:** `2026-05` (May 2026)
- **Period 2:** `2026-06` (June 2026)
- **Period 3:** `2026-07` (July 2026)

### 4.2 Longitudinal Coverage Table

| Coverage Pattern | Expected Count | Actual Count in Workspace | Reason / Finding |
|---|---|---|---|
| May only (`2026-05`) | > 0 | **0** | May Flash Report / Table 6 extraction missing |
| May + June | > 0 | **0** | Multi-period panel missing |
| May + June + July | > 0 | **0** | 3-month panel missing |
| June + July | > 0 | **0** | Multi-period panel missing |
| July only (`2026-07`) | > 0 | **0** | Snapshot date not encoded in available CSV |
| Single snapshot (Unspecified date) | N/A | **1,981** | `Projects_Report.csv` has no period identifier |

### 4.3 Inconsistencies & Duplicates
- **Duplicate Project Records:** In `Projects_Report.csv`, all 1,981 `Project Code` entries are unique.
- **Temporal Changes:** Because only one snapshot exists, delta metrics ($\Delta \text{cost}$, $\Delta \text{doc}$, $\Delta \text{expenditure}$) across months cannot be calculated empirically.

---

## 5. Data Quality & Anomaly Detection

Automated audit rules were run against all 1,981 records in `Projects_Report.csv`:

| Check Category | Validation Rule | Flagged Count | Percentage | Severity | Description / Interpretation |
|---|---|---|---|---|---|
| **Identity** | `project_code is not null` | 0 | 0.00% | Pass | All project codes are populated and unique. |
| **Non-negativity** | `original_cost >= 0` | 0 | 0.00% | Pass | All original costs are strictly positive ($\ge 102$ Cr). |
| **Non-negativity** | `expenditure >= 0` | 0 | 0.00% | Pass | No negative expenditures recorded. |
| **Logical Cost** | `revised_cost < original_cost` (where `revised > 0`) | 379 | 19.13% | Warning | 379 projects record a revised cost lower than original cost (scope de-scoping or partial project revision). |
| **Logical Cost** | `expenditure > original_cost` | 160 | 8.08% | Warning | 160 projects have already spent more than their initial sanctioned budget. |
| **Logical Cost** | `expenditure > revised_cost` (where `revised > 0`) | 53 | 2.68% | High | 53 projects have cumulative expenditure exceeding their authorized revised budget. |
| **Missingness** | `revised_doc is null` | 354 | 17.87% | Expected | Indicates projects operating under original schedule without formal revision. |
| **Physical Progress** | `physical_progress_pct` | **1,981 missing** | **100.0%** | **Critical Block** | The `Projects_Report.csv` export completely omits the physical progress column. |
| **Start Date** | `start_date` | **1,981 missing** | **100.0%** | **Critical Block** | Cannot compute project age or elapsed duration without project start date. |

---

## 6. Point-in-Time (PIT) Readiness & Target Construction Assessment

### 6.1 Variable-by-Variable PIT Classification

| Variable | Prediction Safe at Snapshot $t$? | Role | Leakage Risk & Handling |
|---|---|---|---|
| `project_code` | No (ID only) | Identifier / Audit | Must NOT be supplied to ML model (avoids memorizing project-specific identities). |
| `project_name` | No (Text / ID) | Display / Traceability | Exclude from feature set. |
| `sector_name` | **YES** | Categorical Feature | Static or initial project attribute; leakage-safe. |
| `line_ministry` | **YES** | Categorical Feature | Static administrative attribute; leakage-safe. |
| `original_cost_cr` | **YES** | Baseline Feature | Sanctioned at project inception; leakage-safe. |
| `original_end_date` | **YES** | Baseline Feature | Target completion established at inception; leakage-safe. |
| `expenditure_cr` | **YES** (with timestamp) | Time-dependent Feature | Safe ONLY IF recorded strictly as of snapshot date $t$. |
| `physical_progress_pct`| **YES** (with timestamp) | Time-dependent Feature | Safe as of snapshot date $t$. (Currently missing from CSV). |
| `start_date` | **YES** | Baseline Feature | Safe if inception date. (Currently missing from CSV). |
| `revised_cost_cr` | **LEAKAGE-SENSITIVE** | Context / Conditional | If revision was approved *before* $t$, safe as feature. If approved *after* $t$, **FUTURE LEAKAGE**. |
| `revised_doc` | **LEAKAGE-SENSITIVE** | Context / Candidate Label | If revised *before* $t$, safe as current delay signal. If revised *after* $t$, **FUTURE LEAKAGE**. |
| Realized Completion Date | **STRICT FUTURE LEAKAGE** | Target Evaluation Only | Never use as an input feature. |

### 6.2 Target Construction Analysis: Can a Valid Target Be Constructed?

The primary target required for Module 1 is **future schedule / time overrun**.

> **Rigorous PIT Rule:**
> A project cannot be labeled as a future overrun simply because its current `revised_doc > original_end_date`. That difference is a **current state signal** available at time $t$, not a realization occurring in the future.
>
> A valid future time-overrun target requires:
> $$\mathcal{Y}_{i, t, \Delta t} = \mathbb{I}\left( \text{Realized\_DoC}_{i, t + \Delta t} > \text{Forecasted\_DoC}_{i, t} \right) \quad \text{or} \quad \Delta \text{Slip}_{i, [t, t+\Delta t]} > 0$$

Because the available data contains only a **single snapshot** without a future horizon observation:
1. Future slippage between Month $t$ and Month $t+1$ or $t+2$ is **strictly unobservable**.
2. Labeling projects as "delayed" based on the current snapshot conflates **input features** with **future outcome labels**, producing circular model predictions and 100% synthetic correlation.
3. Therefore, under rigorous ML standards, the future target for all rows in the current repository state is:
   $$\mathbf{Target = UNOBSERVABLE}$$

---

## 7. Derived Features Specification (Prepared for Panel Dataset)

When the multi-period panel (`2026-05`, `2026-06`, `2026-07`) is recovered, the following feature engineering pipelines are specified and ready to execute:

### 7.1 Financial Derived Features
1. **Budget Revision Ratio:**
   $$\text{cost\_revision\_ratio}_t = \frac{\text{revised\_cost}_t}{\text{original\_cost}}$$
2. **Expenditure Utilization Factor (CUF):**
   $$\text{expenditure\_ratio}_t = \frac{\text{expenditure}_t}{\text{original\_cost}} \quad \text{and} \quad \text{revised\_expenditure\_ratio}_t = \frac{\text{expenditure}_t}{\text{revised\_cost}_t}$$
3. **Cost Overrun Amount to Date:**
   $$\text{cost\_overrun\_amount}_t = \max(0, \, \text{revised\_cost}_t - \text{original\_cost})$$

### 7.2 Schedule Derived Features
1. **Planned Duration (Months):**
   $$\text{planned\_duration} = \frac{\text{original\_end\_date} - \text{start\_date}}{30.4375}$$
2. **Elapsed Duration as of Snapshot (Months):**
   $$\text{elapsed\_duration}_t = \frac{\text{snapshot\_date}_t - \text{start\_date}}{30.4375}$$
3. **Current Slippage to Date (Months):**
   $$\text{current\_delay\_months}_t = \max\left(0, \, \frac{\text{revised\_doc}_t - \text{original\_end\_date}}{30.4375}\right)$$
4. **Schedule Pressure Index:**
   $$\text{schedule\_pressure}_t = \frac{\text{remaining\_work\_pct}_t}{\max\left(1, \, \text{remaining\_months}_t\right)}$$

### 7.3 Longitudinal / Velocity Features (Requires $\ge 2$ Snapshots)
1. **Monthly Physical Velocity:**
   $$\text{progress\_velocity}_{[t-1, t]} = \text{physical\_progress}_t - \text{physical\_progress}_{t-1}$$
2. **Monthly Spend Burn Rate:**
   $$\text{spend\_velocity}_{[t-1, t]} = \text{expenditure}_t - \text{expenditure}_{t-1}$$
3. **Schedule Re-slippage Signal:**
   $$\Delta \text{revised\_doc}_{[t-1, t]} = \text{revised\_doc}_t - \text{revised\_doc}_{t-1}$$

---

## 8. Final Decision & Actionable Remediation Plan

### Decision: **`NOT READY`**

### Technical Justification
| Prerequisite | Status | Impact on ML Validity |
|---|---|---|
| Longitudinal 3-month panel | ❌ Missing | Cannot observe temporal evolution or calculate rate of change |
| Physical progress field | ❌ Missing in available CSV | Key indicator of project delivery health is absent |
| Start date field | ❌ Missing in available CSV | Project duration, age, and schedule pace cannot be computed |
| Verified future target | ❌ UNOBSERVABLE | Training a model on current delay as target creates catastrophic data leakage |

### Required Actions to Achieve `READY` Status:
1. **Step 1:** Ingest the true **Table 6 ("All Ongoing Projects")** from the May, June, and July 2026 PAIMANA Flash Reports (which include `Agency`, `State`, `Start Date`, and `Physical Progress`).
2. **Step 2:** Construct the longitudinal long-format dataset:
   `data/raw/PAIMANA_May_June_July_Table6_long.csv` (schema: `[reporting_period, project_code, project_name, sector, agency, state, start_date, original_doc, revised_doc, original_cost, revised_cost, expenditure, physical_progress]`).
3. **Step 3:** Use May 2026 as the **Feature Snapshot Date** ($t$) and July 2026 as the **Outcome Horizon Date** ($t + 2\text{ months}$), creating a mathematically valid, leakage-free classification target:
   $$\mathcal{Y}_{i, \text{May}} = \mathbb{I}\left( \text{revised\_doc}_{i, \text{July}} > \text{revised\_doc}_{i, \text{May}} \quad \lor \quad \text{cost\_revision}_{i, \text{July}} > \text{cost\_revision}_{i, \text{May}} \right)$$
4. **Step 4:** Re-run validation checks and promote the verified dataset to `data/processed/paimana_may_june_july_validated.csv`.

---
*Report compiled autonomously following strict scientific and ML validation integrity standards. No models were trained; no synthetic data was fabricated.*

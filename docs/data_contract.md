# PAIMANA Ingestion Data Contract & Schema Invariants

> **Project:** SIH26103 — Use Case on Web-Based Integrated Project Monitoring Platform  
> **Product:** PAIMANA Predictive Risk Intelligence  
> **Document:** `docs/data_contract.md`  
> **Reference Inputs:** `PAIMANA_Data_Dictionary.xlsx.xlsx`, `reports/module1_data_validation.md`  
> **Status:** SPECIFICATION READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING  

---

## 1. Purpose & Ingestion Policy

This data contract establishes the binding schema, integrity constraints, format definitions, and validation gates required for any raw dataset to be ingested into the PAIMANA Predictive Risk Intelligence pipeline.

Any incoming historical extraction (e.g., Table 6 PDF parsed tables, official MoSPI CSV panels) must pass all automated validation gates defined in this contract before ingestion into `data/raw/` or transformation into `data/processed/`.

---

## 2. Canonical Ingestion Schema

The composite primary key for all incoming longitudinal tables is:
$$\mathbf{Primary\ Key} = \big(\texttt{project\_code}, \, \texttt{reporting\_period}\big)$$

| Column Identifier | Physical Type | Logical Type | Nullable? | Format / Permitted Values | Validation Constraint / Invariant | Business Meaning |
|---|---|---|---|---|---|---|
| `reporting_period` | String / Object | Temporal Key | **NO** | `YYYY-MM` (e.g. `2026-05`) | Valid monthly date string; matches report cycle | Cutoff month represented by the report |
| `project_code` | String / Object | Entity ID | **NO** | Alphanumeric string; length $4\text{–}12$ | Not null; trim whitespace; unique within `reporting_period` | Official MoSPI unique project tracking code |
| `project_name` | String / Object | Entity Name | **NO** | Text; length $3\text{–}255$ | Non-empty string | Official project title |
| `sector` | String / Object | Categorical | **NO** | Predefined sector list (e.g., Railways, Road Transport) | Validated against official sector dictionary | Infrastructure domain classification |
| `agency` | String / Object | Categorical | YES | Text string (e.g. NHAI, RVNL) | Trim whitespace; defaults to 'Unknown' if missing | Central Public Sector Enterprise or Agency |
| `state` | String / Object | Categorical | YES | Indian State/UT name or 'Multi-State' | Validated against Indian State/UT dictionary | Geographical footprint |
| `line_ministry` | String / Object | Categorical | **NO** | Text string (e.g. Ministry of Railways) | Trim whitespace; standard ministry name | Responsible administrative union ministry |
| `start_date` | Date / String | Baseline Date | YES (Flagged) | `YYYY-MM-DD` | If present: $\texttt{start\_date} \le \texttt{reporting\_period}$ | Date of project inception / foundation |
| `original_doc` | Date / String | Baseline Date | **NO** | `YYYY-MM-DD` | Valid calendar date; $\texttt{original\_doc} \ge \texttt{start\_date}$ | Sanctioned initial target Date of Commissioning |
| `revised_doc` | Date / String | Dynamic Date | YES | `YYYY-MM-DD` | If null, project operates on `original_doc` | Current anticipated Date of Commissioning |
| `original_cost_cr` | Float64 | Numeric (₹ Cr) | **NO** | Floating-point $\ge 0.0$ | $\texttt{original\_cost\_cr} > 0.0$ | Originally sanctioned project cost in ₹ Crore |
| `revised_cost_cr` | Float64 | Numeric (₹ Cr) | YES (Coded) | Floating-point $\ge 0.0$ | If $0.0$ or null, project operates on `original_cost_cr` | Latest sanctioned revised cost in ₹ Crore |
| `expenditure_cr` | Float64 | Numeric (₹ Cr) | **NO** | Floating-point $\ge 0.0$ | $\texttt{expenditure\_cr} \ge 0.0$ | Cumulative spending recorded to date in ₹ Crore |
| `physical_progress_pct` | Float64 | Numeric (%) | YES (Flagged) | Floating-point in $[0.0, 100.0]$ | $0.0 \le \texttt{physical\_progress\_pct} \le 100.0$ | Officially logged physical execution percentage |

---

## 3. Automated Validation Gates & Acceptance Invariants

During automated ingestion, the data pipeline runs four tiers of integrity tests. Failures trigger explicit validation alerts without silent modification of source data.

### Tier 1: Identity & Primary Key Gates (CRITICAL - HARD STOP)
1. **Uniqueness Gate:**
   $$\text{Duplicates}\Big(\big[\texttt{project\_code}, \, \texttt{reporting\_period}\big]\Big) \equiv 0$$
   *Action on Failure:* Ingestion rejected. Duplicate rows must be flagged for source auditing.
2. **Entity Non-Null Gate:**
   $$\sum \mathbb{I}\big(\texttt{project\_code} \text{ is null}\big) \equiv 0$$
   *Action on Failure:* Ingestion rejected.

### Tier 2: Numeric Bounds & Range Gates (CRITICAL - HARD STOP)
1. **Cost Non-Negativity:**
   $$\min\big(\texttt{original\_cost\_cr}\big) > 0.0 \quad \land \quad \min\big(\texttt{expenditure\_cr}\big) \ge 0.0$$
   *Action on Failure:* Ingestion rejected if negative costs or negative expenditures are detected.
2. **Progress Boundaries:**
   $$\forall i, \quad 0.0 \le \texttt{physical\_progress\_pct}_i \le 100.0$$
   *Action on Failure:* Ingestion rejected if values $< 0.0$ or $> 100.0$ are discovered. (Values slightly over 100.0 must be quarantined, not clipped silently).

### Tier 3: Logical Anomaly Flags (AUDIT LOG - SOFT WARNING)
These checks flag real-world administrative quirks without rejecting the entire dataset:
1. **Scope Reduction Flag:**
   $$\texttt{revised\_cost\_cr} < \texttt{original\_cost\_cr} \quad (\text{where } \texttt{revised\_cost\_cr} > 0)$$
   *Action:* Record audit log entry. (Represents genuine de-scoping or partial project revision; preserved as a feature signal).
2. **Expenditure Overrun Flag:**
   $$\texttt{expenditure\_cr} > \max\big(\texttt{revised\_cost\_cr}, \, \texttt{original\_cost\_cr}\big)$$
   *Action:* Flag as active financial budget breach; retain in dataset as high-risk indicator.
3. **Missing Revised DoC:**
   $$\texttt{revised\_doc is null}$$
   *Action:* Impute with $\texttt{original\_doc}$ and set boolean indicator $\texttt{has\_revised\_doc} = \text{False}$.

### Tier 4: Temporal Monotonicity & Continuity Invariants (PANEL LEVEL)
For projects tracked across consecutive months $t-1$ and $t$:
1. **Expenditure Monotonicity Flag:**
   $$\texttt{expenditure}(t) \ge \texttt{expenditure}(t-1) - \epsilon$$
   *Action:* If expenditure drops significantly ($\Delta \text{expenditure} < -\text{₹}1.0\text{ Cr}$), flag as an accounting reconciliation adjustment.
2. **Physical Progress Non-Reversal Flag:**
   $$\texttt{physical\_progress}(t) \ge \texttt{physical\_progress}(t-1)$$
   *Action:* If progress drops, flag as a project re-baselining or scope addition event. **Do not force monotonicity.**

---

## 4. Longitudinal Ingestion & Panel Density Requirements

To enable meaningful Point-in-Time modeling:
1. **Cadence:** All reporting periods must represent standard calendar-month closes (e.g. May 31, June 30, July 31).
2. **Minimum Historical Depth for Training:**
   - Single snapshot: **Insufficient for ML** (Descriptive audit only).
   - 2 consecutive snapshots ($t-1, t$): Minimum required to compute velocity features $\Delta \text{progress}$ and $\Delta \text{spend}$.
   - 3 consecutive snapshots ($t-1, t, t+\Delta$): Minimum required to compute 1-month velocity features at $t$ and observe a forward outcome at $t+\Delta$.

---

## 5. Current Status

```text
STATUS: SPECIFICATION READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING
```

*This ingestion contract governs all future data intake. Data files failing these invariants will be rejected prior to pipeline consumption.*

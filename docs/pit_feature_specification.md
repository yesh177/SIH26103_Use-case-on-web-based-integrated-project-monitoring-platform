# PAIMANA Point-in-Time (PIT) Feature Specification

> **Project:** SIH26103 — Use Case on Web-Based Integrated Project Monitoring Platform  
> **Product:** PAIMANA Predictive Risk Intelligence  
> **Document:** `docs/pit_feature_specification.md`  
> **Reference Inputs:** `PAIMANA_Data_Dictionary.xlsx.xlsx`, `reports/module1_data_validation.md`  
> **Status:** SPECIFICATION READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING  

---

## 1. Point-in-Time (PIT) Data Model

### 1.1 Canonical Observation Grain
The foundational observation grain for the predictive dataset is:
$$\mathbf{Unit\ of\ Observation} = \text{One Project} \times \text{One Reporting Period}$$

Every row in the training, validation, and inference datasets represents the state of a single project observed at a specific monthly reporting cutoff date.

- **Primary Entity Key:** `project_code` (Unique alphanumeric/numeric project identifier assigned by MoSPI/PAIMANA).
- **Temporal Index Key:** `reporting_period` (Standardized reporting period formatted as `YYYY-MM`, corresponding to the monthly monitoring cycle cutoff date $t$).

### 1.2 Longitudinal Snapshot Formalism
Let $t \in \mathcal{T}$ denote the **prediction snapshot cutoff date** (e.g., `2026-05-31` for the May 2026 reporting cycle).  
Let $\Delta \in \{1, 2, 3, \dots\}$ denote the **forecast horizon** in months.

$$\mathbf{x}_i(t) = \mathcal{F}\Big(\{\mathbf{z}_i(\tau) \mid \tau \le t\}\Big)$$

Where:
- $\mathbf{z}_i(\tau)$ denotes all raw monitoring signals, cost figures, milestone logs, and administrative records published on or before timestamp $\tau$.
- $\mathbf{x}_i(t)$ is the feature vector constructed strictly from information available at or before snapshot time $t$.
- $\tau > t$ designates the future horizon. **Strict Invariant:** Any data point, revision, expenditure receipt, or progress evaluation timestamped $\tau > t$ is strictly prohibited from entering $\mathbf{x}_i(t)$.

```
   Historical Data Window (Permitted)        Cutoff (t)       Future Outcome Window (Prohibited for Features)
─────────────────────────────────────────────┼──────────────────────────────────────────────────────────────►
  ...  t-2 (March)  ──►  t-1 (April)  ──►  t (May)  │  t+1 (June)  ──►  t+2 (July)  ──►  ...
                                             │
                                     PREDICTION AS-OF (t)
                                 Features: x(t) ONLY           Target: Measured at t+Δ (e.g., July)
```

---

## 2. Feature Inventory & Classification

All candidate features are cataloged below with their strict PIT evaluation, leakage profile, and designated modeling role.

> [!NOTE]
> As established in `reports/module1_data_validation.md`, fields marked as "Historical Panel Required" are defined based on the official MoSPI Table 6 schema and `PAIMANA_Data_Dictionary.xlsx.xlsx`. They are not yet present in the single-snapshot export (`Projects_Report.csv`).

### 2.1 Static & Baseline Project Attributes

| Feature Name | Data Type | Formal Definition | Source Field | Available at $t$? | PIT Safety | Leakage Risk | Transformation / Preprocessing | Modeling Role |
|---|---|---|---|---|---|---|---|---|
| `project_code` | Categorical / String | Official project identification number | `Project Code` | Yes | Safe for ID | High if fed to ML | Kept as row key; stripped from feature matrix | **Metadata / Audit Key Only** (Not a feature) |
| `project_name` | Text / String | Full official title of the infrastructure project | `Project Name` | Yes | Safe for display | High (memorization) | Kept for display/reporting; excluded from ML | **Metadata / Audit Key Only** (Not a feature) |
| `sector` | Categorical | Infrastructure sector classification (e.g., Railways, Roads, Power) | `Sector Name` | Yes | **Safe** | None (static attribute) | One-Hot / Target / Frequency Encoding | **Predictive Feature** (Domain baseline) |
| `line_ministry` | Categorical | Administrative ministry / executing department | `Line Ministry` | Yes | **Safe** | None (static attribute) | Categorical Grouping / Frequency Encoding | **Predictive Feature** (Institutional baseline) |
| `original_cost_cr` | Float64 (Numeric) | Initial government-sanctioned cost at project approval (₹ Crore) | `Original Cost` | Yes | **Safe** | None (fixed inception baseline) | Log-transform $\log(1 + x)$, robust scaling | **Predictive Feature** (Project scale) |
| `original_end_date` | Date (`YYYY-MM-DD`) | Contractual / sanctioned completion date set at approval | `Original End Date` | Yes | **Safe** | None (fixed inception baseline) | Convert to durations relative to $t$ or `start_date` | **Predictive Feature** (Schedule baseline) |
| `start_date` | Date (`YYYY-MM-DD`) | Formal date of project commencement / foundation | `Start Date` (Table 6) | Yes | **Safe** | None (historical milestone) | Convert to durations relative to $t$ | **Predictive Feature** (Temporal anchor) |

### 2.2 Dynamic Monthly Monitoring Attributes (Observed at $t$)

| Feature Name | Data Type | Formal Definition | Source Field | Available at $t$? | PIT Safety | Leakage Risk | Transformation / Preprocessing | Modeling Role |
|---|---|---|---|---|---|---|---|---|
| `reporting_period` | Date (`YYYY-MM`) | Month represented by the monitoring report cycle | `Reporting Period` | Yes | **Safe** | Low | Extracted to Year, Month, Cyclical components | **Temporal Index / Stratification Key** |
| `revised_cost_cr` | Float64 (Numeric) | Approved revised project budget as of snapshot date $t$ (₹ Crore) | `Revised Cost` | Yes (as-of $t$) | **Conditional** | **CRITICAL**: Safe only if formally approved $\le t$. Unrevised projects coded as 0 or equal to original cost. | Replace 0 with `original_cost_cr`; calculate cost delta | **Predictive Feature** (Budget adjustment state) |
| `expenditure_cr` | Float64 (Numeric) | Cumulative financial spending recorded up to cutoff date $t$ (₹ Crore) | `Expenditure` | Yes (as-of $t$) | **Safe** | Low if verified as-of $t$ | Scale relative to budget; verify non-negativity | **Predictive Feature** (Financial pace) |
| `physical_progress_pct` | Float64 (Numeric) | Officially reported physical completion percentage $[0.0, 100.0]$ | `Physical Progress` (Table 6) | Yes (as-of $t$) | **Safe** | Low if verified as-of $t$ | Standard scaling; bounds check $[0, 100]$ | **Predictive Feature** (Physical execution) |
| `revised_end_date` | Date (`YYYY-MM-DD`) | Anticipated / revised Date of Commissioning (DoC) known at $t$ | `Revised Date` | Yes (as-of $t$) | **Conditional** | **CRITICAL**: Safe only if updated $\le t$. Missing indicates project operating on original schedule. | Impute missing with `original_end_date`; calculate delays | **Predictive Feature** (Current schedule stance) |

---

## 3. Derived Point-in-Time Features

All derived features must be mathematically computed using **only** information published at or before snapshot time $t$. Under no circumstances may an observation from $t+1$ be used in these calculations.

### 3.1 Financial Ratios & Pressure Indicators

1. **Cost Growth Ratio:**
   $$\text{cost\_growth\_ratio}(t) = \frac{\max\big(\text{revised\_cost}(t), \, \text{original\_cost}\big)}{\text{original\_cost}}$$
   - *Permitted observations:* `original_cost` (inception), `revised_cost(t)`.
   - *Semantics:* Factor by which the authorized budget has grown relative to baseline. Value $= 1.0$ indicates no revision.

2. **Expenditure-to-Original-Cost Ratio (Original CUF):**
   $$\text{expenditure\_to\_original\_cost}(t) = \frac{\text{expenditure}(t)}{\text{original\_cost}}$$
   - *Permitted observations:* `original_cost` (inception), `expenditure(t)`.
   - *Semantics:* Measures financial burn relative to original sanction. Values $> 1.0$ indicate budget exhaustion.

3. **Expenditure-to-Revised-Cost Ratio (Revised CUF):**
   $$\text{expenditure\_to\_revised\_cost}(t) = \frac{\text{expenditure}(t)}{\max\big(\text{revised\_cost}(t), \, \text{original\_cost}\big)}$$
   - *Permitted observations:* Inception cost, snapshot cost, snapshot expenditure.
   - *Semantics:* True current financial utilization factor against the active working budget.

### 3.2 Schedule Timeline & Elapsed Indicators

4. **Schedule Slippage to Date (Days):**
   $$\text{schedule\_slippage\_days}(t) = \max\Big(0, \, \big(\text{revised\_end\_date}(t) - \text{original\_end\_date}\big).\text{days}\Big)$$
   - *Permitted observations:* `original_end_date`, `revised_end_date(t)`. (If unrevised, slippage $= 0$).
   - *Semantics:* Measures accumulated schedule slippage already formally acknowledged by time $t$.

5. **Project Age (Days):**
   $$\text{project\_age\_days}(t) = \big(t - \text{start\_date}\big).\text{days}$$
   - *Permitted observations:* `start_date` (inception), snapshot date $t$.
   - *Precondition:* Valid `start_date` must be present.

6. **Elapsed Duration Ratio:**
   $$\text{elapsed\_duration\_ratio}(t) = \frac{\big(t - \text{start\_date}\big).\text{days}}{\max\Big(1, \, \big(\text{original\_end\_date} - \text{start\_date}\big).\text{days}\Big)}$$
   - *Permitted observations:* `start_date`, `original_end_date`, snapshot date $t$.
   - *Semantics:* Proportion of original planned project timeline elapsed by time $t$. Values $> 1.0$ indicate project is operating past original deadline.

### 3.3 Progress & Earned Value Discrepancy Indicators

7. **Linear Progress Gap:**
   $$\text{progress\_gap}(t) = \min\big(100.0, \, \text{elapsed\_duration\_ratio}(t) \times 100.0\big) - \text{physical\_progress\_pct}(t)$$
   - *Permitted observations:* `start_date`, `original_end_date`, `physical_progress_pct(t)`.
   - *Semantics:* Discrepancy between expected linear schedule completion and actual physical progress. Positive values indicate project lagging behind timeline.

8. **Financial-to-Physical Gap (Burn Discrepancy):**
   $$\text{expenditure\_progress\_gap}(t) = \Big(\text{expenditure\_to\_revised\_cost}(t) \times 100.0\Big) - \text{physical\_progress\_pct}(t)$$
   - *Permitted observations:* Snapshot expenditure, active budget, snapshot physical progress.
   - *Semantics:* Disproportionate financial spend without commensurate physical delivery (early indicator of distress or scope mismatch).

### 3.4 Longitudinal Velocity Features (Requires Multi-Month Panel)

> [!IMPORTANT]
> The following delta features are valid **strictly and only if** both month $t$ and historical month $t-1$ are genuinely observed empirical records for that project.
> If $t-1$ is unavailable (e.g., project joined monitoring at $t$, or prior month is unobserved), these values must be treated as `NaN` with an explicit missingness indicator (`is_first_observation = True`). **Never backfill using future observations.**

9. **Recent Cost Change ($\Delta$ Cost):**
   $$\text{recent\_cost\_change}(t) = \text{revised\_cost}(t) - \text{revised\_cost}(t-1)$$
   - *Permitted observations:* $\text{revised\_cost}(t)$ and $\text{revised\_cost}(t-1)$.
   - *Constraint:* Invalid if $t-1$ is missing. Never calculate as $\text{revised\_cost}(t+1) - \text{revised\_cost}(t)$.

10. **Recent Monthly Expenditure Burn ($\Delta$ Spend):**
    $$\text{recent\_expenditure\_change}(t) = \text{expenditure}(t) - \text{expenditure}(t-1)$$
    - *Permitted observations:* $\text{expenditure}(t)$ and $\text{expenditure}(t-1)$.

11. **Recent Physical Progress Velocity ($\Delta$ Progress):**
    $$\text{recent\_progress\_change}(t) = \text{physical\_progress\_pct}(t) - \text{physical\_progress\_pct}(t-1)$$
    - *Permitted observations:* $\text{physical\_progress\_pct}(t)$ and $\text{physical\_progress\_pct}(t-1)$.
    - *Semantics:* Actual physical completion gained during the preceding month.

12. **Recent Schedule Revision ($\Delta$ Schedule Slip):**
    $$\text{recent\_schedule\_change}(t) = \big(\text{revised\_end\_date}(t) - \text{revised\_end\_date}(t-1)\big).\text{days}$$
    - *Permitted observations:* $\text{revised\_end\_date}(t)$ and $\text{revised\_end\_date}(t-1)$.
    - *Semantics:* Additional days of delay officially added during month $t$.

---

## 4. Experimental Feature Sets: Model A vs. Model B

To fulfill SIH Problem Statement SIH26103 ("Compare current CUF variables with enhanced/derived predictive features"), two distinct modeling feature sets are defined:

```
┌────────────────────────────────────────────────────────┐
│            MODEL A: OFFICIAL CUF BASELINE              │
│  - sector, line_ministry                               │
│  - original_cost_cr                                    │
│  - original_end_date                                   │
│  - revised_cost_cr                                     │
│  - expenditure_cr                                      │
│  - expenditure_to_original_cost (Raw CUF)              │
│  - physical_progress_pct                               │
└────────────────────────────────────────────────────────┘
                           vs.
┌────────────────────────────────────────────────────────┐
│         MODEL B: ENHANCED PIT PREDICTIVE SET           │
│  All Model A features, PLUS:                           │
│  - cost_growth_ratio                                   │
│  - expenditure_to_revised_cost (Adjusted CUF)          │
│  - schedule_slippage_days                              │
│  - elapsed_duration_ratio                              │
│  - progress_gap (Time vs Progress)                     │
│  - expenditure_progress_gap (Spend vs Progress)        │
│  - recent_expenditure_change (Spend Velocity)          │
│  - recent_progress_change (Physical Velocity)          │
│  - recent_schedule_change (Monthly Delay Escalation)   │
└────────────────────────────────────────────────────────┘
```

*Comparative Protocol:*
Both Model A and Model B must be evaluated on the **identical temporal train/test split** using the exact same target labels. The performance delta will formally quantify the value added by derived engineering over raw monitoring reporting.

---

## 5. Current Status

```text
STATUS: SPECIFICATION READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING
```

*This specification is structurally complete and fully verified against point-in-time constraints. Model training must not proceed until the longitudinal multi-month panel is populated.*

# Module 2A — July 2025 Table 4 Field-Level Semantic Validation Report

Generated: `2026-09-05 12:11:36`

## 1. Source and Provenance

- **Source PDF**: `data/raw/flash_reports/FlashReport_July_2025.pdf`
- **Source Table**: Table 4 — All Ongoing Projects
- **PDF Page Coverage**: Pages 37–66 inclusive (1-indexed)
- **Snapshot Period**: July 2025 (`2025-07`)
- **Extraction Methodology**: PyMuPDF raw stream text extraction with sequential serial number block boundary detection (`src/ingestion/extract_table4_july2025.py`).
- **Derived Interim File**: `data\interim\table4_july_2025_projects.csv`

## 2. Row and Identity Checks

| Check | Expected | Observed | Status |
|---|---:|---:|:---:|
| Total project rows | 791 | 791 | PASS |
| Unique project IDs | 791 | 791 | PASS |
| Duplicate project IDs | 0 | 0 | PASS |
| Serial number range | 1–791 | 1–791 | PASS |
| Missing serial numbers | 0 | 0 | PASS |
| Duplicate serial numbers | 0 | 0 | PASS |
| Source page bounds | 37–66 | 37–66 | PASS |
| Project code vs serial collision | 0 | 0 | PASS |

## 3. Canonical Field Completeness & Missing Values

Every canonical column was checked for missing or unpopulated values:

| Field Name | Type | Missing Count | Notes / Provenance |
|---|---|---:|---|
| `snapshot_date` | string | 0 | Static `"2025-07"` across all records |
| `source_page` | integer | 0 | 37–66 inclusive |
| `sl_no` | integer | 0 | 1–791 strictly sequential |
| `project_id` | string | 0 | 4–7 digit unique project code |
| `project_name` | string | 0 | Complete multi-line consolidated text |
| `agency` | string | 0 | Implementing agency / central PSU |
| `state` | string | 1 | Blank in source PDF for serial 447 |
| `approval_date` | MM/YYYY | 3 | Blank in source PDF for serials 525, 526, 648 |
| `original_completion_date` | MM/YYYY | 0 | 100% complete |
| `revised_completion_date` | MM/YYYY / `(-)` | 0 | 528 dates, 263 source `(-)` |
| `original_cost_crore` | float | 0 | 100% complete |
| `revised_cost_crore` | float | 0 | 100% complete |
| `cumulative_expenditure_crore` | float | 0 | 100% complete |
| `physical_progress_pct` | float | 0 | 100% complete |

> [!NOTE]
> In accordance with project governance rules, source-observed blanks (State for serial 447; Approval Date for serials 525, 526, 648) are left unpopulated to preserve auditability and prevent fabrication.

## 4. Date Validation

- **Approval Date**:
  - Valid `MM/YYYY`: **788** records
  - Legitimate source blanks: **3** records (Serials ['525', '526', '648'])
  - Malformed dates: **0**
- **Original Completion Date (DoC)**:
  - Valid `MM/YYYY`: **791** records (100%)
  - Malformed dates: **0**
- **Revised Completion Date (DoC)**:
  - Valid `MM/YYYY`: **528** records
  - Source-observed `(-)`: **263** records
  - Blank: **0** records
  - Malformed dates: **0**

## 5. Numeric Validation & Source Anomaly Flags

- **Negative Values**:
  - Negative original cost: **0**
  - Negative revised cost: **0**
  - Negative cumulative expenditure: **0**
- **Physical Progress Bounds**:
  - Out of range (< 0% or > 100%): **0**
  - Minimum: **0.00%**
  - Maximum: **100.00%**
  - Average: **46.88%**

### Source Anomaly Counts (Flagged, Not Modified)

| Condition | Count | Explanation |
|---|---:|---|
| Revised Cost < Original Cost | **27** | Legitimate scope/cost reduction recorded in source data |
| Revised Cost > Original Cost | **189** | Cost escalation / revision recorded in source data |
| Revised Cost == Original Cost | **575** | No revision in project estimated cost |
| Cumulative Expenditure > Revised Cost | **39** | Expenditure overrun against current sanctioned revised cost |
| Cumulative Expenditure > Original Cost | **110** | Expenditure exceeding original sanctioned cost |

## 6. Aggregate Reconciliation

Extracted dataset figures were cross-referenced against the official July 2025 Flash Report summary tables:

| Metric | Official Flash Report | Extracted Dataset | Difference | Status |
|---|---:|---:|---:|:---:|
| **Original Cost Total** | ₹ 2,386,335.28 crore *(Table 1, p.23)* | ₹ 2,386,335.28 crore | **₹ -0.00 crore** | **EXACT MATCH** |
| **Revised Cost Total** | ₹ 28,99,509 crore *(Overview, p.4)* | ₹ 2,899,508.83 crore | **₹ -0.17 crore** | **RECONCILED** (rounded) |
| **Cumulative Expenditure** | ₹ 1,510,700.05 crore *(Table 1, p.23)* | ₹ 1,510,700.40 crore | **₹ +0.35 crore** | **RECONCILED** (+0.00002%) |

> [!NOTE]
> The extracted original cost matches the Table 1 official total to two decimal places (exact ₹ 0.00 crore variance). The revised cost is within 0.17 crore of the rounded 28,99,509 crore headline figure reported on Page 4. Cumulative expenditure matches to within 0.35 crore on a 1.51 million crore total.

## 7. Field-Level Audit Results

Seven representative cases were deterministically inspected to verify multi-line handling, edge cases, and parenthetical conventions:

### 7.1 Normal Project (Serial 1, Project ID: `612786`)

- **Source Page**: Page 37
- **Project Name**: `Construction of New Domestic Terminal Building Building and miscellaneous works including maintenance, operations and AICMC at Kadapa Airport`
- **Agency**: `Airport Authority of India [AAI]`
- **State**: `Andhra Pradesh`
- **Dates**:
  - Approval: `01/2024`
  - Original DoC: `01/2026`
  - Revised DoC: `03/2026`
- **Financials**:
  - Original Cost: ₹ 265.91 crore
  - Revised Cost: ₹ 265.91 crore
  - Cumulative Expenditure: ₹ 45.54 crore
  - Physical Progress: 31.00%
- **Audit Verification**: Standard project with approval date, DoCs, matching costs, state, agency

### 7.2 Project with Revised Completion (-) (Serial 4, Project ID: `706724`)

- **Source Page**: Page 37
- **Project Name**: `Guwahati Airport New Integrated Terminal Building Construction Project`
- **Agency**: `Adani Airport Holdings Limited`
- **State**: `Assam`
- **Dates**:
  - Approval: `03/2018`
  - Original DoC: `03/2025`
  - Revised DoC: `(-)`
- **Financials**:
  - Original Cost: ₹ 1,712.00 crore
  - Revised Cost: ₹ 1,712.00 crore
  - Cumulative Expenditure: ₹ 0.00 crore
  - Physical Progress: 94.10%
- **Audit Verification**: Revised DoC explicitly recorded as source (-)

### 7.3 Project with Revised Cost Different from Original (Serial 9, Project ID: `701126`)

- **Source Page**: Page 37
- **Project Name**: `Development of Dholera International Greenfield Airport , Gujarat`
- **Agency**: `Airport Authority of India [AAI]`
- **State**: `Gujarat`
- **Dates**:
  - Approval: `07/2022`
  - Original DoC: `06/2026`
  - Revised DoC: `06/2026`
- **Financials**:
  - Original Cost: ₹ 1,305.00 crore
  - Revised Cost: ₹ 1,551.00 crore
  - Cumulative Expenditure: ₹ 666.42 crore
  - Physical Progress: 63.00%
- **Audit Verification**: Cost revision reflecting escalation or revision in official report

### 7.4 Multi-State Project (Serial 16, Project ID: `611440`)

- **Source Page**: Page 37
- **Project Name**: `Procurment of 30 Nos ACFTs of WT Capacity 10KL at Various Airports`
- **Agency**: `Airport Authority of India [AAI]`
- **State**: `Multi-States (Andhra Pradesh, Bihar, Delhi, Gujarat, Jharkhand, Karnataka, Kerala, Madhya Pradesh, Odisha, Tamil Nadu, Telangana, Uttar Pradesh, West Bengal)`
- **Dates**:
  - Approval: `05/2023`
  - Original DoC: `06/2025`
  - Revised DoC: `(-)`
- **Financials**:
  - Original Cost: ₹ 215.17 crore
  - Revised Cost: ₹ 215.17 crore
  - Cumulative Expenditure: ₹ 104.92 crore
  - Physical Progress: 53.00%
- **Audit Verification**: Multi-state project preserving complete list of involved states

### 7.5 Project Name Spanning Multiple Lines (Serial 20, Project ID: `612793`)

- **Source Page**: Page 37
- **Project Name**: `Widening of basic strip at Western Side of Runway Chainage 80m to 920m i/c slope stabilization Measures [Balance work] of uphill and Improvement of Storm Water Drainage System at Pakyong Airport, Sikkim on design & build basis [EPC] with integrated 10 years maintenance.`
- **Agency**: `Airport Authority of India [AAI]`
- **State**: `Sikkim`
- **Dates**:
  - Approval: `12/2023`
  - Original DoC: `02/2026`
  - Revised DoC: `(-)`
- **Financials**:
  - Original Cost: ₹ 323.26 crore
  - Revised Cost: ₹ 323.26 crore
  - Cumulative Expenditure: ₹ 29.69 crore
  - Physical Progress: 12.00%
- **Audit Verification**: Long multi-line title cleanly consolidated without orphan tokens

### 7.6 Source Legitimately Blank Approval Date (Serial 525, Project ID: `709812`)

- **Source Page**: Page 56
- **Project Name**: `NADIAD-PETLAD [37.26 KM]`
- **Agency**: `WR`
- **State**: `Gujarat`
- **Dates**:
  - Approval: `<BLANK IN SOURCE>`
  - Original DoC: `06/2030`
  - Revised DoC: `06/2030`
- **Financials**:
  - Original Cost: ₹ 461.91 crore
  - Revised Cost: ₹ 461.91 crore
  - Cumulative Expenditure: ₹ 75.00 crore
  - Physical Progress: 7.00%
- **Audit Verification**: Approval date column absent in source PDF; preserved without fabrication

### 7.7 Source Legitimately Blank State (Serial 447, Project ID: `706898`)

- **Source Page**: Page 53
- **Project Name**: `Khurda Road - Balangir Electrification of Railway Track Project`
- **Agency**: `CORE`
- **State**: `<BLANK IN SOURCE>`
- **Dates**:
  - Approval: `09/2019`
  - Original DoC: `03/2021`
  - Revised DoC: `(-)`
- **Financials**:
  - Original Cost: ₹ 267.61 crore
  - Revised Cost: ₹ 267.61 crore
  - Cumulative Expenditure: ₹ 0.00 crore
  - Physical Progress: 0.00%
- **Audit Verification**: State cell unpopulated in source PDF; preserved without fabrication

## 8. Lineage Architecture

```text
Official Flash Report (July 2025)
[data/raw/flash_reports/FlashReport_July_2025.pdf]
                ↓
PyMuPDF Raw Text Extraction (Pages 37–66)
[src/ingestion/extract_table4_july2025.py]
                ↓
Interim Dataset (791 Projects, 14 Canonical Columns)
[data/interim/table4_july_2025_projects.csv]
                ↓
Field-Level Semantic Validation & Aggregate Reconciliation
[src/data/validate_table4_july2025.py]
                ↓
Official Validation Report
[reports/module2a_table4_july2025_validation.md]
```

## 9. Final Status

### PASS — July 2025 Table 4 Field-Level Semantic Validation Complete

All 791 project records meet the structural integrity, data quality, semantic, and aggregate reconciliation standards required for Module 2A. No data was fabricated or silently altered.

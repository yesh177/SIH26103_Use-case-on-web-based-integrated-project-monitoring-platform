# Module 2A — July 2026 Table 6 Validation and Dataset Freeze Report

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 2A — Flash Report Ingestion, Semantic Verification & Dataset Freeze  
**Reporting Period:** July 2026 (`2026-07`)  
**Source Table:** Table 6 — All Ongoing Projects  
**Final Status:** **FROZEN — VALIDATED HISTORICAL BASELINE**  

---

## 1. Provenance & Artifact Integrity

| Artifact | File Path | File Size (Bytes) | SHA-256 Checksum |
|---|---|---|---|
| **Raw Source PDF** | `data/raw/flash_reports/FlashReport_July_2026.pdf` | 6,451,056 | `dcf52cea3b2ed6f97a49739af833f877c2afb55f61d5c43cb162f97ef6f3a9f3` |
| **Interim Extraction** | `data/interim/table6_july_2026_projects.csv` | 416,505 | `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` |
| **Frozen Processed CSV** | `data/processed/table6_july_2026_projects.csv` | 416,505 | `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` |
| **Checksum Verification** | `data/processed/table6_july_2026_projects.sha256` | 100 | Verified identical to promoted dataset |

> [!NOTE]
> **Byte-for-byte identity**: The checksum of `data/interim/table6_july_2026_projects.csv` matches `data/processed/table6_july_2026_projects.csv` exactly (`6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9`). No manual edits, transformations, or post-hoc patches were applied during promotion.

---

## 2. Extraction Defect Remediation History

During Phase 1 field-level semantic audit, two extraction heuristics in `src/ingestion/extract_table6.py` failed:
1. **Dynamic Regex State Detection**: Project descriptions containing Pink Book notations (`PB73/2023-24/NR`, `PB57/2019-20/NR`) or contract codes (`EPC/MORT&H/HRK/01/2021-22`) triggered a date regex in `cell[1]`, causing `cell[0]` (Serial No) to be mistakenly extracted as `state` across 23 projects.
2. **Approval Date Shift on Missing Value (Serial 557)**: For project `706865` (Goa), `Date of Approval` was reported as `NA` in source. Skipping `NA` caused `03/2031` (Original DoC) to be shifted into `approval_date`.

### Remediation Applied:
* Refactored `src/ingestion/extract_table6.py` to use strict positional column binding:
  * `cells[0]`: Serial Number
  * `cells[1]`: Project Name, Agency, Identifiers
  * `cells[2]`: State (enforcing non-numeric, non-empty invariants)
  * `cells[3]`: Date of Approval / Start Date
  * `cells[4]`: Original / Revised Completion Date
  * `cells[5]`: Original / Revised Cost
  * `cells[6]`: Cumulative Expenditure
  * `cells[7]`: Physical Progress
* Refactored `parse_dates_cell` to treat `NA` as empty without shifting following values.
* Added an 8-column invariant check for every row.
* Regenerated the dataset deterministically from `FlashReport_July_2026.pdf`.

---

## 3. Structural & Semantic Validation Summary

### 3.1 Structural Completeness Gates
- **Total Rows Extracted**: `1,775` (Expected: `1,775`) — **PASS**
- **Unique Project IDs**: `1,775` (0 duplicates, 0 missing) — **PASS**
- **Serial Number Continuity**: Serials `1` through `1,775` strictly continuous (0 missing) — **PASS**
- **Source Page Range**: PDF pages `55–152` inclusive (all rows strictly within bounds) — **PASS**
- **Table Schema**: 17 canonical columns match the required specification exactly — **PASS**

### 3.2 Canonical Schema (17 Fields)
1. `snapshot_date` (`2026-07`)
2. `source_page` (55–152)
3. `sl_no` (1–1775)
4. `project_id` (6–7 digit PAIMANA project code)
5. `project_name`
6. `agency`
7. `legacy_ocms_code`
8. `pmgid`
9. `state`
10. `approval_date`
11. `start_date`
12. `original_completion_date`
13. `revised_completion_date`
14. `original_cost_crore`
15. `revised_cost_crore`
16. `cumulative_expenditure_crore`
17. `physical_progress_pct`

### 3.3 State Integrity & Correction Verification
- **Numeric States Detected**: `0` across all 1,775 records — **PASS**
- **Empty States Detected**: `0` across all 1,775 records — **PASS**
- **23 Previously Afflicted Records**: All confirmed restored to official states:
  - Serials 525, 528, 529: `Andhra Pradesh`
  - Serial 532: `Assam`
  - Serials 536, 545, 546: `Bihar`
  - Serial 553: `Chhattisgarh`
  - Serial 557: `Goa`
  - Serial 570: `Haryana`
  - Serial 571: `Jharkhand`
  - Serial 583: `Karnataka`
  - Serial 606: `Maharashtra`
  - Serial 627: `Multi-States (Bihar, West Bengal)`
  - Serials 667, 668, 669: `Odisha`
  - Serials 686, 689, 691, 692: `Rajasthan`
  - Serial 702: `Uttar Pradesh`
  - Serial 1671: `Uttarakhand`

### 3.4 Date Field Integrity & Serial 557 Verification
- **Serial 557 Source Alignment**:
  - `state`: `'Goa'`
  - `approval_date`: `""` (preserved NA from source)
  - `start_date`: `'01/2022'`
  - `original_completion_date`: `'03/2031'`
  - `revised_completion_date`: `""` (unrevised, source observed `(-)`)
- **Overall Date Parsing**: All populated dates conform strictly to `MM/YYYY` format; unpopulated dates preserved as empty strings without shifting.

### 3.5 Financial & Physical Progress Validation
- **Negative Costs / Expenditures**: `0` detected across all records — **PASS**
- **Physical Progress Bounds**: All non-empty progress entries strictly within `[0.0, 100.0]` (min: `0.0%`, max: `100.0%`, mean: `59.00%`) — **PASS**
- **Source-Observed Anomalies Preserved**:
  - Projects where revised cost < original cost: **316** records (preserved raw as reported in source)
  - Projects where cumulative expenditure > revised cost: **59** records (preserved raw as reported in source)

---

## 4. Aggregate Reconciliation Against Official Table 1

Independent summation of the extracted dataset against official MoSPI **Table 1: Ministry-wise Ongoing Projects** on PDF page 24 confirms **0.00** discrepancy across all macro metrics:

| Financial Metric | Official MoSPI Table 1 Total | Frozen Dataset Total | Discrepancy | Reconciliation Status |
|---|---|---|---|---|
| **Total Projects** | `1,775` | `1,775` | `0` | **EXACT MATCH** |
| **Original Cost (Rs. Cr)** | `3,370,138.22` | `3,370,138.22` | `+0.00` | **EXACT MATCH** |
| **MoSPI Revised Cost* (Rs. Cr)** | `3,710,641.55` | `3,710,641.55` | `+0.00` | **EXACT MATCH** |
| **Cumulative Expenditure (Rs. Cr)** | `1,926,099.57` | `1,926,099.57` | `+0.00` | **EXACT MATCH** |

*Formula Note: In official MoSPI reporting, `Revised Cost*` represents Revised Cost if approved, otherwise Original Cost.*

---

## 5. Automated Regression & Semantic Audit Results

### 5.1 Unit & Regression Test Suite (`tests/test_table6_extraction.py`)
- Standard date cell parsing: **PASS**
- Dash and NA date parsing: **PASS**
- Comma and dash cost cell parsing: **PASS**
- Regression test for `PB73/2023-24/NR` (Sl 525): **PASS**
- Regression test for `PB57/2019-20/NR` (Sl 528): **PASS**
- Regression test for `EPC/MORT&H/HRK/01/2021-22` (Sl 532): **PASS**
- Regression test for NA approval date preservation (Sl 557): **PASS**
- Structural column count & numeric state invariants: **PASS**
- **Overall Suite Status**: `8 / 8 tests passed (100%)`.

### 5.2 16-Case Sample Semantic Audit (`reports/module2a_table6_july2026_field_audit.md`)
- First, second, third projects: **PASS**
- Multiline project name (Sl 897): **PASS**
- Legacy OCMS and PMG identifiers (`-`): **PASS**
- Revised completion dates populated and unrevised: **PASS**
- Cost revisions (equal, unequal, decreased): **PASS**
- Expenditure exceeding revised cost: **PASS**
- Page boundary transitions (Sl 19, Sl 4): **PASS**
- Final projects (Sl 1762, Sl 1775): **PASS**
- **Overall Audit Status**: `16 / 16 cases passed (100%)`.

---

## 6. Final Freeze Verdict

* **Status**: **FROZEN**
* **Promoted Dataset**: `data/processed/table6_july_2026_projects.csv`
* **Integrity Hash**: `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9`
* **Sign-off**: Module 2A Ingestion, Extraction, Validation, and Dataset Freeze completed and certified.


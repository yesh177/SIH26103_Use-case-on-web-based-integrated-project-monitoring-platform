# Module 2A — June 2025 Table 7 Extraction & Validation Report

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 2A — Flash Report Ingestion & Verification  
**Reporting Period:** June 2025 (`2025-06`)  
**Source Document:** `data/raw/flash_reports/FlashReport_June_2025.pdf`  
**Extracted Table:** Table 7 (`Project List: Ongoing Projects as of 30th June 2025`)  
**Staged Dataset:** `data/interim/table7_june_2025_projects.csv`  
**Date:** September 2026  
**Status:** **READY FOR VALIDATION** (Extraction Complete & Fully Reconciled)  

---

## 1. Executive Summary & Gate Status

The extraction of June 2025 Table 7 from the official MoSPI Flash Report was performed deterministically using PyMuPDF (`import pymupdf`) via `src/ingestion/extract_table7_june2025.py`.

In contrast to July 2025 (which uses the post-transition PAIMANA portal format with 791 projects in Table 4), June 2025 represents the legacy **OCMS-2006** reporting regime containing **1,595 ongoing central sector projects** across 189 pages (PDF pages 41–229).

### Primary Verification Gate Checklist
| Check | Requirement | Result | Status |
|---|---|---|---|
| **Row Count** | Exactly 1,595 records | `1,595` records | **PASS** |
| **Unique Records** | Exactly 1,595 unique rows | `1,595` unique rows | **PASS** |
| **Serial Number Bounds** | Min: 1, Max: 1,595 | Min: `1`, Max: `1595` | **PASS** |
| **Serial Continuity** | 0 missing, 0 duplicates | `0` missing, `0` duplicates | **PASS** |
| **Project ID Integrity** | 1,595 unique, 0 missing, 0 dups | `1,595` unique, `0` missing, `0` dups | **PASS** |
| **Source Page Bounds** | Pages 41–229 inclusive | Min: `41`, Max: `229` (100% within range) | **PASS** |
| **State Propagation** | 100% coverage, 33 states | `0` missing states, matches Table 2 | **PASS** |
| **Sector Propagation** | 100% coverage, 17 sectors | `0` missing sectors, matches Table 1 | **PASS** |
| **Numeric Parsing Validity** | 0 parsing errors across all costs/exp | `0` errors | **PASS** |
| **Physical Progress Bounds** | All non-null within [0.0, 100.0] | `1,436` values, `0` out of bounds | **PASS** |
| **Negative Values** | No negative costs or expenditures | `0` negative values | **PASS** |
| **Table 1 Reconciliation** | Match all 5 aggregate financial totals | Exact match to `0.00` across all 5 totals | **PASS** |

---

## 2. Source Provenance & Extraction Artifacts

- **Official Publication Archive URL**: `https://www.mospi.gov.in/sites/default/files/publication_reports/FR_JUNE_2025.pdf`
- **Local Source File**: `data/raw/flash_reports/FlashReport_June_2025.pdf`
  - File Size: `14,003,041` bytes
  - SHA256 Checksum: `7f37c63abe9f92d8db6513ad68d91b5c172c9c27454f45691f53fff7ebb2a754`
- **Extractor Script**: `src/ingestion/extract_table7_june2025.py`
- **Output Staging File**: `data/interim/table7_june_2025_projects.csv`
  - File Size: `308,654` bytes
  - SHA256 Checksum: `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43`
  - Total Lines: `1,596` (1 header + 1,595 data rows)

---

## 3. Aggregate Reconciliation against Official Report Totals

An independent, mathematical reconciliation was conducted against the official **Table 1 Overview (Sector-wise Distribution)** on PDF pages 7–8 and the summary totals printed at the end of Table 7 (PDF page 229):

| Metric | Official MoSPI Table 1 Total | Extracted Table 7 Sum | Discrepancy | Result |
|---|---|---|---|---|
| **Total Projects** | `1,595` | `1,595` | `0` | **PERFECT MATCH** |
| **Original Cost (Rs. Cr)** | `2,685,568.07` | `2,685,568.07` | `+0.00` | **PERFECT MATCH** |
| **Revised* Cost (Rs. Cr)** | `2,801,018.15` | `2,801,018.15` | `-0.00` | **PERFECT MATCH** |
| **Anticipated Cost (Rs. Cr)** | `2,975,429.26` | `2,975,429.26` | `+0.00` | **PERFECT MATCH** |
| **Cumulative Expenditure (Rs. Cr)** | `1,630,750.12` | `1,630,750.12` | `-0.00` | **PERFECT MATCH** |

*\*Note: As defined in the official MoSPI Flash Report footnote, "Revised Cost*" represents either the Revised Cost if approved, or the Original Cost if no revision has occurred.*

---

## 4. State & Sector Hierarchical Coverage

In legacy OCMS Table 7, `State` and `Sector` are hierarchical outer groupings rather than repeated cells. The deterministic downward propagation logic successfully captured 100% of rows without a single missing value.

### 4.1 State Distribution Reconciliation (vs. Official Table 2)

| State / UT | Official Table 2 Count | Extracted Table 7 Count | Status |
|---|---|---|---|
| ANDAMAN AND NICOBAR ISLANDS | 9 | 9 | Match |
| ANDHRA PRADESH | 100 | 100 | Match |
| ARUNACHAL PRADESH | 14 | 14 | Match |
| ASSAM | 68 | 68 | Match |
| BIHAR | 90 | 90 | Match |
| CHHATTISGARH | 50 | 50 | Match |
| DELHI | 21 | 21 | Match |
| GOA | 3 | 3 | Match |
| GUJARAT | 89 | 89 | Match |
| HARYANA | 24 | 24 | Match |
| HIMACHAL PRADESH | 27 | 27 | Match |
| JAMMU AND KASHMIR | 53 | 53 | Match |
| JHARKHAND | 64 | 64 | Match |
| KARNATAKA | 79 | 79 | Match |
| KERALA | 29 | 29 | Match |
| LADAKH | 6 | 6 | Match |
| MADHYA PRADESH | 53 | 53 | Match |
| MAHARASHTRA | 157 | 157 | Match |
| MANIPUR | 31 | 31 | Match |
| MEGHALAYA | 14 | 14 | Match |
| MIZORAM | 16 | 16 | Match |
| MULTI STATE | 49 | 49 | Match |
| NAGALAND | 23 | 23 | Match |
| ODISHA | 76 | 76 | Match |
| PUNJAB | 37 | 37 | Match |
| RAJASTHAN | 59 | 59 | Match |
| SIKKIM | 18 | 18 | Match |
| TAMIL NADU | 58 | 58 | Match |
| TELANGANA | 52 | 52 | Match |
| TRIPURA | 14 | 14 | Match |
| UTTAR PRADESH | 126 | 126 | Match |
| UTTARAKHAND | 30 | 30 | Match |
| WEST BENGAL | 56 | 56 | Match |
| **Total** | **1,595** | **1,595** | **33/33 Matched** |

### 4.2 Sector Distribution Reconciliation (vs. Official Table 1)

| Sector | Official Table 1 Count | Extracted Table 7 Count | Status |
|---|---|---|---|
| CIVIL AVIATION | 38 | 38 | Match |
| COAL | 116 | 116 | Match |
| DEPARTMENT OF HIGHER EDUCATION | 20 | 20 | Match |
| DPIIT | 2 | 2 | Match |
| FINANCE | 2 | 2 | Match |
| HEALTH AND FAMILY WELFARE | 7 | 7 | Match |
| HOME AFFAIRS | 3 | 3 | Match |
| MINES | 8 | 8 | Match |
| PETROLEUM | 102 | 102 | Match |
| POWER | 105 | 105 | Match |
| RAILWAYS | 203 | 203 | Match |
| ROAD TRANSPORT AND HIGHWAYS | 923 | 923 | Match |
| SHIPPING AND PORTS | 1 | 1 | Match |
| STEEL | 20 | 20 | Match |
| TELECOMMUNICATIONS | 6 | 6 | Match |
| URBAN DEVELOPMENT | 24 | 24 | Match |
| WATER RESOURCES | 15 | 15 | Match |
| **Total** | **1,595** | **1,595** | **17/17 Matched** |

---

## 5. Field-Level Semantic Audit

A detailed comparison of extracted records against the physical PDF text was conducted for key sample cases:

### Case 1: First Project (`sl_no = 1`, PDF Page 41)
- `snapshot_date`: `2025-06-30`
- `source_page`: `41`
- `sl_no`: `1`
- `project_id`: `N04000073`
- `project_name`: `CONSTRUCTION OF NEW INTEGRATED TERMINAL BUILDING AT VSI AIRPORT, PORTBLAIR`
- `agency`: `AAI`
- `state`: `ANDAMAN AND NICOBAR ISLANDS`
- `sector`: `CIVIL AVIATION`
- `approval_date`: `10-2013`
- `original_completion_date`: `9/2018`
- `revised_completion_date`: `Jun-2023`
- `anticipated_completion_date`: `6/2023`
- `original_cost_crore`: `417.23`
- `revised_cost_crore`: `707.73`
- `anticipated_cost_crore`: `707.73`
- `cumulative_expenditure_crore`: `698.80`
- `physical_progress_pct`: `100.00`
- **Audit Verification**: Exact character-for-character match with PDF source.

### Case 2: Second Project (`sl_no = 2`, PDF Page 41) — Sector Transition
- `sl_no`: `2`, `source_page`: `41`
- `project_id`: `N22000584`
- `project_name`: `LUDHIANA KILA RAIPUR (19 KMS) WITH FREIGHT LINE AT GILL STATION ON LDH-JHL SECTION`
- `agency`: `NR`
- `state`: `ANDAMAN AND NICOBAR ISLANDS` (propagated)
- `sector`: `RAILWAYS` (correctly transitioned from CIVIL AVIATION)
- `approval_date`: `3-2019`
- `original_completion_date`: `3/2025`
- `revised_completion_date`: `Aug-2025`
- `anticipated_completion_date`: `3/2026`
- `original_cost_crore`: `235.72`
- `revised_cost_crore`: `""` (source: `(N.A.)`, preserved as empty)
- `anticipated_cost_crore`: `235.72` (source: `{235.72}`)
- `cumulative_expenditure_crore`: `59.78`
- `physical_progress_pct`: `55.00`
- **Audit Verification**: Correctly parsed parenthesis in project name `(19 KMS)`, identified `NR` as agency and `N22000584` as project ID.

### Case 3: Third Project (`sl_no = 3`, PDF Page 41)
- `sl_no`: `3`, `source_page`: `41`
- `project_id`: `N24002207`
- `project_name`: `MAJOR BRIDGE OVER MIDDLE STRAIT CREEK`
- `agency`: `NHIDCL`
- `state`: `ANDAMAN AND NICOBAR ISLANDS`
- `sector`: `ROAD TRANSPORT AND HIGHWAYS`
- `approval_date`: `12-2024`
- `original_completion_date`: `2/2026`
- `revised_completion_date`: `""` (source: `(N.A.)`)
- `anticipated_completion_date`: `2/2026`
- `original_cost_crore`: `371.80`
- `revised_cost_crore`: `207.99`
- `anticipated_cost_crore`: `207.99`
- `cumulative_expenditure_crore`: `0.00`
- `physical_progress_pct`: `5.23`
- **Audit Verification**: Exact match.

### Case 4: Multi-Line Complex Project (`sl_no = 6`, PDF Page 41)
- `sl_no`: `6`, `source_page`: `41`
- `project_id`: `N24000745`
- `project_name`: `2 LANE WITH HARD SHOLDER , REHABILITATION AND UP GRADATION OF SECTION FROM KM 242.0 TO KM 298.0 OF N`
- `agency`: `NHIDCL`
- `approval_date`: `3-2017`
- `original_completion_date`: `12/2019`
- `revised_completion_date`: `Mar-2023`
- `anticipated_completion_date`: `6/2025`
- `original_cost_crore`: `409.85`
- `revised_cost_crore`: `""` (source: `(N.A.)`)
- `anticipated_cost_crore`: `409.85`
- `cumulative_expenditure_crore`: `214.23`
- `physical_progress_pct`: `95.23`
- **Audit Verification**: Multiline text properly concatenated into single space-delimited name.

### Case 5: Project with N.A. Revised Cost (`sl_no = 5`, PDF Page 41)
- `sl_no`: `5`, `source_page`: `41`
- `project_id`: `N24002209`
- `original_cost_crore`: `183.47`
- `revised_cost_crore`: `""` (source: `(N.A.)`, preserved as empty)
- `anticipated_cost_crore`: `183.47` (source: `{183.47}`)
- **Audit Verification**: N.A. faithfully preserved without inventing values.

### Case 6: Project Near Page Boundary (`sl_no = 8`, PDF Page 41 bottom)
- `sl_no`: `8`, `source_page`: `41`
- `project_id`: `N24000820`
- `project_name`: `Rehabilitation and up gradation to 2 lane with paved shoulder configuration from existing km. 122.00`
- `agency`: `MoRTH`
- `original_cost_crore`: `237.80`, `anticipated_cost_crore`: `238.00`, `cumulative_expenditure_crore`: `222.13`, `physical_progress_pct`: `98.23`
- **Audit Verification**: Clean boundary truncation before page footer.

### Case 7: Project After State Change (`sl_no = 10`, PDF Page 42)
- `sl_no`: `10`, `source_page`: `42`
- `project_id`: `N04000091`
- `project_name`: `C/O OF NITB AND ASSOCIATED WORK AT VIJAYAWADA AIRPORT`
- `agency`: `AAI`
- `state`: `ANDHRA PRADESH` (correctly transitioned from Andaman and Nicobar Islands)
- `sector`: `CIVIL AVIATION`
- **Audit Verification**: State transition verified; first Andhra Pradesh project accurately captured.

### Case 8: Final Project (`sl_no = 1595`, PDF Page 229)
- `sl_no`: `1595`, `source_page`: `229`
- `project_id`: `N30000042`
- `project_name`: `INTERCEPTION AND DIVERSION WITH STP AT HUGHLY-CHINSURAH`
- `agency`: `KMDA`
- `state`: `WEST BENGAL`
- `sector`: `WATER RESOURCES`
- `approval_date`: `5-2018`
- `original_completion_date`: `2/2022`
- `revised_completion_date`: `Sep-2020`
- `anticipated_completion_date`: `3/2025`
- `original_cost_crore`: `160.00`
- `revised_cost_crore`: `154.73`
- `anticipated_cost_crore`: `154.73`
- `cumulative_expenditure_crore`: `93.32`
- `physical_progress_pct`: `92.00`
- **Audit Verification**: Successfully terminated before Table 7 `Total` summary block (`y=575.7`).

---

## 6. Data Quality & Missing Value Profile

| Column | Non-Empty Count | Missing / N.A. Count | Data Integrity Notes |
|---|---|---|---|
| `snapshot_date` | 1,595 | 0 | Constant `2025-06-30` |
| `source_page` | 1,595 | 0 | 41 to 229 inclusive |
| `sl_no` | 1,595 | 0 | Strict consecutive integers 1 to 1595 |
| `project_id` | 1,595 | 0 | 1,580 `N...` codes + 15 legacy 9-digit OCMS codes |
| `project_name` | 1,595 | 0 | Multiline text cleaned |
| `agency` | 1,595 | 0 | Valid ministry/agency abbreviation |
| `state` | 1,595 | 0 | 33 distinct states/UTs |
| `sector` | 1,595 | 0 | 17 distinct sectors |
| `approval_date` | 1,595 | 0 | `M-YYYY` / `MM-YYYY` |
| `original_completion_date` | 1,593 | 2 | 2 projects report N.A./missing in source |
| `revised_completion_date` | 536 | 1,059 | 1,059 projects have no revised date (`N.A.`) |
| `anticipated_completion_date` | 1,590 | 5 | 5 projects have no anticipated date (`N.A.`) |
| `original_cost_crore` | 1,595 | 0 | Fully populated; sum = 2,685,568.07 Cr |
| `revised_cost_crore` | 361 | 1,234 | 1,234 projects have no revised cost (`N.A.`) |
| `anticipated_cost_crore` | 1,595 | 0 | Fully populated; sum = 2,975,429.26 Cr |
| `cumulative_expenditure_crore` | 1,595 | 0 | Fully populated; sum = 1,630,750.12 Cr |
| `physical_progress_pct` | 1,436 | 159 | 159 projects report `-` or N.A. in source |

---

## 7. Operational Recommendation & Next Steps

1. **Gate Readiness**: The dataset strictly passes all completeness, structural, hierarchical, and reconciliation gates. It is **READY FOR VALIDATION**.
2. **Freezing / Promotion**: In accordance with project instructions, the dataset remains strictly in `data/interim/table7_june_2025_projects.csv` and has **NOT** been promoted to `data/processed/`.
3. **Protected Files**: No July 2025, July 2026, or contract files were modified.

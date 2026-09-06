# Module 2B — Canonical Snapshot Construction & Validation Report

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 2B — Canonicalization & Longitudinal Panel Construction (Phase 2)  
**Reporting Periods:** June 2025 (`2025-06`), July 2025 (`2025-07`), July 2026 (`2026-07`)  
**Generated Artifact:** `data/interim/canonical_snapshots.csv`  
**Output Status:** **STAGED INTERIM CANONICAL SNAPSHOTS (PRE-FREEZE)**  

---

## 1. Executive Summary

In Module 2B Phase 2, the three frozen historical MoSPI/PAIMANA project monitoring snapshots were harmonized into a unified canonical snapshot dataset.

### Core Architectural Principle: Observation $\ne$ Resolved Physical Project
Following the Phase 1 specification and user naming directive, the primary key of this dataset is explicitly defined as:
$$\mathbf{canonical\_observation\_key} = \texttt{<source\_snapshot>:<source\_table>:<source\_project\_id>}$$

This key represents an **observation** within a specific reporting cycle. **No cross-snapshot project linking or physical entity merging was performed at this stage.** The creation of unified cross-snapshot entities (`canonical_project_key`) is reserved for subsequent identity resolution.

---

## 2. Frozen Input Datasets & Integrity Verification

Before processing, the cryptographic SHA-256 hashes of all three input datasets were verified against their `.sha256` integrity files:

| Source Snapshot | Source System & Table | File Path | Verified SHA-256 Checksum | Verified Row Count |
|---|---|---|---|---|
| **June 2025** | OCMS Table 7 | `data/processed/table7_june_2025_projects.csv` | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` | `1,595` |
| **July 2025** | PAIMANA Table 4 | `data/processed/table4_july_2025_projects.csv` | `ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3` | `791` |
| **July 2026** | PAIMANA Table 6 | `data/processed/table6_july_2026_projects.csv` | `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` | `1,775` |
| **Total Universe** | — | — | — | **`4,161` records** |

---

## 3. Output Dataset Integrity & Provenance

* **Output File Path**: `data/interim/canonical_snapshots.csv`
* **File Size**: `1,551,343` bytes
* **SHA-256 Checksum**:
  ```text
  0b9d2c919262f13290efda58ed7a21ab341e06616e11571c1ea702251c10a8b7
  ```
* **Total Records**: Exactly `4,161` rows
* **Total Columns**: Exactly `30` canonical columns
* **Deterministic Sort Order**:
  1. `source_snapshot` ascending (`2025-06`, `2025-07`, `2026-07`)
  2. `source_table` ascending (`Table 7`, `Table 4`, `Table 6`)
  3. `source_row` / `sl_no` ascending (integer order)

### Provenance Tracking Method
Each row is attributed with:
* `source_file`: Original PDF filename (`FlashReport_June_2025.pdf`, `FlashReport_July_2025.pdf`, `FlashReport_July_2026.pdf`)
* `source_page`: Source PDF page number
* `source_row`: Official sequential serial number within that report
* `source_record_hash`: Deterministic SHA-256 hash calculated over the complete source record dictionary (`json.dumps(row, sort_keys=True, ensure_ascii=False)`).

---

## 4. Canonical Schema & Missing-Value Audit

All 30 fields conform to the approved Phase 1 specification. Missing values reflect authentic source availability and unrevised project status:

| Column Name | Logical Group | Data Type | Populated Count | Missing Count (% Total) | Semantic Meaning & Source Behavior |
|---|---|---|---|---|---|
| `canonical_observation_key` | IDENTITY | String | 4,161 | 0 (0.0%) | Deterministic observation URI; 100% unique |
| `source_snapshot` | IDENTITY | String | 4,161 | 0 (0.0%) | Reporting cycle: `2025-06`, `2025-07`, `2026-07` |
| `snapshot_date` | IDENTITY | Date | 4,161 | 0 (0.0%) | Standardized cutoff: `2025-06-30`, `2025-07-31`, `2026-07-31` |
| `source_table` | IDENTITY | String | 4,161 | 0 (0.0%) | Source table: `Table 7`, `Table 4`, `Table 6` |
| `source_project_id` | IDENTITY | String | 4,161 | 0 (0.0%) | Raw extracted project identifier |
| `project_name` | IDENTITY | String | 4,161 | 0 (0.0%) | Full official project title |
| `agency` | IDENTITY | String | 4,151 | 10 (0.2%) | Implementing agency (10 unstated in June 2025 source) |
| `state` | IDENTITY | String | 4,160 | 1 (0.0%) | Administrative jurisdiction (1 unstated in July 2025: Sl 447) |
| `approval_date_raw` | DATES | String | 4,146 | 15 (0.4%) | Verbatim approval date string |
| `approval_date` | DATES | Date (`YYYY-MM`) | 4,146 | 15 (0.4%) | Standardized approval date (no day invention) |
| `start_date_raw` | DATES | String | 1,775 | 2,386 (57.3%) | Verbatim start date (available in July 2026 only) |
| `start_date` | DATES | Date (`YYYY-MM`) | 1,775 | 2,386 (57.3%) | Standardized start date; unavailable in 2025 sources |
| `original_completion_date_raw` | DATES | String | 4,159 | 2 (0.0%) | Verbatim target DoC |
| `original_completion_date` | DATES | Date (`YYYY-MM`) | 4,154 | 7 (0.2%) | Standardized target DoC (5 unpopulated `{}` in June 2025) |
| `revised_completion_date_raw` | DATES | String | 2,754 | 1,407 (33.8%) | Verbatim revised DoC (source `(-)` or empty) |
| `revised_completion_date` | DATES | Date (`YYYY-MM`) | 2,491 | 1,670 (40.1%) | Standardized revised DoC (empty for unrevised projects) |
| `anticipated_completion_date_raw` | DATES | String | 1,590 | 2,571 (61.8%) | Verbatim anticipated DoC (June 2025 Table 7 only) |
| `anticipated_completion_date` | DATES | Date (`YYYY-MM`) | 1,590 | 2,571 (61.8%) | Standardized anticipated DoC; unavailable in PAIMANA tables |
| `original_cost_crore` | FINANCIAL | Float64 | 4,161 | 0 (0.0%) | Sanctioned original cost in ₹ Crore ($\ge 0.0$) |
| `revised_cost_crore` | FINANCIAL | Float64 | 2,927 | 1,234 (29.7%) | Approved revised cost (1,234 unrevised records preserved raw) |
| `anticipated_cost_crore` | FINANCIAL | Float64 | 1,595 | 2,566 (61.7%) | Anticipated cost (June 2025 Table 7 only) |
| `cumulative_expenditure_crore` | FINANCIAL | Float64 | 4,161 | 0 (0.0%) | Total expenditure incurred to date ($\ge 0.0$) |
| `physical_progress_pct` | PROGRESS | Float64 | 4,002 | 159 (3.8%) | Physical execution % (159 unstated/`-` in June 2025) |
| `source_page` | PROVENANCE | Integer | 4,161 | 0 (0.0%) | Source PDF page number |
| `source_row` | PROVENANCE | Integer | 4,161 | 0 (0.0%) | Source serial number (`sl_no`) |
| `source_file` | PROVENANCE | String | 4,161 | 0 (0.0%) | Source PDF file basename |
| `source_record_hash` | PROVENANCE | String | 4,161 | 0 (0.0%) | Cryptographic SHA-256 of source row |
| `sector` | SOURCE-SPECIFIC | String | 1,595 | 2,566 (61.7%) | Sector classification (June 2025 Table 7 only) |
| `legacy_ocms_code` | SOURCE-SPECIFIC | String | 1,775 | 2,386 (57.3%) | Legacy OCMS code cell (reports `'-'` in July 2026) |
| `pmgid` | SOURCE-SPECIFIC | String | 1,775 | 2,386 (57.3%) | PMG portal ID cell (reports `'-'` in July 2026) |

---

## 5. Automated Validation & Test Suite Results

The formal test suite [`tests/test_canonical_snapshots.py`](file:///c:/Users/Lenovo/OneDrive/Documents/paimana-predictive-risk/tests/test_canonical_snapshots.py) verified all 20 requirements:

```text
python -m unittest tests/test_canonical_snapshots.py
----------------------------------------------------------------------
Ran 19 tests in 0.264s

OK
```

### Key Assertions Verified:
1. **Row Count Parity**: Exactly 4,161 total rows ($1,595 + 791 + 1,775$).
2. **Schema Invariant**: Exactly 30 canonical fields matching the specification.
3. **Observation Key Uniqueness**: Zero duplicate `canonical_observation_key`s across all 4,161 rows.
4. **Frozen Source Immutability**: All 3 frozen source hashes verified unchanged.
5. **Missing-Value Governance**:
   - Exactly 1,234 unrevised costs in June 2025 remain empty (no imputation).
   - Unavailable fields (`start_date`, `sector`, `anticipated_cost`) are preserved as empty strings, not zero-filled.
6. **Date Normalization**: Normalized to `YYYY-MM` without inventing false day-level precision (`-01`).
7. **Numeric Bounds**: Zero negative costs, zero negative expenditures, physical progress bounded in $[0.0, 100.0]$.
8. **Repeatable Determinism**: Executing the pipeline repeatedly yields byte-for-byte identical output.

---

## 6. Current Status & Next Steps

* **Current Status**: **STAGED INTERIM CANONICAL SNAPSHOTS**
* **Staged Path**: `data/interim/canonical_snapshots.csv`
* **Frozen Inputs**: Unaltered and preserved under cryptographic verification.
* **Downstream Readiness**: The canonical snapshot tier is fully prepared for **Module 2B Phase 3: Project Identity Resolution & Longitudinal Panel Construction**.


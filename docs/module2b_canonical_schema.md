# Module 2B — Canonical Snapshot Schema & Harmonization Specification

> **Project:** SIH26103 — Use Case on Web-Based Integrated Project Monitoring Platform  
> **Product:** PAIMANA Predictive Risk Intelligence  
> **Document:** `docs/module2b_canonical_schema.md`  
> **Module:** 2B — Canonicalization & Longitudinal Panel Construction  
> **Phase:** Phase 1 — Specification Only  
> **Status:** ACTIVE SPECIFICATION — NO MANUAL OR PREMATURE EXECUTION  

---

## 1. Executive Overview & Objectives

Module 2B establishes the formal, deterministic data harmonization layer for the PAIMANA Predictive Risk Intelligence system. It unifies three independently verified and frozen historical project monitoring snapshots published by the Ministry of Statistics and Programme Implementation (MoSPI):

1. **June 2025 Table 7** (`table7_june_2025_projects.csv`): Legacy Online Computerized Monitoring System (**OCMS-2006**) snapshot (1,595 ongoing projects).
2. **July 2025 Table 4** (`table4_july_2025_projects.csv`): Initial operational snapshot from the web-based **PAIMANA** platform (791 ongoing projects).
3. **July 2026 Table 6** (`table6_july_2026_projects.csv`): Full post-transition **PAIMANA** platform snapshot (1,775 ongoing projects).

### Primary Objective
Create an auditable, lossless canonical snapshot schema that integrates heterogeneous source formats across the OCMS $\rightarrow$ PAIMANA platform transition without discarding source-specific attributes, without fabricating synthetic observations, and without corrupting missing-value semantics.

### Downstream Consumer
This canonical snapshot schema serves as the foundation for **Module 2C (Point-in-Time Feature Engineering & Target Construction)** for the Smart India Hackathon (SIH) predictive risk intelligence prototype.

---

## 2. Frozen Source Inventory & Provenance Invariants

The three input datasets are strictly frozen in `data/processed/` under immutable SHA-256 cryptographic verification. Any modification, re-extraction, or in-place alteration of these files is strictly prohibited.

| Snapshot Dataset | Reporting Period | Source System & Table | Raw Source Document & SHA-256 | Processed File Path & SHA-256 | Verified Rows |
|---|---|---|---|---|---|
| **June 2025** | `2025-06-30` | OCMS Table 7 (Ongoing Projects) | `FlashReport_June_2025.pdf`<br>`7f37c63abe9f92d8db6513ad68d91b5c172c9c27454f45691f53fff7ebb2a754` | `data/processed/table7_june_2025_projects.csv`<br>`9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` | `1,595` |
| **July 2025** | `2025-07-31` | PAIMANA Table 4 (Ongoing Projects) | `FlashReport_July_2025.pdf`<br>`1064c963c8afacf903ad9cc876fa3615c4b4b28ccdae920a8ff392af37111508` | `data/processed/table4_july_2025_projects.csv`<br>`ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3` | `791` |
| **July 2026** | `2026-07-31` | PAIMANA Table 6 (Ongoing Projects) | `FlashReport_July_2026.pdf`<br>`dcf52cea3b2ed6f97a49739af833f877c2afb55f61d5c43cb162f97ef6f3a9f3` | `data/processed/table6_july_2026_projects.csv`<br>`6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` | `1,775` |
| **Total Universe** | — | — | — | — | **`4,161` records** |

---

## 3. Canonical Snapshot Schema Specification

The canonical record represents **one project observed at one snapshot cutoff date**. The composite natural primary key for the canonical staging table is:

$$\mathbf{Canonical\ Primary\ Key} = \big(\texttt{source\_snapshot}, \, \texttt{source\_table}, \, \texttt{source\_project\_id}\big)$$

Synthesized as a deterministic URI-style string:
$$\texttt{canonical\_project\_key} = \texttt{<source\_snapshot>:<source\_table>:<source\_project\_id>}$$

### 3.1 Schema Field Inventory & Classification

Every canonical field is explicitly classified into one of four lifecycle states:
1. **Directly Observed**: Extracted verbatim from source without semantic alteration (whitespace trimmed).
2. **Normalized**: Standardized into ISO-8601 calendar format (`YYYY-MM-DD` or `YYYY-MM`), uppercase casing, or standard numeric floats.
3. **Unavailable in Source**: The field does not exist in that source report's physical table layout; populated strictly as `None`/empty, never imputed.
4. **Derived Later**: Point-in-time calculation engineered in downstream Module 2C (e.g. slippage months, cost growth ratio).

| Field Name | Logical Group | Physical Type | Nullable? | Field Status | Business Definition & Standard Value Domain |
|---|---|---|---|---|---|
| `canonical_project_key` | **IDENTITY** | String | **NO** | Normalized | Deterministic unique observation key: `<source_snapshot>:<source_table>:<source_project_id>` |
| `source_snapshot` | **IDENTITY** | String | **NO** | Normalized | Reporting cycle identifier: `2025-06`, `2025-07`, `2026-07` |
| `snapshot_date` | **IDENTITY** | Date / String | **NO** | Normalized | Exact monthly cutoff date: `2025-06-30`, `2025-07-31`, `2026-07-31` |
| `source_table` | **IDENTITY** | String | **NO** | Directly Observed | Source table identifier: `Table 7`, `Table 4`, `Table 6` |
| `source_project_id` | **IDENTITY** | String | **NO** | Directly Observed | Raw project code (e.g. `N04000073`, `220100265`, `612786`) |
| `project_name` | **IDENTITY** | String | **NO** | Directly Observed | Cleaned full official project title |
| `agency` | **IDENTITY** | String | YES | Directly Observed | Central Public Sector Enterprise, executing agency, or railway zone |
| `state` | **IDENTITY** | String | YES | Directly Observed | State / UT / Multi-State jurisdiction |
| `approval_date_raw` | **DATES** | String | YES | Directly Observed | Verbatim approval date string as extracted from source |
| `approval_date` | **DATES** | Date / String | YES | Normalized | Standardized approval date (`YYYY-MM` or `YYYY-MM-01`) |
| `start_date_raw` | **DATES** | String | YES | Directly Observed | Verbatim start date string (available in July 2026; unavailable in June 2025, July 2025) |
| `start_date` | **DATES** | Date / String | YES | Normalized | Standardized start date (`YYYY-MM` or `YYYY-MM-01`) |
| `original_completion_date_raw` | **DATES** | String | YES | Directly Observed | Verbatim original target Date of Commissioning (DoC) |
| `original_completion_date` | **DATES** | Date / String | YES | Normalized | Standardized original target DoC (`YYYY-MM` or `YYYY-MM-01`) |
| `revised_completion_date_raw` | **DATES** | String | YES | Directly Observed | Verbatim revised DoC string (empty if unrevised / `(-)`) |
| `revised_completion_date` | **DATES** | Date / String | YES | Normalized | Standardized latest revised DoC (`YYYY-MM` or `YYYY-MM-01` / empty if unrevised) |
| `anticipated_completion_date_raw` | **DATES** | String | YES | Directly Observed | Verbatim anticipated DoC (available in June 2025; unavailable in July 2025, July 2026) |
| `anticipated_completion_date` | **DATES** | Date / String | YES | Normalized | Standardized anticipated DoC (`YYYY-MM` or `YYYY-MM-01`) |
| `original_cost_crore` | **FINANCIAL** | Float64 | **NO** | Normalized | Sanctioned initial project cost in ₹ Crore ($\ge 0.0$) |
| `revised_cost_crore` | **FINANCIAL** | Float64 | YES | Normalized | Sanctioned revised cost in ₹ Crore (empty if unrevised; NEVER imputed) |
| `anticipated_cost_crore` | **FINANCIAL** | Float64 | YES | Normalized | Anticipated completion cost in ₹ Crore (June 2025 Table 7 only) |
| `cumulative_expenditure_crore` | **FINANCIAL** | Float64 | YES | Normalized | Cumulative expenditure incurred to snapshot date in ₹ Crore ($\ge 0.0$) |
| `physical_progress_pct` | **PROGRESS** | Float64 | YES | Normalized | Officially evaluated physical execution percentage ($0.0 \le x \le 100.0$) |
| `source_page` | **PROVENANCE** | Integer | **NO** | Directly Observed | Source PDF 1-indexed page number |
| `source_row` | **PROVENANCE** | Integer | **NO** | Directly Observed | Official sequential serial number (`sl_no`) within the source table |
| `source_file` | **PROVENANCE** | String | **NO** | Directly Observed | Local raw PDF source filename |
| `source_record_hash` | **PROVENANCE** | String | **NO** | Normalized | Cryptographic SHA-256 hash of the complete raw row string |
| `sector` | **SOURCE-SPECIFIC**| String | YES | Directly Observed | Infrastructure sector (June 2025 Table 7 only; empty for July 2025, July 2026) |
| `legacy_ocms_code` | **SOURCE-SPECIFIC**| String | YES | Directly Observed | Legacy OCMS code cell string (July 2026 Table 6 only; reports `(-)` across source) |
| `pmgid` | **SOURCE-SPECIFIC**| String | YES | Directly Observed | PMG portal tracking ID (July 2026 Table 6 only; reports `(-)` across source) |

---

## 4. Strict Missing-Value Semantics & Invariants

To prevent data pollution and feature distortion during machine learning, missing values must be strictly distinguished across semantic types:

### 4.1 Missing Value Taxonomy

```
                           ┌────────────────────────────────────────────────────────┐
                           │               MISSING VALUE TAXONOMY                   │
                           └──────────────────────────┬─────────────────────────────┘
                                                      │
         ┌────────────────────────────────────────────┼────────────────────────────────────────┐
         │                                            │                                        │
         ▼                                            ▼                                        ▼
┌──────────────────┐                       ┌─────────────────────┐                  ┌────────────────────┐
│ 1. UNAVAILABLE   │                       │ 2. UNREVISED        │                  │ 3. GENUINELY       │
│    IN SOURCE     │                       │    COMMITTED VALUE  │                  │    MISSING         │
├──────────────────┤                       ├─────────────────────┤                  ├────────────────────┤
│ Field was not in │                       │ Field exists, but   │                  │ Field exists, but  │
│ source table     │                       │ project operates on │                  │ source omits data  │
│ schema.          │                       │ original sanction.  │                  │ (e.g. blank state) │
│ Representation:  │                       │ Representation:     │                  │ Representation:    │
│ None / empty     │                       │ None / empty        │                  │ None / empty       │
└──────────────────┘                       └─────────────────────┘                  └────────────────────┘
```

1. **Unavailable in Source (`UNAVAILABLE`)**:
   - *Definition:* The source PDF table layout does not contain this attribute.
   - *Examples:* `start_date` is not in June 2025 or July 2025. `sector` is not in July 2025 or July 2026. `anticipated_cost_crore` is not in July 2025 or July 2026.
   - *Rule:* Retain as `None`/empty string. **NEVER populate with zero, fallback placeholders, or synthetic defaults.**
2. **Unrevised / Uncommitted Value (`UNREVISED`)**:
   - *Definition:* The project has no approved cost revision or has not postponed its target Date of Commissioning.
   - *Source Representations:* Printed as `(-)` in PAIMANA revised completion date; left unpopulated (`N.A.` / empty) in OCMS revised cost.
   - *Rule:* Retain as `None`/empty string in canonical storage.
   - **CRITICAL DATA GOVERNANCE RULE:** **NEVER overwrite missing `revised_cost_crore` with `original_cost_crore` in the canonical snapshot.** The official MoSPI concept $\text{Revised Cost}^* = \text{if approved then Revised Cost else Original Cost}$ is a downstream derived reporting metric and must be computed explicitly during feature engineering, not by corrupting the raw observation.
3. **Genuinely Missing Source Value (`GENUINELY_MISSING`)**:
   - *Definition:* The physical column exists, but the source reports no value (e.g. Serial 447 in July 2025 where State is blank; Serials 525, 526, 648 in July 2025 where Approval Date is unstated; Serial 557 in July 2026 where Approval Date is reported as `NA`).
   - *Rule:* Store as `None`/empty string. Preserve exactly as observed.

---

## 5. Source-to-Canonical Harmonization Mapping

### 5.1 June 2025 Table 7 Crosswalk (OCMS Format — 1,595 Records)

| Source Column (`table7_june_2025_projects.csv`) | Canonical Column | Physical Transformation | Missing-Value Behavior |
|---|---|---|---|
| `snapshot_date` (`2025-06-30`) | `snapshot_date` | Trim whitespace $\rightarrow$ ISO `2025-06-30` | Invariant (Never missing) |
| *Constant* | `source_snapshot` | Assign `'2025-06'` | Invariant |
| *Constant* | `source_table` | Assign `'Table 7'` | Invariant |
| `project_id` | `source_project_id` | Trim whitespace (e.g. `N04000073`, `220100265`) | Invariant (1,595 unique) |
| *Calculated* | `canonical_project_key` | `'2025-06:Table 7:' + source_project_id` | Invariant (1,595 unique) |
| `project_name` | `project_name` | Strip outer whitespace, normalize spaces | Invariant |
| `agency` | `agency` | Trim whitespace | If empty $\rightarrow$ `""` |
| `state` | `state` | Trim whitespace (propagated administrative heading) | Invariant (100% populated) |
| `sector` | `sector` | Trim whitespace (propagated sector heading) | Invariant (100% populated) |
| `approval_date` | `approval_date_raw`<br>`approval_date` | Preserve verbatim.<br>Parse `M-YYYY` or `MM-YYYY` $\rightarrow$ `YYYY-MM-01` | If empty $\rightarrow$ `""` |
| *Unavailable* | `start_date_raw`<br>`start_date` | Not present in OCMS Table 7 layout | Assigned `""` (`UNAVAILABLE`) |
| `original_completion_date` | `original_completion_date_raw`<br>`original_completion_date` | Preserve verbatim.<br>Parse `M/YYYY` or `MM/YYYY` $\rightarrow$ `YYYY-MM-01` | If empty $\rightarrow$ `""` (2 source records) |
| `revised_completion_date` | `revised_completion_date_raw`<br>`revised_completion_date` | Preserve verbatim.<br>Parse `Mon-YYYY` (e.g. `Jun-2023`) $\rightarrow$ `YYYY-MM-01` | If empty / N.A. $\rightarrow$ `""` |
| `anticipated_completion_date` | `anticipated_completion_date_raw`<br>`anticipated_completion_date` | Preserve verbatim.<br>Parse `M/YYYY` or `MM/YYYY` $\rightarrow$ `YYYY-MM-01` | If empty / N.A. $\rightarrow$ `""` |
| `original_cost_crore` | `original_cost_crore` | Float parse (remove commas) | Invariant ($\ge 0.0$) |
| `revised_cost_crore` | `revised_cost_crore` | Float parse (remove commas) | If empty / N.A. $\rightarrow$ `""` (1,234 records) |
| `anticipated_cost_crore` | `anticipated_cost_crore` | Float parse (remove commas) | If empty / N.A. $\rightarrow$ `""` |
| `cumulative_expenditure_crore` | `cumulative_expenditure_crore` | Float parse (remove commas) | If empty $\rightarrow$ `""` |
| `physical_progress_pct` | `physical_progress_pct` | Float parse (remove `%`) | If empty / `-` $\rightarrow$ `""` (159 records) |
| `source_page` | `source_page` | Integer cast (41–229) | Invariant |
| `sl_no` | `source_row` | Integer cast (1–1595) | Invariant |
| *Constant* | `source_file` | Assign `'FlashReport_June_2025.pdf'` | Invariant |
| *Calculated* | `source_record_hash` | SHA-256 of raw source CSV row line | Invariant |
| *Unavailable* | `legacy_ocms_code` | Not present in June 2025 layout | Assigned `""` (`UNAVAILABLE`) |
| *Unavailable* | `pmgid` | Not present in June 2025 layout | Assigned `""` (`UNAVAILABLE`) |

---

### 5.2 July 2025 Table 4 Crosswalk (PAIMANA Initial Format — 791 Records)

| Source Column (`table4_july_2025_projects.csv`) | Canonical Column | Physical Transformation | Missing-Value Behavior |
|---|---|---|---|
| `snapshot_date` (`2025-07`) | `snapshot_date` | Standardize to ISO `2025-07-31` | Invariant |
| *Constant* | `source_snapshot` | Assign `'2025-07'` | Invariant |
| *Constant* | `source_table` | Assign `'Table 4'` | Invariant |
| `project_id` | `source_project_id` | Trim whitespace (4–7 digit PAIMANA ID) | Invariant (791 unique) |
| *Calculated* | `canonical_project_key` | `'2025-07:Table 4:' + source_project_id` | Invariant (791 unique) |
| `project_name` | `project_name` | Strip outer whitespace, normalize spaces | Invariant |
| `agency` | `agency` | Trim whitespace | Invariant |
| `state` | `state` | Trim whitespace | If empty $\rightarrow$ `""` (1 source record, Sl 447) |
| *Unavailable* | `sector` | Not present in Table 4 layout | Assigned `""` (`UNAVAILABLE`) |
| `approval_date` | `approval_date_raw`<br>`approval_date` | Preserve verbatim.<br>Parse `MM/YYYY` $\rightarrow$ `YYYY-MM-01` | If empty $\rightarrow$ `""` (3 source records) |
| *Unavailable* | `start_date_raw`<br>`start_date` | Not present in Table 4 layout | Assigned `""` (`UNAVAILABLE`) |
| `original_completion_date` | `original_completion_date_raw`<br>`original_completion_date` | Preserve verbatim.<br>Parse `MM/YYYY` $\rightarrow$ `YYYY-MM-01` | Invariant |
| `revised_completion_date` | `revised_completion_date_raw`<br>`revised_completion_date` | Preserve verbatim.<br>Parse `MM/YYYY` $\rightarrow$ `YYYY-MM-01` | If empty / `(-)` $\rightarrow$ `""` |
| *Unavailable* | `anticipated_completion_date_raw`<br>`anticipated_completion_date` | Not present in Table 4 layout | Assigned `""` (`UNAVAILABLE`) |
| `original_cost_crore` | `original_cost_crore` | Float parse (remove commas) | Invariant ($\ge 0.0$) |
| `revised_cost_crore` | `revised_cost_crore` | Float parse (remove commas) | Invariant ($\ge 0.0$) |
| *Unavailable* | `anticipated_cost_crore` | Not present in Table 4 layout | Assigned `""` (`UNAVAILABLE`) |
| `cumulative_expenditure_crore` | `cumulative_expenditure_crore` | Float parse (remove commas) | Invariant ($\ge 0.0$) |
| `physical_progress_pct` | `physical_progress_pct` | Float parse (remove `%`) | Invariant ($[0.0, 100.0]$) |
| `source_page` | `source_page` | Integer cast (37–66) | Invariant |
| `sl_no` | `source_row` | Integer cast (1–791) | Invariant |
| *Constant* | `source_file` | Assign `'FlashReport_July_2025.pdf'` | Invariant |
| *Calculated* | `source_record_hash` | SHA-256 of raw source CSV row line | Invariant |
| *Unavailable* | `legacy_ocms_code` | Not present in July 2025 layout | Assigned `""` (`UNAVAILABLE`) |
| *Unavailable* | `pmgid` | Not present in July 2025 layout | Assigned `""` (`UNAVAILABLE`) |

---

### 5.3 July 2026 Table 6 Crosswalk (PAIMANA Expanded Format — 1,775 Records)

| Source Column (`table6_july_2026_projects.csv`) | Canonical Column | Physical Transformation | Missing-Value Behavior |
|---|---|---|---|
| `snapshot_date` (`2026-07`) | `snapshot_date` | Standardize to ISO `2026-07-31` | Invariant |
| *Constant* | `source_snapshot` | Assign `'2026-07'` | Invariant |
| *Constant* | `source_table` | Assign `'Table 6'` | Invariant |
| `project_id` | `source_project_id` | Trim whitespace (6–7 digit PAIMANA ID) | Invariant (1,775 unique) |
| *Calculated* | `canonical_project_key` | `'2026-07:Table 6:' + source_project_id` | Invariant (1,775 unique) |
| `project_name` | `project_name` | Strip outer whitespace, normalize spaces | Invariant |
| `agency` | `agency` | Trim whitespace | If empty $\rightarrow$ `""` |
| `state` | `state` | Trim whitespace (positional column 2) | Invariant (0 numeric, 0 empty) |
| *Unavailable* | `sector` | Not present in Table 6 layout | Assigned `""` (`UNAVAILABLE`) |
| `approval_date` | `approval_date_raw`<br>`approval_date` | Preserve verbatim.<br>Parse `MM/YYYY` $\rightarrow$ `YYYY-MM-01` | If empty / `NA` $\rightarrow$ `""` (e.g. Sl 557) |
| `start_date` | `start_date_raw`<br>`start_date` | Preserve verbatim.<br>Parse `MM/YYYY` $\rightarrow$ `YYYY-MM-01` | If empty / `NA` $\rightarrow$ `""` |
| `original_completion_date` | `original_completion_date_raw`<br>`original_completion_date` | Preserve verbatim.<br>Parse `MM/YYYY` $\rightarrow$ `YYYY-MM-01` | Invariant |
| `revised_completion_date` | `revised_completion_date_raw`<br>`revised_completion_date` | Preserve verbatim.<br>Parse `MM/YYYY` $\rightarrow$ `YYYY-MM-01` | If empty / `(-)` $\rightarrow$ `""` |
| *Unavailable* | `anticipated_completion_date_raw`<br>`anticipated_completion_date` | Not present in Table 6 layout | Assigned `""` (`UNAVAILABLE`) |
| `original_cost_crore` | `original_cost_crore` | Float parse (remove commas) | Invariant ($\ge 0.0$) |
| `revised_cost_crore` | `revised_cost_crore` | Float parse (remove commas) | If empty / `(-)` $\rightarrow$ `""` |
| *Unavailable* | `anticipated_cost_crore` | Not present in Table 6 layout | Assigned `""` (`UNAVAILABLE`) |
| `cumulative_expenditure_crore` | `cumulative_expenditure_crore` | Float parse (remove commas) | If empty $\rightarrow$ `""` |
| `physical_progress_pct` | `physical_progress_pct` | Float parse (remove `%`) | If empty $\rightarrow$ `""` |
| `source_page` | `source_page` | Integer cast (55–152) | Invariant |
| `sl_no` | `source_row` | Integer cast (1–1775) | Invariant |
| *Constant* | `source_file` | Assign `'FlashReport_July_2026.pdf'` | Invariant |
| *Calculated* | `source_record_hash` | SHA-256 of raw source CSV row line | Invariant |
| `legacy_ocms_code` | `legacy_ocms_code` | Trim whitespace | Reports `'-'` across source |
| `pmgid` | `pmgid` | Trim whitespace | Reports `'-'` across source |

---

## 6. Temporal Invariants & Snapshot Alignment

### 6.1 Formal Cutoff Dates
All snapshots are indexed to the exact calendar end of the respective reporting month:

$$\mathcal{T}_{\text{snapshots}} = \{ \mathbf{2025\text{-}06\text{-}30}, \, \mathbf{2025\text{-}07\text{-}31}, \, \mathbf{2026\text{-}07\text{-}31} \}$$

### 6.2 Strict Temporal Rules
1. **No Intermediate Interpolation**: The 12-month interval between July 2025 and July 2026 represents genuine source publication cadence in our acquired data. **Intermediate observations (e.g. August 2025 – June 2026) MUST NOT be synthetically generated, interpolated, or backfilled.**
2. **Variable Interval Handling**: In downstream Module 2C, feature calculation functions must accept elapsed time $\Delta t$ explicitly rather than assuming equidistant monthly steps:
   $$\Delta t_{1} = t_{\text{Jul 25}} - t_{\text{Jun 25}} = 1\text{ month} \approx 31\text{ days}$$
   $$\Delta t_{2} = t_{\text{Jul 26}} - t_{\text{Jul 25}} = 12\text{ months} \approx 365\text{ days}$$
   Rate features (e.g. expenditure velocity, physical progress rate) must normalize by elapsed time:
   $$\text{burn\_rate} = \frac{\Delta \text{expenditure}}{\Delta t}$$

---

## 7. Mandatory Module 2B Validation Gates

Before any longitudinal panel or canonical table is certified, the automated validation pipeline must enforce 11 non-negotiable gates:

```
[ Gate 1: Cryptographic Source Hash Invariance ] ────► PASS
[ Gate 2: Row Count Invariance (4,161 total)   ] ────► PASS
[ Gate 3: Canonical Schema Compliance          ] ────► PASS
[ Gate 4: Zero Source Record Duplication       ] ────► PASS
[ Gate 5: 100% Provenance Traceability         ] ────► PASS
[ Gate 6: Deterministic Primary Key Uniqueness ] ────► PASS
[ Gate 7: Conservative Identity Categorization ] ────► PASS
[ Gate 8: Zero Automated Fuzzy Merges          ] ────► PASS
[ Gate 9: Missing-Value Semantic Preservation  ] ────► PASS
[ Gate 10: Financial & Progress Bounds Check   ] ────► PASS
[ Gate 11: Temporal Cutoff Date Validation     ] ────► PASS
```

1. **Gate 1 — Cryptographic Hash Invariance (HARD STOP):** Verify SHA-256 of all 3 frozen files matches their freeze records exactly (`table7_june_2025_projects.sha256`, `table4_july_2025_projects.sha256`, `table6_july_2026_projects.sha256`).
2. **Gate 2 — Row Count Invariance (HARD STOP):** Exactly 1,595 records for June 2025, 791 for July 2025, and 1,775 for July 2026. Sum $= 4,161$.
3. **Gate 3 — Canonical Schema Compliance (HARD STOP):** Every canonical record must conform strictly to the 30-field schema specification.
4. **Gate 4 — Zero Source Duplication:** No raw source record appears more than once in the staged canonical layer.
5. **Gate 5 — 100% Provenance Traceability:** Every canonical row must map deterministically back to a physical source PDF, page number, serial number, and source record hash.
6. **Gate 6 — Deterministic Observation Keys:** `canonical_project_key` must be 100% unique across all 4,161 records.
7. **Gate 7 — Explicit Identity Confidence:** Every candidate entity cross-link must be tagged with an official confidence category (`EXACT_ID`, `EXPLICIT_CROSS_SOURCE_ID`, `STRONG_MATCH`, `REVIEW_REQUIRED`, `UNMATCHED`).
8. **Gate 8 — Prohibition on Blind Fuzzy Merges:** String similarity metrics alone must NEVER trigger an automated cross-source merge.
9. **Gate 9 — Missing-Value Fidelity:** Verify that unrevised costs remain empty and unavailable fields are not converted to `0` or `0.0`.
10. **Gate 10 — Financial & Progress Range Verification:** No negative costs, no negative expenditures, progress bounded in $[0.0, 100.0]$. Source anomalies (expenditure > cost, revised < original) explicitly preserved.
11. **Gate 11 — Valid Temporal Snapshots:** Every row has `snapshot_date` $\in \{ \text{'2025-06-30'}, \text{'2025-07-31'}, \text{'2026-07-31'} \}$.

---

## 8. Downstream Integration (Module 2C Predictive Prototype)

The canonical snapshot dataset directly feeds **Module 2C**, which will compute Point-in-Time (PIT) features and prediction targets without temporal leakage:

1. **Point-in-Time Feature Construction:**
   - **Static Scale & Scope:** Initial sanctioned cost ($\log \text{cost}$), initial scheduled gestation period ($\text{original\_doc} - \text{approval\_date}$).
   - **Dynamic Trajectory:** Cumulative expenditure ratio ($\text{expenditure} / \text{original\_cost}$), physical progress percentage, elapsed project time percentage.
   - **Velocity Signals:** Progress velocity ($\Delta \text{progress} / \Delta t$), expenditure acceleration.
2. **Prediction Target Definition (Forward Horizon $\Delta$):**
   - **Cost Overrun Risk Indicator:** Binary indicator $\mathbb{I}\Big(\frac{\text{revised\_cost}(t+\Delta) - \text{original\_cost}}{\text{original\_cost}} \ge 0.20\Big)$.
   - **Schedule Slippage Risk Indicator:** Binary indicator $\mathbb{I}\Big(\text{delay}(t+\Delta) \ge 6\text{ months}\Big)$.
3. **Predictive Baseline Models:**
   - Evaluated under strict time-based splits (e.g. Train on 2025 transitions, Test on 2026 outcomes) to eliminate lookahead bias.


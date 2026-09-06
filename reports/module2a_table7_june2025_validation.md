# Module 2A — June 2025 Table 7 Final Validation & Freeze Report

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 2A — Flash Report Ingestion & Verification  
**Reporting Period:** June 2025 (`2025-06`)  
**Source Document:** `data/raw/flash_reports/FlashReport_June_2025.pdf`  
**Extracted Table:** Table 7 (`Project List: Ongoing Projects as of 30th June 2025`)  
**Processed File:** `data/processed/table7_june_2025_projects.csv`  
**Date:** September 2026  
**Final Gate Status:** **MODULE 2A — JUNE 2025 TABLE 7 DATASET FREEZE SUCCESSFUL**  

---

## 1. Executive Summary & Verification Matrix

All pre-freeze gates, structural validations, semantic audits, and independent aggregate reconciliations have passed with zero discrepancies. The June 2025 Table 7 dataset is officially frozen in `data/processed/table7_june_2025_projects.csv`.

| Verification Gate | Specification / Target | Observed Result | Status |
|---|---|---|---|
| **Row Count** | Exactly 1,595 records | `1,595` records | **PASS** |
| **Unique Project IDs** | Exactly 1,595 unique IDs | `1,595` unique IDs (0 missing, 0 duplicates) | **PASS** |
| **Serial Sequence** | Consecutive integers 1–1595 | Min: `1`, Max: `1595`, Missing: `0`, Duplicates: `0` | **PASS** |
| **Source Page Bounds** | PDF pages 41–229 inclusive | Min: `41`, Max: `229` (189 pages; 100% within range) | **PASS** |
| **State Propagation** | Complete coverage across 33 states/UTs | `0` missing; 100% matches Table 2 state breakdown | **PASS** |
| **Sector Propagation** | Complete coverage across 17 sectors | `0` missing; 100% matches Table 1 sector breakdown | **PASS** |
| **Progress Bounds** | All non-empty in [0.0, 100.0] | `1,436` values, `0` out of bounds | **PASS** |
| **Non-Negative Financials** | Zero negative costs / expenditures | `0` negative values | **PASS** |
| **Cost Governance Rule** | revised_cost_crore preserved raw | `1,234` unrevised records kept empty (no artificial overwrite) | **PASS** |
| **Aggregate Reconciliation** | 5 official Table 1 financial totals | Exact match to `0.00` across all 5 macro aggregates | **PASS** |
| **Byte-for-Byte Promotion** | Interim SHA256 == Processed SHA256 | Exact cryptographic equality (`9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43`) | **PASS** |

---

## 2. Independent Aggregate Reconciliation

Every record in the frozen dataset was independently summed and verified against the official **Table 1 Overview (Sector-wise Distribution)** on PDF pages 7–8 and Table 7 summary totals (PDF page 229):

| Macro Indicator | Official MoSPI Table 1 Total | Processed Dataset Total | Variance | Reconciliation Status |
|---|---|---|---|---|
| **Total Projects** | `1,595` | `1,595` | `0` | **EXACT MATCH** |
| **Original Cost (Rs. Cr)** | `2,685,568.07` | `2,685,568.07` | `+0.00` | **EXACT MATCH** |
| **Revised* Cost (Rs. Cr)** | `2,801,018.15` | `2,801,018.15` | `-0.00` | **EXACT MATCH** |
| **Anticipated Cost (Rs. Cr)** | `2,975,429.26` | `2,975,429.26` | `+0.00` | **EXACT MATCH** |
| **Cumulative Expenditure (Rs. Cr)** | `1,630,750.12` | `1,630,750.12` | `-0.00` | **EXACT MATCH** |

*Note: MoSPI defines "Revised Cost*" as the Revised Cost if approved, or the Original Cost if no revision has taken place. In accordance with data governance, `revised_cost_crore` in the dataset remains strictly the raw revised value (`N.A.` for 1,234 projects).*

---

## 3. Data Governance & Missing Value Profile

| Column | Non-Empty Count | Missing / N.A. Count | Provenance & Source Observation |
|---|---|---|---|
| `snapshot_date` | 1,595 | 0 | Point-in-time snapshot constant (`2025-06-30`) |
| `source_page` | 1,595 | 0 | PDF page number (41 to 229) |
| `sl_no` | 1,595 | 0 | Consecutive integers 1 through 1595 |
| `project_id` | 1,595 | 0 | 1,580 `N...` codes + 15 legacy 9-digit OCMS codes |
| `project_name` | 1,595 | 0 | Sanitized multiline project description |
| `agency` | 1,595 | 0 | Central implementing agency (e.g. `AAI`, `NR`, `NHIDCL`) |
| `state` | 1,595 | 0 | Hierarchically propagated across 33 states/UTs |
| `sector` | 1,595 | 0 | Hierarchically propagated across 17 sectors |
| `approval_date` | 1,595 | 0 | Sanction date (`M-YYYY` or `MM-YYYY`) |
| `original_completion_date` | 1,593 | 2 | 2 projects report `N.A.` in source |
| `revised_completion_date` | 536 | 1,059 | 1,059 projects report `N.A.` (unrevised date) |
| `anticipated_completion_date` | 1,590 | 5 | 5 projects report `N.A.` (unrevised anticipated date) |
| `original_cost_crore` | 1,595 | 0 | Sanctioned original cost |
| `revised_cost_crore` | 361 | 1,234 | 1,234 projects unrevised (`N.A.` preserved raw) |
| `anticipated_cost_crore` | 1,595 | 0 | Anticipated cost |
| `cumulative_expenditure_crore` | 1,595 | 0 | Cumulative expenditure |
| `physical_progress_pct` | 1,436 | 159 | 159 projects report `-` or `N.A.` in source |

---

## 4. Cryptographic Provenance & File Integrity

| Artifact Role | File Path | File Size | SHA256 Checksum |
|---|---|---|---|
| **Raw Official Source PDF** | `data/raw/flash_reports/FlashReport_June_2025.pdf` | 14,003,041 bytes | `7f37c63abe9f92d8db6513ad68d91b5c172c9c27454f45691f53fff7ebb2a754` |
| **Staged Interim Dataset** | `data/interim/table7_june_2025_projects.csv` | 308,654 bytes | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` |
| **Frozen Processed Dataset** | `data/processed/table7_june_2025_projects.csv` | 308,654 bytes | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` |
| **Checksum Verification File** | `data/processed/table7_june_2025_projects.sha256` | 100 bytes | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` |

---

## 5. Final Confirmation

MODULE 2A — JUNE 2025 TABLE 7 DATASET FREEZE SUCCESSFUL

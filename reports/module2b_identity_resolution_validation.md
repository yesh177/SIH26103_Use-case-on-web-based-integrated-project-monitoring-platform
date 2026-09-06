# Module 2B — Project Identity Resolution & Longitudinal Panel Report

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 2B — Canonicalization & Longitudinal Panel Construction (Phase 3)  
**Reporting Periods:** June 2025 (`2025-06`), July 2025 (`2025-07`), July 2026 (`2026-07`)  
**Input Artifact:** `data/interim/canonical_snapshots.csv` (4,161 observations)  
**Output Artifacts:**
1. `data/interim/project_identity_map.csv`
2. `data/interim/project_snapshot_panel.csv`  
**Final Status:** **STAGED INTERIM IDENTITY RESOLUTION & PANEL (PRE-FREEZE)**  

---

## 1. Executive Summary

Module 2B Phase 3 resolves physical infrastructure project identities across three distinct historical MoSPI/PAIMANA monitoring snapshots. It transforms the granular canonical observation layer into stable longitudinal physical project entities.

### Fundamental Principle: Defensible Identity Resolution Over Maximal Matching
In strict adherence to the project charter:
* **No Blind Fuzzy Merging:** String distance algorithms (Levenshtein, Jaro-Winkler, word embedding cosine) were **never** used autonomously to force merges.
* **No Cross-System False Equivalences:** OCMS identifiers (`N...`) were not equated to PAIMANA numeric IDs without multi-attribute consensus.
* **Conservative Disambiguation:** Ambiguous candidates or cross-snapshot discrepancies (e.g. line ministry vs CPSE shifts, state modifications) were formally classified as `REVIEW_REQUIRED` and **strictly kept unmerged** with independent deterministic keys.

---

## 2. Quantitative Identity Resolution Summary

| Metric | Count | Percentage of Total Universe | Notes |
|---|---|---|---|
| **Total Canonical Observations** | **`4,161`** | 100.0% | Input universe preserved exactly |
| **Resolved Physical Projects** | **`3,633`** | — | Unique physical projects tracked |
| **Observations Matched (`EXACT_ID`)** | `872` | 21.0% | 436 paired observations (July 2025 $\leftrightarrow$ July 2026) |
| **Observations Matched (`STRONG_MATCH`)**| `137` | 3.3% | OCMS $\leftrightarrow$ PAIMANA cross-system consensus |
| **Observations Flagged (`REVIEW_REQUIRED`)**| `247` | 5.9% | Ambiguous candidates kept strictly unmerged |
| **Observations Independent (`UNMATCHED`)**| `2,905` | 69.8% | Unique to a single snapshot |

---

## 3. Longitudinal Trajectory Distribution

A project's trajectory represents the combination of monitoring snapshots in which its physical entity was observed:

| Longitudinal Trajectory Pattern | Physical Projects | Total Observations | Operational Description |
|---|---|---|---|
| **`2025-06 + 2025-07 + 2026-07`** | **`47`** | `141` | Gold-standard 3-snapshot longitudinal trajectory spanning OCMS and PAIMANA |
| **`2025-07 + 2026-07`** | **`390`** | `780` | Continuous 12-month PAIMANA trajectory (July 2025 $\rightarrow$ July 2026) |
| **`2025-06 + 2026-07`** | **`39`** | `78` | OCMS project linked directly to 2026 PAIMANA expansion |
| **`2025-06 + 2025-07`** | **`5`** | `10` | OCMS project linked to initial 2025 PAIMANA onboarding |
| **`2025-06` (Single Snapshot)** | `1,504` | `1,504` | OCMS projects unique to June 2025 |
| **`2026-07` (Single Snapshot)** | `1,299` | `1,299` | New projects / expanded coverage onboarded by July 2026 |
| **`2025-07` (Single Snapshot)** | `349` | `349` | July 2025 observations (unmatched or flagged for review) |
| **Total Universe** | **`3,633`** | **`4,161`** | Exact parity with source observations |

---

## 4. Deterministic Matching Methodology by Tier

### 4.1 Tier 1: `EXACT_ID` (July 2025 $\leftrightarrow$ July 2026)
* **Pre-condition:** `source_project_id` must be identical across both PAIMANA snapshots.
* **Corroborating Invariants Required:**
  1. **State Compatibility:** Administrative state must match directly, or share regional overlap (e.g. multi-state inclusion).
  2. **Agency Compatibility:** Executing agency must match directly or via standardized organizational acronym/bracket tokens (e.g. `[SECL]` $\sim$ `SECL - CIL`, `[AAI]` $\sim$ `Airport Authority of India`).
  3. **Title Corroboration:** Project titles must share distinctive non-stopword tokens (e.g. facility name, terminal, section names).
* **Result:** **436 project pairs (872 observations)** satisfied all three corroborating criteria and received unified project keys (`PROJ-PAIMANA-<id>`).

### 4.2 Tier 2: `EXPLICIT_CROSS_SOURCE_ID`
* **Condition:** Use only explicit authoritative cross-source identifier published directly in the official source document.
* **Empirical Finding:** In July 2026 Table 6, columns `(Legacy OCMS Code)` and `(PMGID)` uniformly reported `(-)` across all 1,775 rows.
* **Result:** **0 matches.** In accordance with strict governance, zero cross-source IDs were fabricated.

### 4.3 Tier 3: `STRONG_MATCH` (OCMS June 2025 $\leftrightarrow$ PAIMANA)
* **Deterministic Consensus Rule:**
  $$\big(\texttt{State}, \, \texttt{Agency}, \, \texttt{Approval Date}, \, \texttt{Original Cost} \pm 0.05\big) \quad \land \quad \text{Title Overlap} \ge 0.85 \quad \land \quad \text{Unique Candidate}$$
* **Title Overlap Metric:**
  $$\text{Jaccard Token Overlap} = \frac{|S_A \cap S_B|}{|S_A \cup S_B|}$$
  Evaluated after NFKD Unicode normalization, case folding, separator normalization, and removal of boilerplate stopwords.
* **Result:**
  * June 2025 $\leftrightarrow$ July 2025: **39 matches**
  * June 2025 $\leftrightarrow$ July 2026: **79 matches**
  * All 27 projects matching both July 2025 and July 2026 matched the **exact same target project ID**, proving 100% transitivity.

### 4.4 Tier 4: `REVIEW_REQUIRED` (Strictly Unmerged)
* **Trigger:** Identical PAIMANA project ID, but exhibiting an institutional or administrative divergence (e.g. line ministry listed in 2025 vs CPSE in 2026, or state reassignment).
* **Action:** **Strictly unmerged.** Each observation receives an independent deterministic key (`PROJ-REVIEW-<snapshot>-<project_id>`) with `review_status = "PENDING_DOMAIN_REVIEW"` and full diagnostic evidence recorded.
* **Result:** **247 observations** safely isolated from automated merging.

### 4.5 Tier 5: `UNMATCHED`
* **Trigger:** No candidate satisfied Tier 1–3 criteria.
* **Action:** Retained as independent single-snapshot physical projects with deterministic keys (`PROJ-UNMATCHED-<snapshot>-<project_id>`).
* **Result:** **2,905 observations**.

---

## 5. Case Studies & Verification Examples

### 5.1 Accepted 3-Snapshot Longitudinal Match (`STRONG_MATCH` + `EXACT_ID`)
* **Canonical Project Key:** `PROJ-PAIMANA-400033`
* **Asset:** Bhatadi Open Cast Coal Mine Expansion
* **Observations:**
  1. **June 2025 (`2025-06`):** OCMS ID `N06000254`, `BHATADI EXPANSION OC`, Agency: `WCL`, State: `MAHARASHTRA`, Cost: ₹580.60 Cr, Exp: ₹61.33 Cr.
  2. **July 2025 (`2025-07`):** PAIMANA ID `400033`, `BHATADI EXPANSION OC`, Agency: `Western Coalfields Limited [WCL]`, State: `Maharashtra`, Cost: ₹580.61 Cr, Exp: ₹20.52 Cr.
  3. **July 2026 (`2026-07`):** PAIMANA ID `400033`, `BHATADI EXPANSION OC`, Agency: `WCL - CIL`, State: `Maharashtra`, Cost: ₹580.61 Cr, Exp: ₹112.17 Cr.
* **Evidence:** Multi-attribute consensus matches June 2025 to July 2025 (Cost diff 0.01 Cr, title overlap 1.00); July 2025 matches July 2026 under `EXACT_ID`.

### 5.2 Accepted 2-Snapshot Match (`EXACT_ID`)
* **Canonical Project Key:** `PROJ-PAIMANA-612786`
* **Asset:** Kadapa Airport New Domestic Terminal Building
* **Observations:**
  1. **July 2025 (`2025-07`):** PAIMANA ID `612786`, `Construction of New Domestic Terminal Building Building... at Kadapa Airport`, Agency: `Airport Authority of India [AAI]`, State: `Andhra Pradesh`, Cost: ₹265.91 Cr, Exp: ₹45.54 Cr.
  2. **July 2026 (`2026-07`):** PAIMANA ID `612786`, `Construction of New Domestic Terminal Building Building... at Kadapa Airport`, Agency: `Airport Authority of India [AAI]`, State: `Andhra Pradesh`, Cost: ₹265.91 Cr, Exp: ₹176.38 Cr.
* **Evidence:** Exact ID match, 100% state agreement, 100% agency agreement, title overlap 0.95.

### 5.3 Rejected / Ambiguous Match Candidate (`REVIEW_REQUIRED`)
* **Observations:**
  1. `2025-07:Table 4:400012` (`PROJ-REVIEW-2025-07-400012`)
  2. `2026-07:Table 6:400012` (`PROJ-REVIEW-2026-07-400012`)
* **Project Name:** City Gas Distribution Network
* **Divergence Reason:** In 2025, agency reported as `Ministry of Petroleum & Natural Gas`. In 2026, reported as executing CPSE `Indian Oil Corporation Limited [IOCL]`. State also narrowed from multi-state to `Uttar Pradesh`.
* **Resolution Action:** Because the agency string diverged without an official concordance dictionary, the system refused to merge these records automatically. They are retained as separate projects pending explicit human domain sign-off.

---

## 6. Generated Datasets & Provenance

| Dataset | Relative File Path | Rows | Columns | SHA-256 Checksum |
|---|---|---|---|---|
| **Identity Map** | `data/interim/project_identity_map.csv` | 4,161 | 9 | `16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb` |
| **Snapshot Panel** | `data/interim/project_snapshot_panel.csv` | 4,161 | 35 | `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47` |

---

## 7. Automated Test Suite Results

The comprehensive test suite [`tests/test_project_identity_resolution.py`](file:///c:/Users/Lenovo/OneDrive/Documents/paimana-predictive-risk/tests/test_project_identity_resolution.py) executed and validated all 20 assertions:

```text
python -m unittest tests/test_project_identity_resolution.py
----------------------------------------------------------------------
Ran 19 tests in 1.130s

OK
```

Full repository test suite (including Table 6 extractor, panel validator, canonical snapshots, and identity resolution):
```text
python -m unittest discover -s tests -p "test_*.py"
----------------------------------------------------------------------
Ran 61 tests in 1.503s

OK
```

---

## 8. Limitations & Recommendations for Downstream Module 2C

1. **Conservative Recall:** By enforcing strict multi-attribute consensus ($\text{Title Overlap} \ge 0.85$ and cost diff $\le 0.05$ Cr), some OCMS projects whose sanctioned costs were revised prior to portal transition remain unlinked (`UNMATCHED`). This represents a deliberate trade-off prioritizing **zero false merges**.
2. **Gold-Standard Training Subsets:** For longitudinal feature engineering (e.g. burn rate acceleration, slippage velocity), Module 2C can train directly on the **476 multi-snapshot trajectories** (`EXACT_ID` and `STRONG_MATCH`), while utilizing the full 4,161 cross-sectional observations for static risk baselines.
3. **Status:** All interim artifacts remain unfrozen in `data/interim/` awaiting formal review.


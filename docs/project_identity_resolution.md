# Module 2B — Project Identity Resolution & Longitudinal Entity Policy

> **Project:** SIH26103 — Use Case on Web-Based Integrated Project Monitoring Platform  
> **Product:** PAIMANA Predictive Risk Intelligence  
> **Document:** `docs/project_identity_resolution.md`  
> **Module:** 2B — Canonicalization & Longitudinal Panel Construction  
> **Phase:** Phase 1 — Specification Only  
> **Status:** ACTIVE SPECIFICATION — NO MANUAL OR PREMATURE EXECUTION  

---

## 1. Executive Summary & Policy Mandate

A foundational challenge in tracking Indian Central Sector infrastructure projects longitudinally across the 2025–2026 timeframe is the institutional and technological migration from the legacy **Online Computerized Monitoring System (OCMS-2006)** to the modern **PAIMANA platform (`ipm.mospi.gov.in`)**.

This document establishes the binding **Project Identity Resolution Policy** for PAIMANA Predictive Risk Intelligence. Its goal is to resolve project records across disparate monitoring cycles into stable longitudinal entities **without corrupting project histories through false merges, blind fuzzy matching, or synthetic assumptions**.

---

## 2. Institutional Context: Multi-System Architecture

Our frozen dataset tier contains three monitoring snapshots spanning this architectural transition:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CENTRAL SECTOR MONITORING REGIMES                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
         │                                                                   │
         ▼                                                                   ▼
┌───────────────────────────────────────────┐       ┌─────────────────────────────────────────────┐
│ 1. LEGACY OCMS REGIME (June 2025)         │       │ 2. MODERN PAIMANA REGIME (July 2025 & 2026) │
├───────────────────────────────────────────┤       ├─────────────────────────────────────────────┤
│ • System: OCMS-2006                       │       │ • System: PAIMANA Portal (ipm.mospi.gov.in) │
│ • Table: Table 7 (1,595 projects)         │       │ • Tables: Table 4 (2025), Table 6 (2026)    │
│ • Identifier Schema:                      │       │ • Identifier Schema:                        │
│   - Alpha-numeric: 'N' + 8 digits         │       │   - Numeric: 4 to 7 digits                  │
│     (e.g., 'N04000073' - 1,580 records)   │       │     (e.g., '612786', '701107', '706865')    │
│   - Legacy numeric: 9 digits              │       │ • Universe:                                 │
│     (e.g., '220100265' - 15 records)      │       │   - July 2025: 791 projects                 │
│ • Universe: Comprehensive list across     │       │   - July 2026: 1,775 projects               │
│   all sectors, states, and cost thresholds│       │ • Attributes: Standardized portal schema    │
└───────────────────────────────────────────┘       └─────────────────────────────────────────────┘
```

### Core Reality
The identifier namespaces between OCMS and PAIMANA are **disjoint**:
- An OCMS identifier (e.g. `N04000073`) will **never** textually match a PAIMANA identifier (e.g. `612786`).
- While PAIMANA Table 6 introduced column headers for `(Legacy OCMS Code)` and `(PMGID)`, the official source report explicitly prints `(-)` across all 1,775 projects in July 2026.
- Therefore, cross-system linkage cannot rely on explicit external foreign keys and must adhere to conservative, auditable rules.

---

## 3. Project Universe & Lifecycle Rules

To prevent invalid inferences during longitudinal panel assembly and downstream predictive modeling, the following four domain rules are binding:

### Rule 1: Non-Completion Inference Rule
> **A project appearing in snapshot $t$ but absent from snapshot $t+1$ must NOT be automatically classified as "Completed".**

*Rationale:* In government project monitoring, a project may drop out of a published monthly Flash Report for multiple operational reasons:
1. **Reporting Threshold Drops:** Cost revisions or de-scoping may bring a project below the ₹150 Crore reporting threshold.
2. **Administrative Restructuring:** The project may be transferred to a State Government, a joint venture, or a different ministry.
3. **Reporting Non-Compliance:** Implementing agencies occasionally fail to submit monthly data by the publication cutoff date.
4. **Institutional Transition Drop:** During the July 2025 platform migration, only 791 projects were onboarded into Table 4 out of the 1,595 projects monitored in June 2025 OCMS. The remaining projects were not necessarily completed; they were phased into PAIMANA over subsequent reporting cycles (as evidenced by 1,775 projects in July 2026).

### Rule 2: Non-Newness Inference Rule
> **The appearance of a project in snapshot $t+1$ that was absent in snapshot $t$ must NOT be automatically classified as a "Newly Sanctioned Project".**

*Rationale:* A project appearing for the first time in July 2026 Table 6 may have an approval date from 2012 or 2018. It is an existing ongoing project that was newly onboarded into the PAIMANA platform, elevated above the threshold, or consolidated from legacy regional pipelines.

### Rule 3: Identity Amendment Rule
> **Any proposed cross-snapshot identity link represents an empirical claim that requires multi-attribute corroborating evidence.**

Static inception attributes—specifically initial sanctioned cost, original Date of Commissioning, administrative state, and approval date—must be cross-referenced before asserting that two records represent the same physical infrastructure asset.

### Rule 4: Source Coverage Retention
> **Source coverage disparities must be explicitly retained in the metadata and must not be masked by synthetic imputation or forced joins.**

The longitudinal panel must preserve the exact snapshot universe sizes ($1,595 \rightarrow 791 \rightarrow 1,775$) rather than truncating all analyses to an artificially restricted inner-join intersection.

---

## 4. Conservative Identity-Resolution Taxonomy

Every proposed link between a record in snapshot $A$ and a record in snapshot $B$ must be formally tagged with one of five deterministic confidence tiers:

```
                                    ┌──────────────────────────────────────────────┐
                                    │      IDENTITY RESOLUTION CONFIDENCE TIERS    │
                                    └──────────────────────┬───────────────────────┘
                                                           │
          ┌───────────────────────────┬────────────────────┴───────────────┬───────────────────────────┐
          │                           │                                    │                           │
          ▼                           ▼                                    ▼                           ▼
┌───────────────────┐       ┌───────────────────┐                ┌───────────────────┐       ┌───────────────────┐
│ 1. EXACT_ID       │       │ 2. EXPLICIT_CROSS │                │ 3. STRONG_MATCH   │       │ 4. REVIEW_REQUIRED│
│    (Confidence:   │       │    SOURCE_ID      │                │    (Confidence:   │       │    (Confidence:   │
│     CERTAIN)      │       │    (Confidence:   │                │     HIGH)         │       │     AMBIGUOUS)    │
│                   │       │     CERTAIN)      │                │                   │       │                   │
│ Same platform     │       │ Explicit source   │                │ Disparate systems │       │ Partial match /   │
│ identifier match  │       │ bridge provided   │                │ but exact multi-  │       │ attribute conflict│
│ + corroboration   │       │ in source data    │                │ attribute lock    │       │ / multiple cand.  │
└───────────────────┘       └───────────────────┘                └───────────────────┘       └───────────────────┘
                                                                                                       │
                                                                                                       ▼
                                                                                             ┌───────────────────┐
                                                                                             │ 5. UNMATCHED      │
                                                                                             │    (Independent   │
                                                                                             │     trajectory)   │
                                                                                             └───────────────────┘
```

### 4.1 Tier 1: `EXACT_ID` (Highest Confidence)
* **Applicability:** Strictly within the **same identifier namespace** (e.g. July 2025 Table 4 $\leftrightarrow$ July 2026 Table 6).
* **Criteria:**
  1. `project_id(A) == project_id(B)` (exact character match).
  2. `agency(A)` matches `agency(B)` (normalized).
  3. `state(A)` matches `state(B)`.
  4. Core project title keywords match (e.g. Kadapa Airport Terminal Building).
* **Action:** **Automatic longitudinal merge permitted.** Both observations receive the same `longitudinal_project_entity_id`.

### 4.2 Tier 2: `EXPLICIT_CROSS_SOURCE_ID` (Source-Authoritative Bridge)
* **Applicability:** Cross-system linkage where the source document explicitly publishes the predecessor identifier.
* **Criteria:**
  1. `legacy_ocms_code(B) == project_id(A)`.
  2. Or official MoSPI transition concordance mapping officially provided.
* **Current Empirical Reality:** Because July 2026 Table 6 prints `(-)` for all legacy codes, **zero records currently qualify under Tier 2 based on raw published data**. This tier is reserved for official concordances if acquired.
* **Action:** **Automatic merge permitted ONLY upon authentic source verification.**

### 4.3 Tier 3: `STRONG_MATCH` (Deterministic Multi-Attribute Consensus)
* **Applicability:** Cross-system matching between OCMS (June 2025) and PAIMANA (July 2025 / July 2026).
* **Criteria (ALL must hold simultaneously):**
  1. **Administrative State:** Exact normalized match (`state(A) == state(B)`).
  2. **Implementing Agency:** Exact normalized match (`agency(A) == agency(B)`).
  3. **Inception Financial Baseline:** $\big|\texttt{original\_cost\_crore}(A) - \texttt{original\_cost\_crore}(B)\big| < 0.05$ ₹ Cr (exact to within rounding).
  4. **Approval Date:** Exact month-year match (`approval_date(A) == approval_date(B)`).
  5. **Title Distinctiveness:** Normalized title token overlap $\ge 0.85$, AND no other candidate in the target snapshot shares the same attributes.
* **Uniqueness Constraint:** If more than one project in the target snapshot matches the tuple $\big(\texttt{State}, \texttt{Agency}, \texttt{Original Cost}, \texttt{Approval Date}\big)$, the match **collapses to Tier 4 (`REVIEW_REQUIRED`)**.
* **Action:** **Staged for deterministic cross-system linkage with explicit audit logging.**

### 4.4 Tier 4: `REVIEW_REQUIRED` (Ambiguous / Conflicted Candidates)
* **Applicability:** Any candidate link exhibiting partial alignment but failing Tier 3 consensus.
* **Triggers:**
  - High project title lexical similarity, but `original_cost_crore` differs by $> 10\%$.
  - Exact financial and state match, but different approval dates.
  - One-to-many or many-to-one candidate collisions (e.g. multiple highway widening packages in the same state under the same agency).
* **Action:** **HARD PROHIBITION ON AUTOMATED MERGE.** Records remain unlinked in the automated panel unless manually validated with official documentary evidence.

### 4.5 Tier 5: `UNMATCHED` (Unique Snapshot Trajectory)
* **Applicability:** Records with no candidate link satisfying Tiers 1–3.
* **Action:** Treated as an independent single-snapshot or partial-snapshot trajectory. Retained in the canonical layer for cross-sectional training and evaluation.

---

## 5. Strict Anti-Patterns & Prohibited Operations

### Anti-Pattern 1: The False Identity Equivalence
> [!CAUTION]
> **PROHIBITION:** Never assume that an identifier string appearing in an OCMS report has any relationship to a numerical identifier in a PAIMANA report.  
> E.g., OCMS serial `525` or code `N04000073` has zero relationship to PAIMANA project code `705375`.

### Anti-Pattern 2: Blind Project-Name Fuzzy Merging
> [!CAUTION]
> **PROHIBITION:** Standard string distance algorithms (Levenshtein distance, Jaro-Winkler, Cosine similarity on word embeddings) must **NEVER** serve as an autonomous merge rule.

#### Why Fuzzy Matching Fails in Indian Infrastructure Data:
Indian central sector infrastructure projects frequently utilize standardized, repetitive administrative nomenclature:
- *Example A:* `"Four Laning of NH-31 from Km 120.00 to Km 150.00 (Package I)"`
- *Example B:* `"Four Laning of NH-31 from Km 150.00 to Km 180.00 (Package II)"`
- Standard fuzzy matching computes $> 95\%$ similarity between Example A and Example B, despite them being distinct physical civil contracts with different contractors, budgets, and delay profiles. Blind fuzzy merging would destroy data integrity by collapsing two distinct projects into a corrupted aggregate.

### Anti-Pattern 3: Synthetic History Fabrication
> [!CAUTION]
> **PROHIBITION:** Never backfill or interpolate missing snapshot observations between July 2025 and July 2026. A 12-month jump is a genuine empirical gap and must be modeled as a 12-month time delta $\Delta t$, not filled with synthetic monthly steps.

---

## 6. Longitudinal Entity ID Assignment Architecture

In the longitudinal panel layer (to be implemented in downstream Phase 2), each record will maintain both its snapshot-specific key and its unified longitudinal entity key:

```sql
-- Conceptual Schema Representation
canonical_project_key          -- '2026-07:Table 6:612786' (Unique snapshot observation)
longitudinal_entity_id         -- 'ENT_PAIMANA_612786' (Unified entity across snapshots)
identity_resolution_tier       -- 'EXACT_ID'
resolution_evidence            -- 'Matched on PAIMANA project_id 612786, Agency AAI, State AP'
```

### Prefix Convention for `longitudinal_entity_id`:
1. `ENT_PAIMANA_<project_id>`: Projects identified under the modern PAIMANA namespace (e.g. `ENT_PAIMANA_612786`).
2. `ENT_OCMS_<project_id>`: Projects identified under the legacy OCMS namespace that could not be linked to PAIMANA with Tier 1–3 confidence (e.g. `ENT_OCMS_N04000073`).
3. If a Tier 3 `STRONG_MATCH` bridges an OCMS project to a PAIMANA project, the entity adopts the modern `ENT_PAIMANA_<project_id>` identifier, with the legacy OCMS ID logged in the provenance metadata.

---

## 7. Downstream Interface with Module 2C (Predictive Prototype)

By establishing rigorous identity resolution, the longitudinal panel provides clean, leakage-free trajectories for **Module 2C**:

1. **Entity-Level Trajectory Tracking:**
   For any entity $i$ observed at snapshots $t_1 \le t_2$:
   $$\Delta \text{Cost}_i = \text{revised\_cost}_i(t_2) - \text{revised\_cost}_i(t_1)$$
   $$\Delta \text{Slippage}_i = \text{revised\_doc}_i(t_2) - \text{revised\_doc}_i(t_1)$$
   $$\text{Progress Velocity}_i = \frac{\text{physical\_progress}_i(t_2) - \text{physical\_progress}_i(t_1)}{t_2 - t_1}$$
2. **Leakage Prevention:**
   Features for predicting risk at snapshot $t$ are computed strictly using observations timestamped $\tau \le t$. Outcomes and target labels are evaluated at $t + \Delta$ using confirmed longitudinal linkages.
3. **Auditability:**
   Every ML sample retains its `identity_resolution_tier`. High-risk or low-confidence linkages (`REVIEW_REQUIRED`, `UNMATCHED`) can be filtered out during sensitivity analysis to ensure ML evaluation is conducted strictly on gold-standard project trajectories.


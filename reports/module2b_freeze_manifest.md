# Module 2B — Final Promotion & Freeze Manifest

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 2B — Canonicalization & Longitudinal Panel Construction  
**Freeze Status:** **FROZEN / CERTIFIED**  
**Freeze Date:** September 5, 2026  
**Governance Authority:** Project Data Governance Board  

---

## 1. Executive Summary

This manifest formally certifies the promotion and freeze of the **Module 2B Project Identity Resolution and Longitudinal Snapshot Panel** artifacts into `data/processed/`.

All interim outputs have passed the Phase 3 Final QA Gate with zero defects, zero policy violations, 100% transitivity consistency, and byte-for-byte fidelity against the canonical observation layer.

---

## 2. Source Inputs & Checksums

The frozen outputs are deterministically derived from the following immutable source datasets:

| Dataset / File Description | Local Repository Path | Row Count | Official SHA-256 Checksum | Immutability Status |
|---|---|:---:|---|:---:|
| **June 2025 Table 7 Projects** | `data/processed/table7_june_2025_projects.csv` | 1,595 | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` | **FROZEN** |
| **July 2025 Table 4 Projects** | `data/processed/table4_july_2025_projects.csv` | 791 | `ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3` | **FROZEN** |
| **July 2026 Table 6 Projects** | `data/processed/table6_july_2026_projects.csv` | 1,775 | `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` | **FROZEN** |
| **Canonical Snapshot Layer** | `data/interim/canonical_snapshots.csv` | 4,161 | `0b9d2c919262f13290efda58ed7a21ab341e06616e11571c1ea702251c10a8b7` | **STAGED (UNMODIFIED)** |

---

## 3. Promoted & Frozen Artifacts

The following artifacts have been promoted from `data/interim/` to `data/processed/` with 100% byte-for-byte equality:

| Promoted Artifact | Destination Path | File Size | Row Count | Frozen SHA-256 Checksum | Companion Checksum File |
|---|---|:---:|:---:|---|---|
| **Project Identity Map** | `data/processed/project_identity_map.csv` | 972,051 bytes | 4,161 | `16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb` | `data/processed/project_identity_map.sha256` |
| **Project Snapshot Panel** | `data/processed/project_snapshot_panel.csv` | 2,318,183 bytes | 4,161 | `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47` | `data/processed/project_snapshot_panel.sha256` |

*Note: The interim copies (`data/interim/project_identity_map.csv` and `data/interim/project_snapshot_panel.csv`) remain completely intact and unchanged on disk for reproducible audit lineage.*

---

## 4. Dataset Statistics

| Metric | Certified Value | Notes / Description |
|---|:---:|---|
| **Total Canonical Observations** | **`4,161`** | Exact sum of June 2025 (1,595) + July 2025 (791) + July 2026 (1,775) |
| **Resolved Physical Projects** | **`3,633`** | Unique physical infrastructure project entities tracked |
| **3-Snapshot Trajectories** | **`47`** | Projects observed across all 3 snapshots (`2025-06 + 2025-07 + 2026-07`) |
| **2-Snapshot PAIMANA Trajectories (July-only)** | **`390`** | Projects observed in both July 2025 and July 2026 |
| **Total July 2025 ↔ July 2026 Trajectories** | **`437`** | All 12-month PAIMANA continuous entities ($390 + 47$) |
| **OCMS ↔ July 2026 Trajectories** | **`39`** | Projects observed in June 2025 and July 2026 |
| **OCMS ↔ July 2025 Trajectories** | **`5`** | Projects observed in June 2025 and July 2025 |
| **Single-Snapshot Projects** | **`3,152`** | 1,504 in June 2025; 349 in July 2025; 1,299 in July 2026 |
| **Same-Snapshot Key Collisions** | **`0`** | $|P \cap S| \le 1$ for all projects $P$ and snapshots $S$ |
| **Artificial / Imputed Observations** | **`0`** | Zero synthetic or interpolated rows created |

### Match Tier Distribution

| Confidence Tier | Matching Logic | Total Observations | Merged Physical Entities | Unmerged Observations |
|---|---|:---:|:---:|:---:|
| **`EXACT_ID`** | Identical PAIMANA ID + Multi-Attribute Corroboration | 872 | 436 paired entities | 0 |
| **`STRONG_MATCH`** | Strict Consensus (State, Agency, Date, Cost $\pm 5\%$, Overlap $\ge 0.85$) | 137 | 91 links into 46 PAIMANA projects | 0 |
| **`REVIEW_REQUIRED`**| Institutional/State Discrepancies Requiring Domain Review | 247 | 0 (Strictly unmerged) | 247 |
| **`UNMATCHED`** | No Candidate Meeting Conservative Thresholds | 2,905 | 0 (Strictly unmerged) | 2,905 |
| **Total** | | **4,161** | — | — |

---

## 5. Governance Principles & Invariants

This freeze adheres to the following non-negotiable data governance rules:

1. **No Synthetic Observations:** Every row in `project_snapshot_panel.csv` directly reflects a verified physical observation reported by MoSPI. Zero forward-fill or backward-fill records were synthesized.
2. **No Fabricated Identifiers:** Cross-reference identifiers (such as PMGID or legacy OCMS codes) were never fabricated when unpopulated in the source documents.
3. **No Blind Fuzzy Merging:** String similarity heuristics (Levenshtein distance, Jaro-Winkler, word embeddings) were strictly barred from autonomous entity resolution.
4. **No Manual Identity Edits:** Zero individual records or project keys were hand-edited. All identities result from deterministic algorithmic resolution.
5. **No Source Mutation:** Raw PDF documents and frozen processed tables were accessed in read-only mode and have not been altered.
6. **No Artificial Missing Snapshots:** Unmatched observations are retained as genuine point-in-time singletons rather than forcing artificial links.
7. **Prohibition on In-Place Modification:** The promoted files in `data/processed/` are frozen and permanent. Any future adjustments must occur in downstream derivation scripts.

---

## 6. Post-Promotion Verification Sign-off

- **Byte Equality Verification:** Passed (interim $\equiv$ processed, exact match)
- **SHA-256 Checksum Verification:** Passed (promoted files match pre-promotion hash)
- **Unit & Integration Regression Suite:** `61 / 61 PASS` (`python -m unittest discover -s tests -p "test_*.py"`)
- **Module 2B Final Status:** **FROZEN / COMPLETE**

\# Module 2B — Historical Source Inventory



\## Purpose



This document records the official historical project-monitoring sources

identified for construction of the PAIMANA longitudinal project panel.



Only verified sources will be acquired and incorporated into the dataset.



\---



\## Source Hierarchy



1\. Official PAIMANA Monthly Flash Reports

2\. Official MoSPI/IPMD Monthly Flash Reports

3\. Official legacy OCMS reports where required and schema-compatible



Third-party datasets are not authoritative model sources.



\---



\## Confirmed Historical Source



\### July 2025



\- Reporting period: July 2025

\- Source type: Monthly Flash Report

\- System/context: PAIMANA

\- Source domain: official MoSPI/IPMD

\- Project-level data: YES

\- Project identifiers: YES

\- Project cost fields: YES

\- Expenditure: YES

\- Physical progress: YES

\- Status: CANDIDATE FOR ACQUISITION



Source:



https://ipm.mospi.gov.in/Content/ArchiveReport/flash/2025-26/FlashReport\_July\_2025.pdf



\---



\## Current Validated Snapshot



\### July 2026



\- Reporting period: July 2026

\- Source type: Monthly Flash Report

\- Local source:

&#x20; `data/raw/flash\_reports/FlashReport\_July\_2026.pdf`

\- Source table: Table 6 — All Ongoing Projects

\- Project count: 1,775

\- Status: VALIDATED + FROZEN



\---



\## Historical Acquisition Window



Preferred target:



July 2025 → July 2026



This window contains approximately one year of potential monthly monitoring

history.



However, a month will only be included if an authentic official project-level

source is located and successfully validated.



Missing months will remain missing.



\---



\## Candidate Monthly Sources



| Reporting Period | Source Type | Official Source Located | Project-Level Data | Status |

|---|---|---|---|---|

| 2025-07 | Flash Report | YES | YES | CANDIDATE |

| 2025-08 | Flash Report | To verify | To verify | PENDING |

| 2025-09 | Flash Report | To verify | To verify | PENDING |

| 2025-10 | Flash Report | To verify | To verify | PENDING |

| 2025-11 | Flash Report | To verify | To verify | PENDING |

| 2025-12 | Flash Report | To verify | To verify | PENDING |

| 2026-01 | Flash Report | To verify | To verify | PENDING |

| 2026-02 | Flash Report | To verify | To verify | PENDING |

| 2026-03 | Flash Report | To verify | To verify | PENDING |

| 2026-04 | Flash Report | To verify | To verify | PENDING |

| 2026-05 | Flash Report | To verify | To verify | PENDING |

| 2026-06 | Flash Report | To verify | To verify | PENDING |

| 2026-07 | Flash Report | YES | YES | FROZEN |



\---



\## Important System Transition



Historical sources may originate from different monitoring-system versions.



Therefore:



\- PAIMANA-era reports must be identified separately.

\- Legacy OCMS reports must be identified separately.

\- Schema differences must be documented.

\- Project identifiers must be reconciled before merging.

\- No automatic assumption will be made that fields with similar names have

&#x20; identical definitions.



\---



\## Acquisition Rules



For every source that is acquired:



1\. Preserve the original file.

2\. Store it under `data/raw/flash\_reports/`.

3\. Do not modify the raw file.

4\. Record the source URL.

5\. Record the reporting period.

6\. Record the acquisition date.

7\. Generate a SHA-256 checksum.

8\. Record extraction status.

9\. Record validation status.

10\. Record any schema differences.



\---



\## Longitudinal Dataset Goal



The final structure should resemble:



project\_id | snapshot\_date | project attributes...



Example:



612786 | 2025-07 | ...

612786 | 2025-08 | ...

612786 | 2025-09 | ...

...

612786 | 2026-07 | ...



Only observations actually present in official sources will be included.



\---



\## Decision Rule



A historical report becomes part of the predictive dataset only after:



Official source

→ Raw preservation

→ Extraction

→ Structural validation

→ Semantic validation

→ Aggregate reconciliation

→ Project-ID validation

→ Snapshot freeze



\---



\## Current Status



Module 2B source inventory: IN PROGRESS



July 2026 baseline: VALIDATED + FROZEN



July 2025: OFFICIAL PROJECT-LEVEL SOURCE CONFIRMED



Remaining months: TO BE VERIFIED


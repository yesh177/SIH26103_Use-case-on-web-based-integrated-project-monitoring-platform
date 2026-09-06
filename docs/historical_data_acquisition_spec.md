\# Module 2B — Historical Data Acquisition Specification



\## 1. Purpose



Module 2B establishes the historical monthly project-monitoring dataset required

for longitudinal analysis and point-in-time predictive modelling.



The objective is to construct a project × reporting-period panel from authentic

MoSPI/PAIMANA/OCMS monitoring records.



No synthetic observations will be created for the final predictive dataset.



\---



\## 2. Core Dataset Structure



The target structure is:



project\_id × snapshot\_date



Each row represents one project's observed state at one reporting period.



Example:



| project\_id | snapshot\_date | project\_name | cost | expenditure | progress | completion\_date |

|---|---|---|---:|---:|---:|---|

| 612786 | 2026-05 | ... | ... | ... | ... | ... |

| 612786 | 2026-06 | ... | ... | ... | ... | ... |

| 612786 | 2026-07 | ... | ... | ... | ... | ... |



The model must only use information available at or before the corresponding

snapshot date.



\---



\## 3. Source Priority



Historical data will be acquired using the following priority:



1\. Official PAIMANA monthly Flash Reports

2\. Official MoSPI/IPMD monthly Flash Reports

3\. Official legacy OCMS reports where required and schema-compatible

4\. Other sources only when explicitly documented and independently validated



Unofficial datasets, scraped third-party datasets, generated data, and

unverified copies will not be used as authoritative model observations.



\---



\## 4. Historical Period



The preferred historical period begins with the earliest reliably obtainable

monthly project-level reports and continues through July 2026.



The exact usable period will be determined by actual source availability.



Missing months must remain missing.



The project will NOT fabricate or interpolate an entire monthly snapshot merely

to create a balanced panel.



\---



\## 5. Snapshot Rule



Every acquired report must represent a specific reporting period.



Each snapshot must contain:



\- reporting period

\- source file

\- source URL where available

\- source page/range where applicable

\- extraction method

\- extraction status

\- validation status



\---



\## 6. Canonical Project-Level Fields



The preferred canonical schema is:



\- snapshot\_date

\- source\_page

\- sl\_no

\- project\_id

\- project\_name

\- agency

\- legacy\_ocms\_code

\- pmgid

\- state

\- approval\_date

\- start\_date

\- original\_completion\_date

\- revised\_completion\_date

\- original\_cost\_crore

\- revised\_cost\_crore

\- cumulative\_expenditure\_crore

\- physical\_progress\_pct



Additional fields may be added when supported by authoritative sources.



Fields must never be populated by inference when the source does not provide

them.



\---



\## 7. Project Identity



`project\_id` is the primary longitudinal entity key.



The project ID must be validated before snapshots are merged.



Legacy identifiers such as:



\- Legacy OCMS Code

\- PMGID



must be retained separately and must not automatically replace `project\_id`.



If project identifiers change between systems, an explicit mapping must be

created and documented.



\---



\## 8. Raw Data Rules



Raw source files are immutable.



For every historical report:



1\. Preserve the original downloaded/copied file.

2\. Store it under `data/raw/`.

3\. Never edit the raw file.

4\. Record its provenance.

5\. Generate derived extraction artifacts separately.



\---



\## 9. Acquisition Manifest



Every source must be recorded in:



`data/raw/source\_manifest.csv`



Required tracking fields:



\- reporting\_period

\- source\_type

\- source\_name

\- source\_url

\- local\_filename

\- download\_status

\- extraction\_status

\- validation\_status

\- notes



Recommended additional fields:



\- acquisition\_date

\- source\_pages

\- schema\_version

\- sha256

\- provenance\_notes



\---



\## 10. Extraction Pipeline



Historical source processing follows:



```text

Official source

&#x20;     ↓

Raw source file

&#x20;     ↓

Source manifest

&#x20;     ↓

Table identification

&#x20;     ↓

Project-level extraction

&#x20;     ↓

Intermediate dataset

&#x20;     ↓

Structural validation

&#x20;     ↓

Semantic validation

&#x20;     ↓

Aggregate reconciliation

&#x20;     ↓

Validated processed snapshot


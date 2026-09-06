# Module 2A — June 2025 Flash Report Source Provenance & Inspection Report

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 2A — Flash Report Ingestion & Verification  
**Reporting Period:** June 2025 (`2025-06`)  
**Date:** September 2026  

---

## 1. Source Identification & Official Provenance

In strict accordance with project data governance, only primary official government sources are used. Unofficial mirrors, synthetic datasets, and third-party aggregators are prohibited.

### 1.1 Official Government Authority
- **Publishing Entity**: Ministry of Statistics and Programme Implementation (MoSPI), Government of India
- **Division**: Infrastructure and Project Monitoring Division (IPMD)
- **Official Publication Archive URL**:
  `https://www.mospi.gov.in/sites/default/files/publication_reports/FR_JUNE_2025.pdf`
- **Secondary / Legacy Portal URL**:
  `https://ipm.mospi.gov.in/Content/ArchiveReport/flash/2025-26/FlashReport_June_2025.pdf`

### 1.2 Local File Integrity & Verification
- **Local File Path**: `data/raw/flash_reports/FlashReport_June_2025.pdf`
- **File Existence**: Verified on disk
- **File Size**: `14,003,041` bytes (~13.35 MB)
- **SHA256 Checksum**: `7f37c63abe9f92d8db6513ad68d91b5c172c9c27454f45691f53fff7ebb2a754`
- **PyMuPDF Verification**: Opened successfully with `import pymupdf`
- **Total PDF Pages**: `234` pages

### 1.3 Document Metadata
- **Format**: PDF 1.6
- **Title**: `SECTOR_WISE.xlsx`
- **Author**: `Mospi`
- **Creator**: `PScript5.dll Version 5.2.2`
- **Producer**: `Acrobat Distiller 19.0 (Windows)`
- **Creation Date**: `D:20250710170911+05'30'` (July 10, 2025)
- **Modification Date**: `D:20250711164722+05'30'` (July 11, 2025)
- **Encryption**: None

---

## 2. System Transition Context (OCMS-2006 to PAIMANA)

The physical inspection of `FlashReport_June_2025.pdf` confirms the operational transition between legacy OCMS-2006 and the web-based PAIMANA platform:

1. **Legacy OCMS Reporting System**: June 2025 represents the final monthly monitoring cycle under the legacy **OCMS-2006** reporting system before PAIMANA took effect.
2. **Project Universe Size**: June 2025 covers **1,595 ongoing central sector projects** (Rs. 150 Crore and above), as confirmed in Table 1 Overview (page 8) and Table 7. In July 2025 (PAIMANA Report No. 477), Table 4 contained **791 ongoing projects**.
3. **Report Generation Origin**: The metadata title `SECTOR_WISE.xlsx` generated via `PScript5.dll` / `Acrobat Distiller` reflects the legacy Excel-to-PostScript batch compilation used by OCMS, contrasting with the direct web-rendered reports introduced under PAIMANA.

---

## 3. Table Identification: "All Ongoing Projects"

From the Table of Contents (PDF page 2) and full document scan:
- **Table Number**: `Table:-7`
- **Official Table Title**: `Table:-7. Project List: Ongoing Projects as of 30th June 2025`
- **PDF Page Range**: **Page 41 through Page 229** inclusive (189 pages total)
- **Printed Page Numbers**: Pages 37 through 225 (PDF page index = printed page index + 4)
- **Expected Projects**: **1,595** projects (Serial numbers 1 through 1595, continuous, matching Table 1 Sector-wise Overview Total of 1,595)

---

## 4. Header & Column Layout Inspection

The table headers spanning PDF pages 41–229 consist of a 9-zone layout:

| Zone / Column Header | Observed Source Header | Coordinates / Position | Source Representation |
|---|---|---|---|
| Col 1 | `State` | x ~ 16–70 pt | Grouped hierarchy header; prints state name once; applies downwards |
| Col 2 | `Sector` | x ~ 79–140 pt | Grouped hierarchy header; prints sector name once; applies downwards |
| Col 3 | `Sl No` | x ~ 140–165 pt | Integer serial (1 to 1595) |
| Col 4 | `Project Name`<br>`(Agency Name)`<br>`(Project Code)` | x ~ 144–295 pt | Multi-line text block:<br>- Line(s): Project Name<br>- Line: `(Agency )`<br>- Line: `(ProjectCode )` (e.g., `(N04000073 )`) |
| Col 5 | `Date of Approval (MM/YYYY)` | x ~ 296–335 pt | Date format `M-YYYY` or `MM-YYYY` (e.g., `10-2013`, `3-2019`) |
| Col 6 | `Date of Commissioning`<br>`Original`<br>`(Revised)`<br>`{Anticipated}`<br>`(MM/YYYY)` | x ~ 340–415 pt | Multi-tier commissioning date:<br>- Original: `M/YYYY`<br>- Revised: `(Mon-YYYY)` or `(N.A.)`<br>- Anticipated: `{M/YYYY}` or `{N.A.}` |
| Col 7 | `Cost Original`<br>`(Revised)`<br>`{Anticipated}`<br>`in Rs. Crore` | x ~ 430–485 pt | Multi-tier cost in Rs. Crore:<br>- Original: numeric string<br>- Revised: `(...)` or `(N.A.)`<br>- Anticipated: `{...}` |
| Col 8 | `Cumulative Expenditure in Rs. Crore` | x ~ 505–550 pt | Numeric decimal string (e.g., `698.80`, `0.00`) |
| Col 9 | `Physical Progress (%)` | x ~ 560–595 pt | Numeric decimal string (e.g., `100.00`, `5.23`) or `-` |

---

## 5. Representative Project Rows

### Row 1 (PDF Page 41)
- **State**: `ANDAMAN AND NICOBAR ISLANDS`
- **Sector**: `CIVIL AVIATION`
- **Sl No**: `1`
- **Project Name**: `CONSTRUCTION OF NEW INTEGRATED TERMINAL BUILDING AT VSI AIRPORT, PORTBLAIR`
- **Agency**: `AAI`
- **Project Code / ID**: `N04000073`
- **Date of Approval**: `10-2013`
- **Commissioning Date**:
  - Original: `9/2018`
  - Revised: `Jun-2023`
  - Anticipated: `6/2023`
- **Cost (Rs. Crore)**:
  - Original: `417.23`
  - Revised: `707.73`
  - Anticipated: `707.73`
- **Cumulative Expenditure (Rs. Crore)**: `698.80`
- **Physical Progress (%)**: `100.00`

### Row 2 (PDF Page 41)
- **State**: `ANDAMAN AND NICOBAR ISLANDS` (propagated from state block)
- **Sector**: `RAILWAYS`
- **Sl No**: `2`
- **Project Name**: `LUDHIANA KILA RAIPUR (19 KMS) WITH FREIGHT LINE AT GILL STATION ON LDH-JHL SECTION`
- **Agency**: `NR`
- **Project Code / ID**: `N22000584`
- **Date of Approval**: `3-2019`
- **Commissioning Date**:
  - Original: `3/2025`
  - Revised: `Aug-2025`
  - Anticipated: `3/2026`
- **Cost (Rs. Crore)**:
  - Original: `235.72`
  - Revised: `N.A.`
  - Anticipated: `235.72`
- **Cumulative Expenditure (Rs. Crore)**: `59.78`
- **Physical Progress (%)**: `55.00`

### Row 3 (PDF Page 41)
- **State**: `ANDAMAN AND NICOBAR ISLANDS` (propagated)
- **Sector**: `ROAD TRANSPORT AND HIGHWAYS`
- **Sl No**: `3`
- **Project Name**: `MAJOR BRIDGE OVER MIDDLE STRAIT CREEK`
- **Agency**: `NHIDCL`
- **Project Code / ID**: `N24002207`
- **Date of Approval**: `12-2024`
- **Commissioning Date**: Original: `2/2026`, Revised: `N.A.`, Anticipated: `2/2026`
- **Cost (Rs. Crore)**: Original: `371.80`, Revised: `207.99`, Anticipated: `207.99`
- **Cumulative Expenditure (Rs. Crore)**: `0.00`
- **Physical Progress (%)**: `5.23`

---

## 6. Schema Comparison: June 2025 vs. July 2025 Canonical

| Dimension / Field | July 2025 (PAIMANA) | June 2025 (Legacy OCMS) | Alignment & Handling Notes |
|---|---|---|---|
| **Table Number** | Table 4 (`All Ongoing Projects`) | Table 7 (`Ongoing Projects as of 30th June 2025`) | June extractor must target Table 7 across PDF pp. 41–229 |
| **Total Projects** | 791 (Serials 1–791) | 1,595 (Serials 1–1595) | Expected row count is 1,595; verified against Table 1 total |
| **PDF Page Range** | 37–66 (30 pages) | 41–229 (189 pages) | Scale is ~6.3x larger due to higher project universe |
| **`snapshot_date`** | `2025-07-31` | `2025-06-30` | Explicit constant for month |
| **`source_page`** | 37 to 66 | 41 to 229 | Preserves source PDF page number |
| **`sl_no`** | 1 to 791 | 1 to 1595 | Consecutive integer serial |
| **`project_id`** | e.g. `N04000073` | e.g. `N04000073` | Sourced from `(Project Code)` line |
| **`project_name`** | Multi-line text | Multi-line text | Clean multiline project description |
| **`agency`** | e.g. `AAI` | e.g. `AAI` | Sourced from `(Agency )` line |
| **`state`** | Explicit column per row | Leftmost hierarchical grouping column | Must propagate state downwards until next state encountered |
| **`sector`** | Not separate column in Table 4 | Second hierarchical column | Available in June 2025 source; can be retained or mapped |
| **`approval_date`** | `MM/YYYY` | `MM-YYYY` or `M-YYYY` | Sourced from approval date column |
| **`original_completion_date`** | Original commissioning | Original commissioning | Direct equivalent |
| **`revised_completion_date`** | Revised commissioning | Revised `(...)` / Anticipated `{...}` | June has both Revised and Anticipated dates |
| **`original_cost_crore`** | Original cost | Original cost | Direct equivalent |
| **`revised_cost_crore`** | Revised cost | Revised `(...)` / Anticipated `{...}` | June has both Revised and Anticipated costs |
| **`cumulative_expenditure_crore`** | Numeric decimal | Numeric decimal | Direct equivalent |
| **`physical_progress_pct`** | Numeric decimal | Numeric decimal | Direct equivalent |

---

## 7. Operational Status & Manifest Record

- **Source Manifest Status**: `ACQUIRED` (updated in `data/raw/source_manifest.csv`)
- **Extraction Status**: `PENDING` (awaiting explicit user instruction)
- **Validation Status**: `PENDING`
- **July 2025 & July 2026 Integrity**: Unaltered and preserved.

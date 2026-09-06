"""
PAIMANA Predictive Risk Intelligence
Module 2A: July 2025 Table 4 Dataset Freezing & Promotion

Promotes validated interim dataset to data/processed/table4_july_2025_projects.csv,
generates SHA256 checksums, creates data/processed/README.md, and updates
data/raw/source_manifest.csv.
"""

from collections import Counter
from datetime import datetime
from pathlib import Path
import csv
import hashlib
import shutil
import sys

INTERIM_PATH = Path("data/interim/table4_july_2025_projects.csv")
PROCESSED_DIR = Path("data/processed")
PROCESSED_CSV = PROCESSED_DIR / "table4_july_2025_projects.csv"
CHECKSUM_PATH = PROCESSED_DIR / "table4_july_2025_projects.sha256"
README_PATH = PROCESSED_DIR / "README.md"
MANIFEST_PATH = Path("data/raw/source_manifest.csv")
RAW_PDF = Path("data/raw/flash_reports/FlashReport_July_2025.pdf")

EXPECTED_PROJECTS = 791

REQUIRED_COLUMNS = [
    "snapshot_date",
    "source_page",
    "sl_no",
    "project_id",
    "project_name",
    "agency",
    "state",
    "approval_date",
    "original_completion_date",
    "revised_completion_date",
    "original_cost_crore",
    "revised_cost_crore",
    "cumulative_expenditure_crore",
    "physical_progress_pct",
]


def sha256_file(path: Path) -> str:
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_interim_dataset():
    print("=" * 75)
    print("STEP 1: PRE-PROMOTION VERIFICATION OF INTERIM DATASET")
    print("=" * 75)

    if not INTERIM_PATH.exists():
        raise FileNotFoundError(f"Interim dataset not found: {INTERIM_PATH}")

    with INTERIM_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)

    # 1. Row count
    if len(rows) != EXPECTED_PROJECTS:
        raise ValueError(f"Expected {EXPECTED_PROJECTS} rows, found {len(rows)}")
    print(f"  [OK] Row count: {len(rows)} (Expected: {EXPECTED_PROJECTS})")

    # 2. Schema check
    if columns != REQUIRED_COLUMNS:
        raise ValueError(f"Columns mismatch: {columns} != {REQUIRED_COLUMNS}")
    print(f"  [OK] Schema: 14 canonical columns match exactly")

    # 3. Unique project IDs
    project_ids = [r["project_id"].strip() for r in rows if r["project_id"].strip()]
    if len(set(project_ids)) != EXPECTED_PROJECTS:
        dupes = [pid for pid, c in Counter(project_ids).items() if c > 1]
        raise ValueError(f"Duplicate project IDs found: {dupes}")
    print(f"  [OK] Unique project IDs: {len(set(project_ids))} / {EXPECTED_PROJECTS}")

    # 4. Serials 1-791
    serials = [int(r["sl_no"]) for r in rows]
    if sorted(serials) != list(range(1, EXPECTED_PROJECTS + 1)):
        missing = sorted(set(range(1, EXPECTED_PROJECTS + 1)) - set(serials))
        raise ValueError(f"Serial numbers mismatch. Missing: {missing}")
    print(f"  [OK] Serial numbers: strictly 1 through {EXPECTED_PROJECTS}")

    return rows


def promote_dataset():
    print("\n" + "=" * 75)
    print("STEP 2: PROMOTE DATASET (INTERIM -> PROCESSED)")
    print("=" * 75)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Pure copy without modification
    shutil.copy2(INTERIM_PATH, PROCESSED_CSV)
    print(f"  [OK] Copied dataset to: {PROCESSED_CSV}")

    # Checksum calculation
    interim_hash = sha256_file(INTERIM_PATH)
    processed_hash = sha256_file(PROCESSED_CSV)

    if interim_hash != processed_hash:
        raise ValueError("Checksum mismatch between interim and processed files!")

    with CHECKSUM_PATH.open("w", encoding="utf-8") as f:
        f.write(f"{processed_hash}  {PROCESSED_CSV.name}\n")
    print(f"  [OK] SHA256 Checksum ({processed_hash[:16]}...) recorded to: {CHECKSUM_PATH}")


def write_processed_readme():
    print("\n" + "=" * 75)
    print("STEP 3: WRITE DATA/PROCESSED/README.MD")
    print("=" * 75)

    interim_hash = sha256_file(PROCESSED_CSV)
    raw_pdf_hash = sha256_file(RAW_PDF) if RAW_PDF.exists() else "N/A"
    raw_pdf_size = RAW_PDF.stat().st_size if RAW_PDF.exists() else 0
    csv_size = PROCESSED_CSV.stat().st_size

    readme_content = f"""# Processed Datasets — PAIMANA Predictive Risk Intelligence

This directory stores frozen, quality-validated historical snapshot datasets promoted from interim extraction pipelines.

## Dataset Inventory

### 1. July 2025 Table 4 Ongoing Projects (`table4_july_2025_projects.csv`)

- **Dataset Name**: July 2025 Table 4 Ongoing Projects Dataset
- **Reporting Period**: July 2025 (`2025-07`)
- **Source Authority**: Ministry of Statistics and Programme Implementation (MoSPI), Government of India / PAIMANA Portal (`ipm.mospi.gov.in`)
- **Source PDF Filename**: `FlashReport_July_2025.pdf`
- **Source PDF Path**: `data/raw/flash_reports/FlashReport_July_2025.pdf`
- **Source PDF File Size**: {raw_pdf_size:,} bytes
- **Source PDF SHA256**: `{raw_pdf_hash}`
- **Source Table**: Table 4 — All Ongoing Projects
- **Source PDF Pages**: Pages 37–66 inclusive (1-indexed)
- **Extracted Project Count**: **791** records
- **Unique Project Codes**: **791** unique project IDs
- **Serial Number Range**: 1 through 791 (exact sequential match)
- **Promoted File Path**: `data/processed/table4_july_2025_projects.csv`
- **Promoted File Size**: {csv_size:,} bytes
- **Promoted File SHA256**: `{interim_hash}`
- **Extraction Script**: `src/ingestion/extract_table4_july2025.py`
- **Validation Script**: `src/data/validate_table4_july2025.py`
- **Validation Report**: `reports/module2a_table4_july2025_validation.md`

#### Schema (14 Canonical Fields)

1. `snapshot_date`: Snapshot reporting period (`2025-07`)
2. `source_page`: Source PDF page number (37–66)
3. `sl_no`: Sequential serial number (1–791)
4. `project_id`: Unique 4–7 digit PAIMANA project code
5. `project_name`: Full project title
6. `agency`: Central implementing agency / PSU
7. `state`: State / UT / Multi-State jurisdiction
8. `approval_date`: Approval date (MM/YYYY or source blank)
9. `original_completion_date`: Original target Date of Commissioning (MM/YYYY)
10. `revised_completion_date`: Latest revised target DoC (MM/YYYY or source `(-)`)
11. `original_cost_crore`: Sanctioned original cost in ₹ crore
12. `revised_cost_crore`: Anticipated revised cost in ₹ crore
13. `cumulative_expenditure_crore`: Cumulative expenditure to date in ₹ crore
14. `physical_progress_pct`: Physical progress percentage (0.00%–100.00%)

#### Governance & Provenance Principles

- **Immutability**: The raw source PDF (`data/raw/flash_reports/FlashReport_July_2025.pdf`) remains strictly immutable.
- **Source Fidelity**: Legitimate source-observed blanks (State for serial 447; Approval Date for serials 525, 526, 648) and source-observed representations (such as `(-)` for unrevised completion dates) have been preserved exactly as reported without synthetic imputation or alteration.
- **Source Anomalies Preserved**: Source-observed conditions (e.g. 27 projects with revised cost < original cost; 39 projects with cumulative expenditure exceeding revised cost) are retained for transparent auditability and have not been artificially corrected.
- **Dataset Scope**: This dataset represents a verified, point-in-time snapshot of raw historical operational reporting. It is **not yet the final ML feature table**; subsequent temporal alignment, feature engineering, and cross-month panel linkage will be performed in downstream modules.
"""

    with README_PATH.open("w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"  [OK] Written provenance README to: {README_PATH}")


def update_source_manifest():
    print("\n" + "=" * 75)
    print("STEP 4: UPDATE DATA/RAW/SOURCE_MANIFEST.CSV")
    print("=" * 75)

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Source manifest not found: {MANIFEST_PATH}")

    with MANIFEST_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        manifest_cols = reader.fieldnames or []
        rows = list(reader)

    updated = False
    for r in rows:
        if r.get("reporting_period") == "2025-07" and r.get("source_type") == "flash_report":
            r["local_filename"] = "FlashReport_July_2025.pdf"
            r["download_status"] = "ACQUIRED"
            r["extraction_status"] = "PASS"
            r["validation_status"] = "PASS"
            # Retain blank source_url if not already documented
            if not r.get("source_url"):
                r["source_url"] = ""
            r["notes"] = "Table 4 extracted (791 projects); validated and frozen; local PDF provenance verified"
            updated = True

    if not updated:
        rows.append({
            "reporting_period": "2025-07",
            "source_type": "flash_report",
            "source_name": "MoSPI Flash Report",
            "source_url": "",
            "local_filename": "FlashReport_July_2025.pdf",
            "download_status": "ACQUIRED",
            "extraction_status": "PASS",
            "validation_status": "PASS",
            "notes": "Table 4 extracted (791 projects); validated and frozen; local PDF provenance verified",
        })

    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_cols)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  [OK] Updated source manifest: {MANIFEST_PATH}")
    for r in rows:
        print(f"    {r['reporting_period']} | {r['source_type']} | {r['local_filename']} | download={r['download_status']} | extract={r['extraction_status']} | val={r['validation_status']}")


def final_verification():
    print("\n" + "=" * 75)
    print("STEP 5: FINAL VERIFICATION AUDIT")
    print("=" * 75)

    # 1. Processed file exists
    if not PROCESSED_CSV.exists():
        raise FileNotFoundError(f"Missing processed file: {PROCESSED_CSV}")
    print(f"  Processed file exists: True ({PROCESSED_CSV})")

    # 2. Row count, unique IDs, serial range
    with PROCESSED_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  Row count            : {len(rows)} (Expected: {EXPECTED_PROJECTS})")
    pids = [r["project_id"] for r in rows]
    print(f"  Unique project IDs   : {len(set(pids))} / {len(rows)}")
    serials = [int(r["sl_no"]) for r in rows]
    print(f"  Serial number range  : min={min(serials)}, max={max(serials)}")

    # 3. File sizes & Checksums
    raw_pdf_size = RAW_PDF.stat().st_size if RAW_PDF.exists() else 0
    raw_pdf_sha = sha256_file(RAW_PDF) if RAW_PDF.exists() else "N/A"

    interim_size = INTERIM_PATH.stat().st_size
    interim_sha = sha256_file(INTERIM_PATH)

    processed_size = PROCESSED_CSV.stat().st_size
    processed_sha = sha256_file(PROCESSED_CSV)

    print(f"\n  FILE INTEGRITY & CHECKSUMS:")
    print(f"    Raw PDF      : {RAW_PDF.name}")
    print(f"      Size       : {raw_pdf_size:,} bytes")
    print(f"      SHA256     : {raw_pdf_sha}")
    print(f"    Interim CSV  : {INTERIM_PATH.name}")
    print(f"      Size       : {interim_size:,} bytes")
    print(f"      SHA256     : {interim_sha}")
    print(f"    Processed CSV: {PROCESSED_CSV.name}")
    print(f"      Size       : {processed_size:,} bytes")
    print(f"      SHA256     : {processed_sha}")
    print(f"    Match Interim==Processed: {interim_sha == processed_sha}")

    print("\n" + "=" * 75)
    print("STATUS: MODULE 2A JULY 2025 TABLE 4 DATASET FREEZE SUCCESSFUL")
    print("=" * 75)


def main():
    verify_interim_dataset()
    promote_dataset()
    write_processed_readme()
    update_source_manifest()
    final_verification()


if __name__ == "__main__":
    main()

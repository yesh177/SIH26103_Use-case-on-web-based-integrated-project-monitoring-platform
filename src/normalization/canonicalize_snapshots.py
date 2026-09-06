"""
PAIMANA Predictive Risk Intelligence
Module 2B: Phase 2 — Canonical Snapshot Construction

Harmonizes the three frozen historical MoSPI/PAIMANA snapshots:
1. June 2025 Table 7 (1,595 records)
2. July 2025 Table 4 (791 records)
3. July 2026 Table 6 (1,775 records)

Total canonical observations: 4,161 records.
Outputs: data/interim/canonical_snapshots.csv
"""

from pathlib import Path
import csv
import hashlib
import json
import re
import sys

# Frozen input paths
JUNE_2025_PATH = Path("data/processed/table7_june_2025_projects.csv")
JUNE_2025_SHA = Path("data/processed/table7_june_2025_projects.sha256")

JULY_2025_PATH = Path("data/processed/table4_july_2025_projects.csv")
JULY_2025_SHA = Path("data/processed/table4_july_2025_projects.sha256")

JULY_2026_PATH = Path("data/processed/table6_july_2026_projects.csv")
JULY_2026_SHA = Path("data/processed/table6_july_2026_projects.sha256")

OUTPUT_PATH = Path("data/interim/canonical_snapshots.csv")

CANONICAL_COLUMNS = [
    # IDENTITY (8)
    "canonical_observation_key",
    "source_snapshot",
    "snapshot_date",
    "source_table",
    "source_project_id",
    "project_name",
    "agency",
    "state",
    # DATES (10)
    "approval_date_raw",
    "approval_date",
    "start_date_raw",
    "start_date",
    "original_completion_date_raw",
    "original_completion_date",
    "revised_completion_date_raw",
    "revised_completion_date",
    "anticipated_completion_date_raw",
    "anticipated_completion_date",
    # FINANCIAL (4)
    "original_cost_crore",
    "revised_cost_crore",
    "anticipated_cost_crore",
    "cumulative_expenditure_crore",
    # PROGRESS (1)
    "physical_progress_pct",
    # PROVENANCE (4)
    "source_page",
    "source_row",
    "source_file",
    "source_record_hash",
    # SOURCE-SPECIFIC (3)
    "sector",
    "legacy_ocms_code",
    "pmgid",
]

MONTH_NAMES = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
    "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
    "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}


def sha256_file(path: Path) -> str:
    """Compute SHA256 of a file in 1MB chunks."""
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def compute_source_record_hash(row_dict: dict) -> str:
    """
    Calculate deterministic SHA-256 hash of a source row dictionary.
    Method: JSON serialization with sorted keys and UTF-8 encoding.
    """
    payload = json.dumps(row_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_date(val: str) -> str:
    """
    Normalize date strings into ISO YYYY-MM representation.
    Does NOT invent day-level precision when only month/year is given.
    Returns empty string for unpopulated/missing values.
    """
    if not val:
        return ""
    s = val.strip()
    if s.upper() in ["NA", "N.A.", "-", "", "(-)", "(-) (-)", "{}", "{ }"]:
        return ""

    # YYYY-MM-DD -> YYYY-MM
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    # YYYY-MM
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if m:
        return s

    # MM/YYYY or M/YYYY
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", s)
    if m:
        month = int(m.group(1))
        year = m.group(2)
        if 1 <= month <= 12:
            return f"{year}-{month:02d}"

    # MM-YYYY or M-YYYY
    m = re.fullmatch(r"(\d{1,2})-(\d{4})", s)
    if m:
        month = int(m.group(1))
        year = m.group(2)
        if 1 <= month <= 12:
            return f"{year}-{month:02d}"

    # Mon-YYYY (e.g. Jun-2023)
    m = re.fullmatch(r"([A-Za-z]{3})-(\d{4})", s)
    if m:
        mon_str = m.group(1).upper()
        year = m.group(2)
        if mon_str in MONTH_NAMES:
            return f"{year}-{MONTH_NAMES[mon_str]}"

    raise ValueError(f"Unrecognized date format cannot be normalized: '{s}'")


def verify_frozen_inputs():
    """Verify presence and SHA256 checksums of all 3 frozen inputs."""
    print("=" * 75)
    print("STEP 1: VERIFYING FROZEN INPUT INTEGRITY")
    print("=" * 75)

    pairs = [
        ("June 2025 Table 7", JUNE_2025_PATH, JUNE_2025_SHA),
        ("July 2025 Table 4", JULY_2025_PATH, JULY_2025_SHA),
        ("July 2026 Table 6", JULY_2026_PATH, JULY_2026_SHA),
    ]

    for label, csv_path, sha_path in pairs:
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing frozen dataset: {csv_path}")
        if not sha_path.exists():
            raise FileNotFoundError(f"Missing checksum file: {sha_path}")

        expected_hash = sha_path.read_text(encoding="utf-8").split()[0].strip()
        actual_hash = sha256_file(csv_path)

        if actual_hash != expected_hash:
            raise ValueError(
                f"INTEGRITY VIOLATION on {label}!\n"
                f"Expected: {expected_hash}\n"
                f"Actual:   {actual_hash}"
            )
        print(f"  [OK] {label:<20} SHA256: {actual_hash}")


def transform_june_2025(rows: list) -> list:
    """Transform June 2025 Table 7 (1,595 records) to canonical schema."""
    canonical_rows = []
    for r in rows:
        proj_id = r["project_id"].strip()
        record_hash = compute_source_record_hash(r)
        canonical_rows.append({
            "canonical_observation_key": f"2025-06:Table 7:{proj_id}",
            "source_snapshot": "2025-06",
            "snapshot_date": "2025-06-30",
            "source_table": "Table 7",
            "source_project_id": proj_id,
            "project_name": r["project_name"].strip(),
            "agency": r["agency"].strip(),
            "state": r["state"].strip(),
            "approval_date_raw": r["approval_date"].strip(),
            "approval_date": normalize_date(r["approval_date"]),
            "start_date_raw": "",
            "start_date": "",
            "original_completion_date_raw": r["original_completion_date"].strip(),
            "original_completion_date": normalize_date(r["original_completion_date"]),
            "revised_completion_date_raw": r["revised_completion_date"].strip(),
            "revised_completion_date": normalize_date(r["revised_completion_date"]),
            "anticipated_completion_date_raw": r["anticipated_completion_date"].strip(),
            "anticipated_completion_date": normalize_date(r["anticipated_completion_date"]),
            "original_cost_crore": r["original_cost_crore"].strip(),
            "revised_cost_crore": r["revised_cost_crore"].strip(),
            "anticipated_cost_crore": r["anticipated_cost_crore"].strip(),
            "cumulative_expenditure_crore": r["cumulative_expenditure_crore"].strip(),
            "physical_progress_pct": r["physical_progress_pct"].strip(),
            "source_page": r["source_page"].strip(),
            "source_row": r["sl_no"].strip(),
            "source_file": "FlashReport_June_2025.pdf",
            "source_record_hash": record_hash,
            "sector": r["sector"].strip(),
            "legacy_ocms_code": "",
            "pmgid": "",
        })
    return canonical_rows


def transform_july_2025(rows: list) -> list:
    """Transform July 2025 Table 4 (791 records) to canonical schema."""
    canonical_rows = []
    for r in rows:
        proj_id = r["project_id"].strip()
        record_hash = compute_source_record_hash(r)
        canonical_rows.append({
            "canonical_observation_key": f"2025-07:Table 4:{proj_id}",
            "source_snapshot": "2025-07",
            "snapshot_date": "2025-07-31",
            "source_table": "Table 4",
            "source_project_id": proj_id,
            "project_name": r["project_name"].strip(),
            "agency": r["agency"].strip(),
            "state": r["state"].strip(),
            "approval_date_raw": r["approval_date"].strip(),
            "approval_date": normalize_date(r["approval_date"]),
            "start_date_raw": "",
            "start_date": "",
            "original_completion_date_raw": r["original_completion_date"].strip(),
            "original_completion_date": normalize_date(r["original_completion_date"]),
            "revised_completion_date_raw": r["revised_completion_date"].strip(),
            "revised_completion_date": normalize_date(r["revised_completion_date"]),
            "anticipated_completion_date_raw": "",
            "anticipated_completion_date": "",
            "original_cost_crore": r["original_cost_crore"].strip(),
            "revised_cost_crore": r["revised_cost_crore"].strip(),
            "anticipated_cost_crore": "",
            "cumulative_expenditure_crore": r["cumulative_expenditure_crore"].strip(),
            "physical_progress_pct": r["physical_progress_pct"].strip(),
            "source_page": r["source_page"].strip(),
            "source_row": r["sl_no"].strip(),
            "source_file": "FlashReport_July_2025.pdf",
            "source_record_hash": record_hash,
            "sector": "",
            "legacy_ocms_code": "",
            "pmgid": "",
        })
    return canonical_rows


def transform_july_2026(rows: list) -> list:
    """Transform July 2026 Table 6 (1,775 records) to canonical schema."""
    canonical_rows = []
    for r in rows:
        proj_id = r["project_id"].strip()
        record_hash = compute_source_record_hash(r)
        canonical_rows.append({
            "canonical_observation_key": f"2026-07:Table 6:{proj_id}",
            "source_snapshot": "2026-07",
            "snapshot_date": "2026-07-31",
            "source_table": "Table 6",
            "source_project_id": proj_id,
            "project_name": r["project_name"].strip(),
            "agency": r["agency"].strip(),
            "state": r["state"].strip(),
            "approval_date_raw": r["approval_date"].strip(),
            "approval_date": normalize_date(r["approval_date"]),
            "start_date_raw": r["start_date"].strip(),
            "start_date": normalize_date(r["start_date"]),
            "original_completion_date_raw": r["original_completion_date"].strip(),
            "original_completion_date": normalize_date(r["original_completion_date"]),
            "revised_completion_date_raw": r["revised_completion_date"].strip(),
            "revised_completion_date": normalize_date(r["revised_completion_date"]),
            "anticipated_completion_date_raw": "",
            "anticipated_completion_date": "",
            "original_cost_crore": r["original_cost_crore"].strip(),
            "revised_cost_crore": r["revised_cost_crore"].strip(),
            "anticipated_cost_crore": "",
            "cumulative_expenditure_crore": r["cumulative_expenditure_crore"].strip(),
            "physical_progress_pct": r["physical_progress_pct"].strip(),
            "source_page": r["source_page"].strip(),
            "source_row": r["sl_no"].strip(),
            "source_file": "FlashReport_July_2026.pdf",
            "source_record_hash": record_hash,
            "sector": "",
            "legacy_ocms_code": r["legacy_ocms_code"].strip(),
            "pmgid": r["pmgid"].strip(),
        })
    return canonical_rows


def build_canonical_snapshots():
    """Execute end-to-end canonical snapshot construction pipeline."""
    verify_frozen_inputs()

    print()
    print("=" * 75)
    print("STEP 2: HARMONIZING SNAPSHOTS INTO CANONICAL SCHEMA")
    print("=" * 75)

    with JUNE_2025_PATH.open(encoding="utf-8", newline="") as f:
        june_rows = list(csv.DictReader(f))
    if len(june_rows) != 1595:
        raise ValueError(f"Expected 1,595 June 2025 rows, found {len(june_rows)}")
    canon_june = transform_june_2025(june_rows)
    print(f"  [OK] June 2025 Table 7 harmonized: {len(canon_june)} records")

    with JULY_2025_PATH.open(encoding="utf-8", newline="") as f:
        july25_rows = list(csv.DictReader(f))
    if len(july25_rows) != 791:
        raise ValueError(f"Expected 791 July 2025 rows, found {len(july25_rows)}")
    canon_july25 = transform_july_2025(july25_rows)
    print(f"  [OK] July 2025 Table 4 harmonized: {len(canon_july25)} records")

    with JULY_2026_PATH.open(encoding="utf-8", newline="") as f:
        july26_rows = list(csv.DictReader(f))
    if len(july26_rows) != 1775:
        raise ValueError(f"Expected 1,775 July 2026 rows, found {len(july26_rows)}")
    canon_july26 = transform_july_2026(july26_rows)
    print(f"  [OK] July 2026 Table 6 harmonized: {len(canon_july26)} records")

    all_records = canon_june + canon_july25 + canon_july26
    total_records = len(all_records)
    if total_records != 4161:
        raise ValueError(f"Expected 4,161 total records, found {total_records}")
    print(f"  [OK] Total harmonized observations: {total_records} (1,595 + 791 + 1,775)")

    # Deterministic sorting
    print()
    print("=" * 75)
    print("STEP 3: DETERMINISTIC SORTING & INTEGRITY CHECKS")
    print("=" * 75)
    sorted_records = sorted(
        all_records,
        key=lambda x: (x["source_snapshot"], x["source_table"], int(x["source_row"]))
    )

    # Observation key uniqueness
    keys = [r["canonical_observation_key"] for r in sorted_records]
    if len(set(keys)) != total_records:
        raise ValueError(f"Duplicate canonical_observation_key detected! {total_records - len(set(keys))} duplicates")
    print(f"  [OK] canonical_observation_key uniqueness: {len(set(keys))} / {total_records} (100% unique)")

    # Save to data/interim/canonical_snapshots.csv
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(sorted_records)

    output_sha256 = sha256_file(OUTPUT_PATH)
    file_size = OUTPUT_PATH.stat().st_size

    print()
    print("=" * 75)
    print("CANONICAL SNAPSHOT DATASET SUCCESSFULLY CREATED")
    print("=" * 75)
    print(f"  Output Path:   {OUTPUT_PATH}")
    print(f"  Total Rows:    {total_records}")
    print(f"  Total Columns: {len(CANONICAL_COLUMNS)}")
    print(f"  File Size:     {file_size:,} bytes")
    print(f"  SHA-256:       {output_sha256}")

    return OUTPUT_PATH, total_records, output_sha256


if __name__ == "__main__":
    build_canonical_snapshots()

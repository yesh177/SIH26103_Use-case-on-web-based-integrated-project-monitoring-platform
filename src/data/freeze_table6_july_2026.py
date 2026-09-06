"""
PAIMANA Predictive Risk Intelligence
Module 2A: July 2026 Table 6 Dataset Freezing & Promotion

Verifies interim dataset integrity against all structural and semantic gates,
promotes exact validated bytes to data/processed/table6_july_2026_projects.csv,
generates SHA256 checksum, and ensures byte-for-byte fidelity.
"""

from collections import Counter
from datetime import datetime
from pathlib import Path
import csv
import hashlib
import shutil
import sys

INTERIM_PATH = Path("data/interim/table6_july_2026_projects.csv")
PROCESSED_DIR = Path("data/processed")
PROCESSED_CSV = PROCESSED_DIR / "table6_july_2026_projects.csv"
CHECKSUM_PATH = PROCESSED_DIR / "table6_july_2026_projects.sha256"

EXPECTED_PROJECTS = 1775

REQUIRED_COLUMNS = [
    "snapshot_date",
    "source_page",
    "sl_no",
    "project_id",
    "project_name",
    "agency",
    "legacy_ocms_code",
    "pmgid",
    "state",
    "approval_date",
    "start_date",
    "original_completion_date",
    "revised_completion_date",
    "original_cost_crore",
    "revised_cost_crore",
    "cumulative_expenditure_crore",
    "physical_progress_pct",
]


def sha256_file(path: Path) -> str:
    """Compute SHA256 checksum of a file in 1MB chunks."""
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_interim_dataset():
    """Verify all structural and semantic requirements before promotion."""
    print("=" * 75)
    print("STEP 1: PRE-FREEZE VERIFICATION OF JULY 2026 INTERIM DATASET")
    print("=" * 75)

    # 1. Existence check
    if not INTERIM_PATH.exists():
        raise FileNotFoundError(f"Interim dataset not found: {INTERIM_PATH}")
    print(f"  [OK] Interim file exists: {INTERIM_PATH}")

    # 2. Successful CSV read & schema validation
    with INTERIM_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)

    print(f"  [OK] Successfully read {len(rows)} records via csv.DictReader")

    if columns != REQUIRED_COLUMNS:
        raise ValueError(
            f"Schema mismatch.\nExpected: {REQUIRED_COLUMNS}\nFound:    {columns}"
        )
    print("  [OK] Schema: 17 canonical columns match exactly")

    # 3. Row count check
    if len(rows) != EXPECTED_PROJECTS:
        raise ValueError(f"Expected {EXPECTED_PROJECTS} rows, found {len(rows)}")
    print(f"  [OK] Row count: exactly {len(rows)} (Expected: {EXPECTED_PROJECTS})")

    # 4. Serial continuity 1–1775
    serials = [int(r["sl_no"]) for r in rows]
    expected_serials = list(range(1, EXPECTED_PROJECTS + 1))
    if serials != expected_serials:
        missing = sorted(set(expected_serials) - set(serials))
        raise ValueError(f"Serial numbers are not continuous 1–1775. Missing: {missing}")
    print(f"  [OK] Serial numbers: strictly continuous 1 through {EXPECTED_PROJECTS}")

    # 5. Project ID uniqueness and completeness
    project_ids = [r["project_id"].strip() for r in rows if r["project_id"].strip()]
    if len(project_ids) != EXPECTED_PROJECTS:
        raise ValueError(f"Missing project IDs: {EXPECTED_PROJECTS - len(project_ids)}")
    if len(set(project_ids)) != EXPECTED_PROJECTS:
        dupes = [pid for pid, c in Counter(project_ids).items() if c > 1]
        raise ValueError(f"Duplicate project IDs detected: {dupes}")
    print(f"  [OK] Unique project IDs: {len(set(project_ids))} / {EXPECTED_PROJECTS} (0 missing, 0 duplicate)")

    # 6. Source pages 55–152
    pages = [int(r["source_page"]) for r in rows]
    if not all(55 <= p <= 152 for p in pages):
        out_of_bounds = [p for p in pages if not (55 <= p <= 152)]
        raise ValueError(f"Source pages out of bounds [55, 152]: {out_of_bounds}")
    print(f"  [OK] Source pages: all within range [55, 152] (min: {min(pages)}, max: {max(pages)})")

    # 7. No numeric or invalid state values
    numeric_states = [(r["sl_no"], r["state"]) for r in rows if r["state"].strip().isdigit()]
    if numeric_states:
        raise ValueError(f"Numeric/corrupted state values detected in {len(numeric_states)} records: {numeric_states[:10]}")

    empty_states = [(r["sl_no"], r["project_id"]) for r in rows if not r["state"].strip()]
    if empty_states:
        raise ValueError(f"Empty state values detected in {len(empty_states)} records: {empty_states[:10]}")
    print(f"  [OK] State validation: 0 numeric states, 0 empty states across all {len(rows)} records")

    # 8. Verification of all 23 previously corrupted records
    check_23_serials = [
        (525, "Andhra Pradesh"),
        (528, "Andhra Pradesh"),
        (529, "Andhra Pradesh"),
        (532, "Assam"),
        (536, "Bihar"),
        (545, "Bihar"),
        (546, "Bihar"),
        (553, "Chhattisgarh"),
        (557, "Goa"),
        (570, "Haryana"),
        (571, "Jharkhand"),
        (583, "Karnataka"),
        (606, "Maharashtra"),
        (627, "Multi-States (Bihar, West Bengal)"),
        (667, "Odisha"),
        (668, "Odisha"),
        (669, "Odisha"),
        (686, "Rajasthan"),
        (689, "Rajasthan"),
        (691, "Rajasthan"),
        (692, "Rajasthan"),
        (702, "Uttar Pradesh"),
        (1671, "Uttarakhand"),
    ]
    rows_by_sl = {int(r["sl_no"]): r for r in rows}
    for sl, exp_state in check_23_serials:
        actual_state = rows_by_sl[sl]["state"]
        if actual_state != exp_state:
            raise ValueError(
                f"Serial {sl} state mismatch: expected '{exp_state}', found '{actual_state}'"
            )
    print(f"  [OK] Verified all 23 previously corrupted state records match official ground truth")

    # 9. Verification of Serial 557 values
    r557 = rows_by_sl[557]
    if r557["project_id"] != "706865":
        raise ValueError(f"Serial 557 project_id mismatch: expected '706865', got '{r557['project_id']}'")
    if r557["state"] != "Goa":
        raise ValueError(f"Serial 557 state mismatch: expected 'Goa', got '{r557['state']}'")
    if r557["approval_date"] != "":
        raise ValueError(
            f"Serial 557 approval_date mismatch: expected '' (source NA), got '{r557['approval_date']}'"
        )
    if r557["start_date"] != "01/2022":
        raise ValueError(f"Serial 557 start_date mismatch: expected '01/2022', got '{r557['start_date']}'")
    if r557["original_completion_date"] != "03/2031":
        raise ValueError(
            f"Serial 557 original_completion_date mismatch: expected '03/2031', got '{r557['original_completion_date']}'"
        )
    if r557["revised_completion_date"] != "":
        raise ValueError(
            f"Serial 557 revised_completion_date mismatch: expected '', got '{r557['revised_completion_date']}'"
        )
    print("  [OK] Serial 557 verified: approval_date preserved as empty (NA), completion dates unshifted")

    # 10. Financial Totals & Table 1 Reconciliation
    tot_orig = sum(float(r["original_cost_crore"]) for r in rows if r["original_cost_crore"])
    tot_rev_mospi = sum(float(r["revised_cost_crore"]) if r["revised_cost_crore"] else float(r["original_cost_crore"]) for r in rows)
    tot_exp = sum(float(r["cumulative_expenditure_crore"]) for r in rows if r["cumulative_expenditure_crore"])

    expected_orig = 3370138.22
    expected_rev = 3710641.55
    expected_exp = 1926099.57

    if round(tot_orig, 2) != expected_orig:
        raise ValueError(f"Original cost mismatch: {tot_orig:.2f} != {expected_orig:.2f}")
    if round(tot_rev_mospi, 2) != expected_rev:
        raise ValueError(f"Revised cost* mismatch: {tot_rev_mospi:.2f} != {expected_rev:.2f}")
    if round(tot_exp, 2) != expected_exp:
        raise ValueError(f"Cumulative expenditure mismatch: {tot_exp:.2f} != {expected_exp:.2f}")

    print("  [OK] Financial Reconciliation against official Table 1 totals:")
    print(f"       Original Cost: {tot_orig:,.2f} Cr (Official: {expected_orig:,.2f} Cr, Diff: +0.00)")
    print(f"       Revised Cost*: {tot_rev_mospi:,.2f} Cr (Official: {expected_rev:,.2f} Cr, Diff: +0.00)")
    print(f"       Expenditure:   {tot_exp:,.2f} Cr (Official: {expected_exp:,.2f} Cr, Diff: +0.00)")

    return rows


def promote_dataset():
    """Copy interim dataset to processed and generate checksum."""
    print()
    print("=" * 75)
    print("STEP 2: CONTROLLED DATASET PROMOTION")
    print("=" * 75)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Compute source checksum
    source_sha256 = sha256_file(INTERIM_PATH)
    print(f"  Source file:      {INTERIM_PATH}")
    print(f"  Source SHA256:    {source_sha256}")

    # Copy exact validated bytes
    shutil.copy2(INTERIM_PATH, PROCESSED_CSV)
    print(f"  Promoted to:      {PROCESSED_CSV}")

    # Compute promoted checksum
    promoted_sha256 = sha256_file(PROCESSED_CSV)
    print(f"  Promoted SHA256:  {promoted_sha256}")

    # Strict byte-for-byte comparison
    if source_sha256 != promoted_sha256:
        PROCESSED_CSV.unlink(missing_ok=True)
        raise ValueError(
            f"CRITICAL ERROR: Promoted SHA256 differs from source!\n"
            f"Source:   {source_sha256}\n"
            f"Promoted: {promoted_sha256}"
        )
    print("  [OK] Byte-for-byte identity confirmed: Source SHA256 == Promoted SHA256")

    # Generate .sha256 checksum file
    checksum_content = f"{promoted_sha256}  {PROCESSED_CSV.name}\n"
    CHECKSUM_PATH.write_text(checksum_content, encoding="utf-8")
    print(f"  Generated:        {CHECKSUM_PATH}")

    return promoted_sha256


def main():
    print("PAIMANA Module 2A — July 2026 Table 6 Dataset Freeze Pipeline")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    verify_interim_dataset()
    sha256 = promote_dataset()

    print()
    print("=" * 75)
    print("JULY 2026 TABLE 6 DATASET FREEZE COMPLETED SUCCESSFULLY")
    print("=" * 75)
    print(f"  Frozen Dataset: {PROCESSED_CSV}")
    print(f"  SHA256:         {sha256}")
    print(f"  Status:         FROZEN")


if __name__ == "__main__":
    main()
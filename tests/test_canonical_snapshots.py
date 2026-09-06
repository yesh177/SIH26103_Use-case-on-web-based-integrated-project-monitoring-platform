"""
Test suite for Module 2B Canonical Snapshots (tests/test_canonical_snapshots.py).

Verifies:
1. Output exists
2. Exactly 4,161 rows
3. Exactly 30 canonical fields
4. Expected column names
5. 1,595 June observations
6. 791 July 2025 observations
7. 1,775 July 2026 observations
8. canonical_observation_key uniqueness
9. Every source observation represented exactly once
10. Source row counts preserved
11. Frozen source hashes unchanged
12. Source pages valid
13. Source rows valid
14. No negative financial values
15. Physical progress bounds [0.0, 100.0]
16. Snapshot dates valid
17. Missing-value semantics preserved (no imputation, raw values kept)
18. No cross-snapshot matching performed (no physical project entity created)
19. No duplicate canonical observations
20. Deterministic output across repeated runs
21. Source-specific field fidelity: June 2025 sector populated; July 2025/2026 sector empty;
    July 2026 legacy_ocms_code & pmgid remain source-observed '-'.
"""

from collections import Counter
from pathlib import Path
import csv
import hashlib
import unittest

from src.normalization.canonicalize_snapshots import (
    CANONICAL_COLUMNS,
    JUNE_2025_PATH,
    JUNE_2025_SHA,
    JULY_2025_PATH,
    JULY_2025_SHA,
    JULY_2026_PATH,
    JULY_2026_SHA,
    OUTPUT_PATH,
    build_canonical_snapshots,
    normalize_date,
    sha256_file,
)


class TestCanonicalSnapshots(unittest.TestCase):
    """Test suite covering all Module 2B canonical snapshot validation gates."""

    @classmethod
    def setUpClass(cls):
        """Load canonical dataset once for class-level inspection."""
        if not OUTPUT_PATH.exists():
            build_canonical_snapshots()
        with OUTPUT_PATH.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cls.columns = reader.fieldnames or []
            cls.rows = list(reader)

    def test_01_output_exists(self):
        """Verify output file exists on disk."""
        self.assertTrue(OUTPUT_PATH.exists(), f"Output file missing: {OUTPUT_PATH}")
        self.assertGreater(OUTPUT_PATH.stat().st_size, 0)

    def test_02_exact_row_count(self):
        """Verify total row count is exactly 4,161."""
        self.assertEqual(len(self.rows), 4161, f"Expected 4,161 rows, got {len(self.rows)}")

    def test_03_exact_column_count(self):
        """Verify exactly 30 canonical fields exist."""
        self.assertEqual(len(self.columns), 30, f"Expected 30 columns, got {len(self.columns)}")
        self.assertEqual(len(CANONICAL_COLUMNS), 30)

    def test_04_expected_column_names(self):
        """Verify column names match specification exactly."""
        self.assertEqual(self.columns, CANONICAL_COLUMNS)

    def test_05_06_07_snapshot_partition_counts(self):
        """Verify row counts per snapshot: June 2025 (1595), July 2025 (791), July 2026 (1775)."""
        counts = Counter(r["source_snapshot"] for r in self.rows)
        self.assertEqual(counts["2025-06"], 1595)
        self.assertEqual(counts["2025-07"], 791)
        self.assertEqual(counts["2026-07"], 1775)
        self.assertEqual(sum(counts.values()), 4161)

    def test_08_canonical_observation_key_uniqueness(self):
        """Verify canonical_observation_key is 100% unique across all rows."""
        keys = [r["canonical_observation_key"] for r in self.rows]
        self.assertEqual(len(keys), len(set(keys)), "Duplicate canonical_observation_keys found!")
        self.assertEqual(len(set(keys)), 4161)

    def test_09_every_source_observation_represented_exactly_once(self):
        """Verify mapping from (source_snapshot, source_table, source_row) is bijective."""
        tuples = [(r["source_snapshot"], r["source_table"], int(r["source_row"])) for r in self.rows]
        self.assertEqual(len(tuples), len(set(tuples)))

    def test_10_source_row_counts_preserved(self):
        """Verify source serial numbers match range 1..N for each snapshot."""
        for snap, expected_count in [("2025-06", 1595), ("2025-07", 791), ("2026-07", 1775)]:
            serials = [int(r["source_row"]) for r in self.rows if r["source_snapshot"] == snap]
            self.assertEqual(len(serials), expected_count)
            self.assertEqual(sorted(serials), list(range(1, expected_count + 1)))

    def test_11_frozen_source_hashes_unchanged(self):
        """Verify frozen source files have NOT been modified."""
        pairs = [
            (JUNE_2025_PATH, JUNE_2025_SHA),
            (JULY_2025_PATH, JULY_2025_SHA),
            (JULY_2026_PATH, JULY_2026_SHA),
        ]
        for path, sha_path in pairs:
            expected = sha_path.read_text(encoding="utf-8").split()[0].strip()
            actual = sha256_file(path)
            self.assertEqual(actual, expected, f"Frozen dataset altered: {path}")

    def test_12_source_pages_valid(self):
        """Verify source page bounds per report."""
        for r in self.rows:
            page = int(r["source_page"])
            snap = r["source_snapshot"]
            if snap == "2025-06":
                self.assertTrue(41 <= page <= 229, f"Invalid June 2025 page: {page}")
            elif snap == "2025-07":
                self.assertTrue(37 <= page <= 66, f"Invalid July 2025 page: {page}")
            elif snap == "2026-07":
                self.assertTrue(55 <= page <= 152, f"Invalid July 2026 page: {page}")

    def test_13_source_rows_valid(self):
        """Verify source_row is a positive integer."""
        for r in self.rows:
            self.assertTrue(r["source_row"].isdigit())
            self.assertGreaterEqual(int(r["source_row"]), 1)

    def test_14_no_negative_financial_values(self):
        """Verify no financial values are negative."""
        financial_cols = [
            "original_cost_crore", "revised_cost_crore",
            "anticipated_cost_crore", "cumulative_expenditure_crore"
        ]
        for r in self.rows:
            for col in financial_cols:
                val = r[col].strip()
                if val:
                    f_val = float(val)
                    self.assertGreaterEqual(
                        f_val, 0.0,
                        f"Negative financial value in {r['canonical_observation_key']}, {col}: {f_val}"
                    )

    def test_15_physical_progress_bounds(self):
        """Verify physical progress is in [0.0, 100.0]."""
        for r in self.rows:
            val = r["physical_progress_pct"].strip()
            if val:
                f_val = float(val)
                self.assertTrue(
                    0.0 <= f_val <= 100.0,
                    f"Physical progress out of bounds in {r['canonical_observation_key']}: {f_val}"
                )

    def test_16_snapshot_dates_valid(self):
        """Verify snapshot dates are strictly 2025-06-30, 2025-07-31, 2026-07-31."""
        valid_dates = {"2025-06-30", "2025-07-31", "2026-07-31"}
        for r in self.rows:
            self.assertIn(r["snapshot_date"], valid_dates)
            if r["source_snapshot"] == "2025-06":
                self.assertEqual(r["snapshot_date"], "2025-06-30")
            elif r["source_snapshot"] == "2025-07":
                self.assertEqual(r["snapshot_date"], "2025-07-31")
            elif r["source_snapshot"] == "2026-07":
                self.assertEqual(r["snapshot_date"], "2026-07-31")

    def test_17_missing_value_semantics_preserved(self):
        """Verify missing revised costs are preserved raw (not imputed)."""
        june_unrevised = sum(
            1 for r in self.rows
            if r["source_snapshot"] == "2025-06" and not r["revised_cost_crore"].strip()
        )
        self.assertEqual(june_unrevised, 1234, "June 2025 unrevised costs corrupted!")

        # Verify unavailable start_date in June 2025 & July 2025 is empty
        for r in self.rows:
            if r["source_snapshot"] in ["2025-06", "2025-07"]:
                self.assertEqual(r["start_date"], "", "start_date fabricated in 2025!")
                self.assertEqual(r["start_date_raw"], "", "start_date_raw fabricated in 2025!")

    def test_18_no_cross_snapshot_matching_performed(self):
        """Verify no canonical_project_key (entity ID) was created in this phase."""
        self.assertNotIn("canonical_project_key", self.columns)
        self.assertIn("canonical_observation_key", self.columns)

    def test_19_no_duplicate_canonical_observations(self):
        """Verify zero duplicate rows across the entire dataset."""
        record_hashes = [r["source_record_hash"] for r in self.rows]
        self.assertEqual(len(record_hashes), len(set(record_hashes)), "Duplicate record hashes!")

    def test_20_deterministic_output_across_repeated_runs(self):
        """Verify that running the script again produces byte-for-byte identical output."""
        hash_before = sha256_file(OUTPUT_PATH)
        build_canonical_snapshots()
        hash_after = sha256_file(OUTPUT_PATH)
        self.assertEqual(hash_before, hash_after, "Canonicalization is not deterministic!")

    def test_21_source_specific_field_fidelity(self):
        """Verify sector, legacy_ocms_code, and pmgid field rules."""
        # June 2025 sector must be 100% populated
        june_sectors = [r["sector"] for r in self.rows if r["source_snapshot"] == "2025-06"]
        self.assertTrue(all(s != "" for s in june_sectors))
        self.assertEqual(len(set(june_sectors)), 17)

        # July 2025 & July 2026 sector must be empty (unavailable in source)
        other_sectors = [r["sector"] for r in self.rows if r["source_snapshot"] != "2025-06"]
        self.assertTrue(all(s == "" for s in other_sectors), "Sector fabricated for July 2025/2026!")

        # July 2026 legacy_ocms_code & pmgid must report '-'
        july26_ocms = [r["legacy_ocms_code"] for r in self.rows if r["source_snapshot"] == "2026-07"]
        july26_pmgid = [r["pmgid"] for r in self.rows if r["source_snapshot"] == "2026-07"]
        self.assertTrue(all(c == "-" for c in july26_ocms))
        self.assertTrue(all(p == "-" for p in july26_pmgid))


if __name__ == "__main__":
    unittest.main()

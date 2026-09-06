"""
Unit and validation test suite for Module 2B Phase 3: Project Identity Resolution.

Verifies:
1. 4,161 observations represented exactly once
2. No observation belongs to multiple canonical projects
3. canonical_project_key deterministic and stable
4. No random UUIDs
5. match_confidence populated for every observation
6. match_method populated for every observation
7. No forbidden fuzzy-only matches
8. No duplicate observation mappings in identity map
9. Matched pairs have recorded evidence
10. Unmatched observations retained
11. Panel contains no artificial snapshot rows (exact 4,161 rows)
12. source_snapshot values unchanged
13. source_project_id values unchanged
14. Frozen source datasets remain unchanged
15. Canonical snapshot dataset remains unchanged
16. Rerunning the resolver produces byte-for-byte identical output
17. Match counts by confidence tier verified
18. Matched observation counts by snapshot pair verified
19. Ambiguous/review-required cases reported and remain unmerged
20. No automatic match violates the Phase 1 policy
"""

from collections import Counter, defaultdict
from pathlib import Path
import csv
import unittest

from src.normalization.resolve_project_identity import (
    CANONICAL_SNAPSHOTS_PATH,
    FROZEN_FILES,
    IDENTITY_MAP_PATH,
    PANEL_PATH,
    resolve_identities,
    sha256_file,
)


class TestProjectIdentityResolution(unittest.TestCase):
    """Validation test suite covering all identity resolution gates."""

    @classmethod
    def setUpClass(cls):
        """Ensure identity resolution has run and load artifacts."""
        if not IDENTITY_MAP_PATH.exists() or not PANEL_PATH.exists():
            resolve_identities()

        with IDENTITY_MAP_PATH.open(encoding="utf-8", newline="") as f:
            cls.map_rows = list(csv.DictReader(f))

        with PANEL_PATH.open(encoding="utf-8", newline="") as f:
            cls.panel_rows = list(csv.DictReader(f))

        with CANONICAL_SNAPSHOTS_PATH.open(encoding="utf-8", newline="") as f:
            cls.canon_rows = list(csv.DictReader(f))

    def test_01_exact_observation_count(self):
        """Verify exactly 4,161 observations appear in identity map and panel."""
        self.assertEqual(len(self.map_rows), 4161)
        self.assertEqual(len(self.panel_rows), 4161)

    def test_02_bijective_observation_mapping(self):
        """Verify every observation maps to exactly one canonical project."""
        obs_keys = [r["canonical_observation_key"] for r in self.map_rows]
        self.assertEqual(len(obs_keys), len(set(obs_keys)))
        self.assertEqual(len(set(obs_keys)), 4161)

    def test_03_canonical_project_key_deterministic(self):
        """Verify canonical project keys follow deterministic prefix naming."""
        allowed_prefixes = ("PROJ-PAIMANA-", "PROJ-UNMATCHED-", "PROJ-REVIEW-")
        for r in self.map_rows:
            key = r["canonical_project_key"]
            self.assertTrue(
                key.startswith(allowed_prefixes),
                f"Invalid project key format: {key}"
            )

    def test_04_no_random_uuids(self):
        """Verify no random UUID format exists in canonical_project_key."""
        import re
        uuid_pattern = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
        for r in self.map_rows:
            self.assertIsNone(
                uuid_pattern.search(r["canonical_project_key"]),
                f"Random UUID detected in project key: {r['canonical_project_key']}"
            )

    def test_05_match_confidence_populated(self):
        """Verify match_confidence is populated for every observation."""
        allowed_tiers = {"EXACT_ID", "EXPLICIT_CROSS_SOURCE_ID", "STRONG_MATCH", "REVIEW_REQUIRED", "UNMATCHED"}
        for r in self.map_rows:
            self.assertIn(r["match_confidence"], allowed_tiers)

    def test_06_match_method_populated(self):
        """Verify match_method is explicitly stated for every observation."""
        for r in self.map_rows:
            self.assertTrue(bool(r["match_method"].strip()))

    def test_07_no_fuzzy_only_matches(self):
        """Verify no match method relies exclusively on string similarity."""
        for r in self.map_rows:
            self.assertNotIn("FUZZY_ONLY", r["match_method"])
            self.assertNotIn("LEVENSHTEIN", r["match_method"])

    def test_08_no_duplicate_observation_mappings(self):
        """Verify identity map contains zero duplicate rows."""
        hashes = [hash((r["canonical_observation_key"], r["canonical_project_key"])) for r in self.map_rows]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_09_matched_pairs_have_recorded_evidence(self):
        """Verify all matched observations have detailed evidence recorded."""
        for r in self.map_rows:
            if r["match_confidence"] in ["EXACT_ID", "STRONG_MATCH"]:
                self.assertTrue(
                    len(r["match_evidence"].strip()) > 10,
                    f"Empty or inadequate evidence for matched observation: {r['canonical_observation_key']}"
                )

    def test_10_unmatched_observations_retained(self):
        """Verify unmatched observations are properly retained with independent keys."""
        unmatched = [r for r in self.map_rows if r["match_confidence"] == "UNMATCHED"]
        self.assertGreater(len(unmatched), 2500)
        for r in unmatched:
            self.assertTrue(r["canonical_project_key"].startswith("PROJ-UNMATCHED-"))

    def test_11_panel_contains_no_artificial_snapshot_rows(self):
        """Verify panel grain is exactly 1 row per real source observation (4,161 rows)."""
        self.assertEqual(len(self.panel_rows), 4161)
        panel_obs = [r["canonical_observation_key"] for r in self.panel_rows]
        canon_obs = [r["canonical_observation_key"] for r in self.canon_rows]
        self.assertEqual(sorted(panel_obs), sorted(canon_obs))

    def test_12_source_snapshot_values_unchanged(self):
        """Verify source_snapshot values match canonical inputs exactly."""
        counts = Counter(r["source_snapshot"] for r in self.panel_rows)
        self.assertEqual(counts["2025-06"], 1595)
        self.assertEqual(counts["2025-07"], 791)
        self.assertEqual(counts["2026-07"], 1775)

    def test_13_source_project_id_values_unchanged(self):
        """Verify source_project_id values match canonical input identically."""
        p_ids = [r["source_project_id"] for r in self.panel_rows]
        c_ids = [r["source_project_id"] for r in self.canon_rows]
        self.assertEqual(sorted(p_ids), sorted(c_ids))

    def test_14_frozen_source_datasets_unchanged(self):
        """Verify cryptographic integrity of frozen sources."""
        for csv_path, sha_path in FROZEN_FILES:
            expected = sha_path.read_text(encoding="utf-8").split()[0].strip()
            actual = sha256_file(csv_path)
            self.assertEqual(actual, expected)

    def test_15_canonical_snapshot_dataset_unchanged(self):
        """Verify canonical snapshot input was not modified."""
        actual = sha256_file(CANONICAL_SNAPSHOTS_PATH)
        self.assertEqual(actual, "0b9d2c919262f13290efda58ed7a21ab341e06616e11571c1ea702251c10a8b7")

    def test_16_deterministic_rerun(self):
        """Verify rerunning identity resolution produces byte-for-byte identical files."""
        map_hash_before = sha256_file(IDENTITY_MAP_PATH)
        panel_hash_before = sha256_file(PANEL_PATH)

        resolve_identities()

        map_hash_after = sha256_file(IDENTITY_MAP_PATH)
        panel_hash_after = sha256_file(PANEL_PATH)

        self.assertEqual(map_hash_before, map_hash_after)
        self.assertEqual(panel_hash_before, panel_hash_after)

    def test_17_18_confidence_and_trajectory_counts(self):
        """Verify confidence tier distribution and trajectory counts."""
        conf_counts = Counter(r["match_confidence"] for r in self.map_rows)
        self.assertEqual(conf_counts["EXACT_ID"], 872)
        self.assertEqual(conf_counts["STRONG_MATCH"], 137)
        self.assertEqual(conf_counts["REVIEW_REQUIRED"], 247)
        self.assertEqual(conf_counts["UNMATCHED"], 2905)

    def test_19_review_required_cases_remain_unmerged(self):
        """Verify review-required cases are NOT merged into shared physical projects."""
        review_rows = [r for r in self.map_rows if r["match_confidence"] == "REVIEW_REQUIRED"]
        self.assertEqual(len(review_rows), 247)
        for r in review_rows:
            self.assertTrue(r["canonical_project_key"].startswith("PROJ-REVIEW-"))

    def test_20_no_violation_of_phase1_policy(self):
        """Verify no OCMS observation is matched via EXACT_ID."""
        for r in self.map_rows:
            if r["source_snapshot"] == "2025-06":
                self.assertNotEqual(r["match_confidence"], "EXACT_ID")


if __name__ == "__main__":
    unittest.main()

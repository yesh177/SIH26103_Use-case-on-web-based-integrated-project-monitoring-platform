"""
Unit and Integration Tests for Module 4 Phase 5 — Risk Score Quality Audit
SIH26103 PAIMANA Predictive Risk Intelligence

Verifies all quality audit invariants on data/processed/project_risk_scores.csv:
1. Exact SHA-256 hash matching frozen expectation.
2. Exact SHA-256 hashes of all upstream frozen files.
3. Row count, uniqueness, column schema, and null completeness.
4. Mathematical correctness of attention_score (FULL vs PARTIAL).
5. Mathematical correctness of compound_exposure (FULL strictly).
6. Non-zero preservation of missing schedule outcomes.
7. Attention tier assignment against empirical quantiles Q50, Q75, Q90.
8. Tier invariance and rank invariance for tied attention scores.
9. Correct portfolio ranking behavior (descending, method='min').
10. Correct dual elevation diagnostic counts (both >= 0.50, >= 0.75, >= 0.90).
"""

import os
import unittest
import hashlib
import numpy as np
import pandas as pd

EXPECTED_RISK_SCORES_SHA256 = "6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d"

EXPECTED_UPSTREAM_HASHES = {
    "data/interim/pit_features_july2025_to_july2026.csv": "052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329",
    "data/processed/table7_june_2025_projects.csv": "9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43",
    "data/processed/table4_july_2025_projects.csv": "ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3",
    "data/processed/table6_july_2026_projects.csv": "6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9",
    "data/processed/project_identity_map.csv": "16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb",
    "data/processed/project_snapshot_panel.csv": "9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47",
}

EXPECTED_COLUMNS = [
    "canonical_project_key", "source_project_id", "project_name", "state", "agency",
    "snapshot_date", "prediction_cutoff_date", "is_eligible_cost_target",
    "is_eligible_schedule_target", "cost_risk_probability", "schedule_risk_probability",
    "risk_coverage", "attention_score", "compound_exposure", "attention_tier",
    "portfolio_rank", "cost_model_name", "schedule_model_name",
    "cost_probability_variant", "schedule_probability_variant", "scoring_method_version",
]


class TestModule4RiskScoreQualityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.scores_path = os.path.join(cls.repo_root, "data", "processed", "project_risk_scores.csv")
        cls.assertTrue(os.path.exists(cls.scores_path), f"Missing risk scores file: {cls.scores_path}")
        cls.df = pd.read_csv(cls.scores_path)

    # 1. Verify project_risk_scores.csv SHA-256 hash immutability
    def test_01_risk_scores_sha256_unmodified(self):
        with open(self.scores_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(computed, EXPECTED_RISK_SCORES_SHA256)

    # 2. Verify all upstream frozen files SHA-256 hashes
    def test_02_upstream_frozen_hashes(self):
        for rel_path, expected_hash in EXPECTED_UPSTREAM_HASHES.items():
            full_p = os.path.join(self.repo_root, rel_path)
            self.assertTrue(os.path.exists(full_p), f"Missing frozen file: {full_p}")
            with open(full_p, "rb") as f:
                computed = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(computed, expected_hash, f"Hash mismatch for {rel_path}")

    # 3. Exact row count and uniqueness
    def test_03_row_count_and_uniqueness(self):
        self.assertEqual(len(self.df), 437)
        self.assertEqual(self.df["canonical_project_key"].nunique(), 437)
        self.assertEqual(self.df.duplicated(subset=["canonical_project_key"]).sum(), 0)

    # 4. Schema columns completeness
    def test_04_schema_columns(self):
        self.assertEqual(len(self.df.columns), 21)
        for col in EXPECTED_COLUMNS:
            self.assertIn(col, self.df.columns)

    # 5. Null pattern: strictly schedule and compound fields for PARTIAL
    def test_05_null_pattern(self):
        null_counts = self.df.isnull().sum()
        self.assertEqual(null_counts["schedule_risk_probability"], 132)
        self.assertEqual(null_counts["compound_exposure"], 132)
        for col in EXPECTED_COLUMNS:
            if col not in ["schedule_risk_probability", "compound_exposure"]:
                self.assertEqual(null_counts[col], 0, f"Unexpected nulls in column {col}")

    # 6. Probability and attention score ranges
    def test_06_ranges_and_bounds(self):
        # Cost probability
        self.assertTrue((self.df["cost_risk_probability"] >= 0.0).all())
        self.assertTrue((self.df["cost_risk_probability"] <= 1.0).all())

        # Schedule probability (for non-nulls)
        sched_valid = self.df["schedule_risk_probability"].dropna()
        self.assertEqual(len(sched_valid), 305)
        self.assertTrue((sched_valid >= 0.0).all())
        self.assertTrue((sched_valid <= 1.0).all())

        # Attention score
        self.assertTrue((self.df["attention_score"] >= 0.0).all())
        self.assertTrue((self.df["attention_score"] <= 1.0).all())

        # Compound exposure
        comp_valid = self.df["compound_exposure"].dropna()
        self.assertEqual(len(comp_valid), 305)
        self.assertTrue((comp_valid >= 0.0).all())
        self.assertTrue((comp_valid <= 1.0).all())

    # 7. Coverage counts and invariants
    def test_07_coverage_invariants(self):
        full = self.df[self.df["risk_coverage"] == "FULL"]
        partial = self.df[self.df["risk_coverage"] == "PARTIAL"]

        self.assertEqual(len(full), 305)
        self.assertEqual(len(partial), 132)

        # Full projects have both probabilities and compound exposure
        self.assertTrue(full["cost_risk_probability"].notna().all())
        self.assertTrue(full["schedule_risk_probability"].notna().all())
        self.assertTrue(full["compound_exposure"].notna().all())

        # Partial projects have null schedule probability and null compound exposure
        self.assertTrue(partial["schedule_risk_probability"].isna().all())
        self.assertTrue(partial["compound_exposure"].isna().all())

    # 8. Mathematical formula checks for attention_score and compound_exposure
    def test_08_mathematical_formulas(self):
        full = self.df[self.df["risk_coverage"] == "FULL"]
        partial = self.df[self.df["risk_coverage"] == "PARTIAL"]

        # Attention score on FULL: max(Pc, Ps)
        expected_full_att = np.maximum(full["cost_risk_probability"], full["schedule_risk_probability"])
        np.testing.assert_array_almost_equal(full["attention_score"].to_numpy(), expected_full_att.to_numpy(), decimal=6)

        # Attention score on PARTIAL: Pc
        np.testing.assert_array_almost_equal(partial["attention_score"].to_numpy(), partial["cost_risk_probability"].to_numpy(), decimal=6)

        # Compound exposure on FULL: min(Pc, Ps)
        expected_full_comp = np.minimum(full["cost_risk_probability"], full["schedule_risk_probability"])
        np.testing.assert_array_almost_equal(full["compound_exposure"].to_numpy(), expected_full_comp.to_numpy(), decimal=6)

    # 9. Empirical quantile alignment and tier assignment
    def test_09_empirical_quantiles_and_tiers(self):
        attention = self.df["attention_score"].to_numpy()
        q50 = float(np.quantile(attention, 0.50))
        q75 = float(np.quantile(attention, 0.75))
        q90 = float(np.quantile(attention, 0.90))

        self.assertAlmostEqual(q50, 0.906667, places=5)
        self.assertAlmostEqual(q75, 0.983333, places=5)
        self.assertAlmostEqual(q90, 0.994667, places=5)

        for _, row in self.df.iterrows():
            score = row["attention_score"]
            tier = row["attention_tier"]
            if score >= q90:
                self.assertEqual(tier, "Tier 1")
            elif score >= q75:
                self.assertEqual(tier, "Tier 2")
            elif score >= q50:
                self.assertEqual(tier, "Tier 3")
            else:
                self.assertEqual(tier, "Tier 4")

        # Check exact counts
        tier_counts = self.df["attention_tier"].value_counts()
        self.assertEqual(tier_counts["Tier 1"], 44)
        self.assertEqual(tier_counts["Tier 2"], 73)
        self.assertEqual(tier_counts["Tier 3"], 102)
        self.assertEqual(tier_counts["Tier 4"], 218)

    # 10. Tied scores receive identical tiers and identical ranks
    def test_10_tied_scores_consistency(self):
        grouped = self.df.groupby("attention_score")
        for score, group in grouped:
            self.assertEqual(group["attention_tier"].nunique(), 1, f"Inconsistent tier for score {score}")
            self.assertEqual(group["portfolio_rank"].nunique(), 1, f"Inconsistent rank for score {score}")

    # 11. Portfolio rank bounds and monotonicity
    def test_11_portfolio_rank_monotonicity(self):
        self.assertTrue((self.df["portfolio_rank"] >= 1).all())
        self.assertTrue((self.df["portfolio_rank"] <= 437).all())

        # When sorted by rank ascending, attention score must be monotonically non-increasing
        sorted_df = self.df.sort_values(by="portfolio_rank", ascending=True)
        diffs = np.diff(sorted_df["attention_score"].to_numpy())
        self.assertTrue((diffs <= 1e-9).all(), "Attention score does not decrease monotonically with rank!")

    # 12. Dual elevation counts verification
    def test_12_dual_elevation_counts(self):
        full = self.df[self.df["risk_coverage"] == "FULL"]
        c_ge_50_s_ge_50 = int(((full["cost_risk_probability"] >= 0.50) & (full["schedule_risk_probability"] >= 0.50)).sum())
        c_ge_75_s_ge_75 = int(((full["cost_risk_probability"] >= 0.75) & (full["schedule_risk_probability"] >= 0.75)).sum())
        c_ge_90_s_ge_90 = int(((full["cost_risk_probability"] >= 0.90) & (full["schedule_risk_probability"] >= 0.90)).sum())

        self.assertEqual(c_ge_50_s_ge_50, 98)
        self.assertEqual(c_ge_75_s_ge_75, 71)
        self.assertEqual(c_ge_90_s_ge_90, 42)


if __name__ == "__main__":
    unittest.main()

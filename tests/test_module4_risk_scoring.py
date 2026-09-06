"""
Unit and Integration Tests for Module 4 — Risk Scoring Engine
SIH26103 PAIMANA Predictive Risk Intelligence

Verifies:
1. Immutability of PIT dataset and upstream frozen files.
2. Probability validity (bounded in [0, 1]).
3. Non-zero preservation of missing schedule predictions.
4. Correct FULL vs PARTIAL risk coverage logic.
5. Compound exposure computation strictly on FULL coverage.
6. Attention score logic (max(Pc, Ps) for FULL, Pc for PARTIAL).
7. Consistent tier assignments for tied scores.
8. Empirical quantile alignment (Q50, Q75, Q90).
9. Unique canonical project identities.
10. Bit-for-bit determinism across consecutive pipeline runs.
"""

import os
import unittest
import hashlib
import numpy as np
import pandas as pd
from src.scoring.generate_project_risk_scores import (
    generate_risk_scores,
    EXPECTED_PIT_SHA256,
    EXPECTED_UPSTREAM_HASHES,
    assign_attention_tier,
)


class TestModule4RiskScoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.output_path = os.path.join(cls.repo_root, "data", "processed", "project_risk_scores.csv")
        cls.df = generate_risk_scores(cls.pit_path, cls.output_path)

    # 1. Verify PIT dataset hash immutability
    def test_01_pit_dataset_hash_unchanged(self):
        with open(self.pit_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(computed, EXPECTED_PIT_SHA256)

    # 2. Verify upstream frozen files hashes
    def test_02_upstream_frozen_files_unchanged(self):
        for rel_path, expected_hash in EXPECTED_UPSTREAM_HASHES.items():
            full_p = os.path.join(self.repo_root, rel_path)
            self.assertTrue(os.path.exists(full_p), f"Missing frozen file: {full_p}")
            with open(full_p, "rb") as f:
                computed = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(computed, expected_hash, f"Hash mismatch for {rel_path}")

    # 3. Output row count and identity uniqueness
    def test_03_output_shape_and_uniqueness(self):
        self.assertEqual(len(self.df), 437)
        self.assertEqual(self.df["canonical_project_key"].nunique(), 437)

    # 4. Probabilities bounded in [0, 1]
    def test_04_probabilities_bounded(self):
        # Cost risk probability: all 437 must be bounded [0, 1]
        self.assertTrue(self.df["cost_risk_probability"].notna().all())
        self.assertTrue((self.df["cost_risk_probability"] >= 0.0).all())
        self.assertTrue((self.df["cost_risk_probability"] <= 1.0).all())

        # Schedule risk probability: eligible 305 must be bounded [0, 1]
        sched_valid = self.df["schedule_risk_probability"].dropna()
        self.assertEqual(len(sched_valid), 305)
        self.assertTrue((sched_valid >= 0.0).all())
        self.assertTrue((sched_valid <= 1.0).all())

    # 5. Missing schedule predictions never converted to zero
    def test_05_missing_schedule_not_zero(self):
        ineligible = self.df[self.df["is_eligible_schedule_target"] == 0]
        self.assertEqual(len(ineligible), 132)
        self.assertTrue(ineligible["schedule_risk_probability"].isna().all())

    # 6. FULL / PARTIAL risk coverage logic
    def test_06_risk_coverage_logic(self):
        full_cov = self.df[self.df["risk_coverage"] == "FULL"]
        partial_cov = self.df[self.df["risk_coverage"] == "PARTIAL"]

        self.assertEqual(len(full_cov), 305)
        self.assertEqual(len(partial_cov), 132)

        self.assertTrue(full_cov["schedule_risk_probability"].notna().all())
        self.assertTrue(partial_cov["schedule_risk_probability"].isna().all())

    # 7. Compound exposure only populated for FULL coverage
    def test_07_compound_exposure_coverage_constraint(self):
        full_cov = self.df[self.df["risk_coverage"] == "FULL"]
        partial_cov = self.df[self.df["risk_coverage"] == "PARTIAL"]

        self.assertTrue(full_cov["compound_exposure"].notna().all())
        self.assertTrue(partial_cov["compound_exposure"].isna().all())

        # Check mathematical formula min(Pc, Ps)
        expected_compound = np.minimum(full_cov["cost_risk_probability"], full_cov["schedule_risk_probability"])
        np.testing.assert_array_almost_equal(full_cov["compound_exposure"], expected_compound, decimal=6)

    # 8. Attention score formula verification
    def test_08_attention_score_logic(self):
        # FULL coverage: attention_score == max(Pc, Ps)
        full_cov = self.df[self.df["risk_coverage"] == "FULL"]
        expected_full_attention = np.maximum(full_cov["cost_risk_probability"], full_cov["schedule_risk_probability"])
        np.testing.assert_array_almost_equal(full_cov["attention_score"], expected_full_attention, decimal=6)

        # PARTIAL coverage: attention_score == Pc
        partial_cov = self.df[self.df["risk_coverage"] == "PARTIAL"]
        np.testing.assert_array_almost_equal(partial_cov["attention_score"], partial_cov["cost_risk_probability"], decimal=6)

    # 9. Attention tiers follow Q50/Q75/Q90 thresholds
    def test_09_tier_threshold_logic(self):
        attention = self.df["attention_score"].to_numpy()
        q50 = float(np.quantile(attention, 0.50))
        q75 = float(np.quantile(attention, 0.75))
        q90 = float(np.quantile(attention, 0.90))

        for _, row in self.df.iterrows():
            score = row["attention_score"]
            tier = row["attention_tier"]
            expected_tier = assign_attention_tier(score, q50, q75, q90)
            self.assertEqual(tier, expected_tier)

    # 10. Identical attention scores receive identical tiers and valid ranking
    def test_10_tie_consistency_and_ranking(self):
        # Group by attention score
        score_groups = self.df.groupby("attention_score")
        for score, group in score_groups:
            # All items with identical attention score must have identical tier
            self.assertEqual(group["attention_tier"].nunique(), 1, f"Tied score {score} has conflicting tiers!")
            # All items with identical attention score must have identical portfolio rank
            self.assertEqual(group["portfolio_rank"].nunique(), 1, f"Tied score {score} has conflicting ranks!")

        # Rank must be positive integers <= 437
        self.assertTrue((self.df["portfolio_rank"] >= 1).all())
        self.assertTrue((self.df["portfolio_rank"] <= 437).all())

    # 11. Metadata preservation and provenance fields
    def test_11_metadata_and_provenance_fields(self):
        required_cols = [
            "canonical_project_key", "source_project_id", "project_name", "state", "agency",
            "snapshot_date", "prediction_cutoff_date", "is_eligible_cost_target",
            "is_eligible_schedule_target", "cost_risk_probability", "schedule_risk_probability",
            "risk_coverage", "attention_score", "compound_exposure", "attention_tier",
            "portfolio_rank", "cost_model_name", "schedule_model_name",
            "cost_probability_variant", "schedule_probability_variant", "scoring_method_version",
        ]
        for col in required_cols:
            self.assertIn(col, self.df.columns)

        self.assertTrue((self.df["cost_model_name"] == "RandomForestClassifier(n_estimators=300, random_state=42)").all())
        self.assertTrue((self.df["schedule_model_name"] == "RandomForestClassifier(n_estimators=300, random_state=42)").all())
        self.assertTrue((self.df["cost_probability_variant"] == "Raw / Uncalibrated").all())
        self.assertTrue((self.df["schedule_probability_variant"] == "Raw / Uncalibrated").all())
        self.assertTrue((self.df["scoring_method_version"] == "1.0.0").all())

    # 12. Bit-for-bit determinism across consecutive runs
    def test_12_determinism_across_runs(self):
        tmp_output = os.path.join(self.repo_root, "data", "processed", "project_risk_scores_test_determinism.csv")
        df2 = generate_risk_scores(self.pit_path, tmp_output)

        np.testing.assert_array_almost_equal(self.df["cost_risk_probability"].to_numpy(), df2["cost_risk_probability"].to_numpy(), decimal=8)
        np.testing.assert_array_almost_equal(
            self.df["schedule_risk_probability"].dropna().to_numpy(),
            df2["schedule_risk_probability"].dropna().to_numpy(),
            decimal=8
        )
        np.testing.assert_array_almost_equal(self.df["attention_score"].to_numpy(), df2["attention_score"].to_numpy(), decimal=8)
        self.assertTrue((self.df["attention_tier"] == df2["attention_tier"]).all())
        self.assertTrue((self.df["portfolio_rank"] == df2["portfolio_rank"]).all())

        if os.path.exists(tmp_output):
            os.remove(tmp_output)
        tmp_part = os.path.join(self.repo_root, "data", "processed", "project_risk_scores_test_determinism_partitions.csv")
        if os.path.exists(tmp_part):
            os.remove(tmp_part)

    # 13. Partition sidecar existence and full portfolio coverage
    def test_13_partition_sidecar_exists_and_covers_all_projects(self):
        part_path = os.path.join(self.repo_root, "data", "processed", "project_risk_score_partitions.csv")
        self.assertTrue(os.path.exists(part_path), f"Missing partition sidecar: {part_path}")
        part_df = pd.read_csv(part_path)
        self.assertEqual(len(part_df), 437)
        self.assertEqual(list(part_df.columns), ["canonical_project_key", "cost_prediction_partition", "schedule_prediction_partition"])
        self.assertListEqual(list(part_df["canonical_project_key"]), list(self.df["canonical_project_key"]))

    # 14. Partition categorical values validity
    def test_14_partition_values_valid(self):
        part_path = os.path.join(self.repo_root, "data", "processed", "project_risk_score_partitions.csv")
        part_df = pd.read_csv(part_path)
        valid_cost_parts = {"MODELFIT", "CALIBRATION_HOLDOUT", "TEST_HOLDOUT"}
        valid_sched_parts = {"MODELFIT", "CALIBRATION_HOLDOUT", "TEST_HOLDOUT", "NOT_ELIGIBLE"}
        self.assertTrue(set(part_df["cost_prediction_partition"]).issubset(valid_cost_parts))
        self.assertTrue(set(part_df["schedule_prediction_partition"]).issubset(valid_sched_parts))

    # 15. Exact partition size distribution
    def test_15_partition_counts_exact(self):
        part_path = os.path.join(self.repo_root, "data", "processed", "project_risk_score_partitions.csv")
        part_df = pd.read_csv(part_path)
        cost_counts = part_df["cost_prediction_partition"].value_counts().to_dict()
        sched_counts = part_df["schedule_prediction_partition"].value_counts().to_dict()

        self.assertEqual(cost_counts["MODELFIT"], 261)
        self.assertEqual(cost_counts["CALIBRATION_HOLDOUT"], 88)
        self.assertEqual(cost_counts["TEST_HOLDOUT"], 88)

        self.assertEqual(sched_counts["MODELFIT"], 183)
        self.assertEqual(sched_counts["CALIBRATION_HOLDOUT"], 61)
        self.assertEqual(sched_counts["TEST_HOLDOUT"], 61)
        self.assertEqual(sched_counts["NOT_ELIGIBLE"], 132)

    # 16. Partition alignment with schedule eligibility
    def test_16_partition_schedule_eligibility_alignment(self):
        part_path = os.path.join(self.repo_root, "data", "processed", "project_risk_score_partitions.csv")
        part_df = pd.read_csv(part_path)
        merged = self.df[["canonical_project_key", "is_eligible_schedule_target"]].merge(part_df, on="canonical_project_key")

        ineligible = merged[merged["is_eligible_schedule_target"] == 0]
        eligible = merged[merged["is_eligible_schedule_target"] == 1]

        self.assertTrue((ineligible["schedule_prediction_partition"] == "NOT_ELIGIBLE").all())
        self.assertFalse((eligible["schedule_prediction_partition"] == "NOT_ELIGIBLE").any())

    # 17. Partition sidecar determinism across runs
    def test_17_partition_determinism(self):
        tmp_output = os.path.join(self.repo_root, "data", "processed", "project_risk_scores_test_part_det.csv")
        tmp_part = os.path.join(self.repo_root, "data", "processed", "project_risk_scores_test_part_det_partitions.csv")
        generate_risk_scores(self.pit_path, tmp_output)

        part_orig = pd.read_csv(os.path.join(self.repo_root, "data", "processed", "project_risk_score_partitions.csv"))
        part_new = pd.read_csv(tmp_part)

        pd.testing.assert_frame_equal(part_orig, part_new)

        if os.path.exists(tmp_output):
            os.remove(tmp_output)
        if os.path.exists(tmp_part):
            os.remove(tmp_part)


if __name__ == "__main__":
    unittest.main()

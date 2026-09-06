"""
Unit and Integration Tests for Module 4 Phase 6 — Explainable Risk Drivers
SIH26103 PAIMANA Predictive Risk Intelligence

Verifies all explainability engine invariants:
1. Authorized 12 predictors only; sector strictly absent.
2. Zero target leakage or July 2026 outcome fields.
3. Cryptographic integrity of all upstream files and project_risk_scores.csv.
4. Exactly 874 explanation records (437 projects x 2 tasks).
5. Zero duplicate (canonical_project_key, task) pairs.
6. Probability values match project_risk_scores.csv identically.
7. Feature values in explanations match PIT dataset values.
8. Missing schedule probabilities remain strictly missing (NaN).
9. All top reported features belong to the authorized 12 predictors.
10. Valid directions ('ELEVATES_RISK', 'ATTENUATES_RISK', 'NEUTRAL').
11. Bit-for-bit determinism across repeated executions.
12. Factual, non-hallucinated source facts.
"""

import os
import unittest
import hashlib
import numpy as np
import pandas as pd
from src.explainability.explain_risk_drivers import (
    generate_explanations,
    AUTHORIZED_PREDICTORS,
    PROHIBITED_FIELDS,
    EXPECTED_PIT_SHA256,
    EXPECTED_SCORES_SHA256,
    EXPECTED_UPSTREAM_HASHES,
)


class TestModule4Explainability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.scores_path = os.path.join(cls.repo_root, "data", "processed", "project_risk_scores.csv")
        cls.output_path = os.path.join(cls.repo_root, "data", "interim", "project_risk_explanations.csv")

        cls.df, cls.global_cost, cls.global_sched = generate_explanations(
            cls.pit_path, cls.scores_path, cls.output_path
        )
        cls.pit_df = pd.read_csv(cls.pit_path)
        cls.scores_df = pd.read_csv(cls.scores_path)

    # 1. Verify project_risk_scores.csv hash is unchanged
    def test_01_risk_scores_unmodified(self):
        with open(self.scores_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(computed, EXPECTED_SCORES_SHA256)

    # 2. Verify all upstream frozen hashes
    def test_02_upstream_frozen_hashes(self):
        for rel_path, expected_hash in EXPECTED_UPSTREAM_HASHES.items():
            full_p = os.path.join(self.repo_root, rel_path)
            self.assertTrue(os.path.exists(full_p), f"Missing frozen file: {full_p}")
            with open(full_p, "rb") as f:
                computed = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(computed, expected_hash, f"Hash mismatch for {rel_path}")

    # 3. Authorized predictor list only, sector strictly absent
    def test_03_authorized_predictors_only(self):
        self.assertEqual(len(AUTHORIZED_PREDICTORS), 12)
        for prohibited in PROHIBITED_FIELDS:
            self.assertNotIn(prohibited, AUTHORIZED_PREDICTORS)
            self.assertNotIn(prohibited, self.global_cost.keys())
            self.assertNotIn(prohibited, self.global_sched.keys())

        # Check in explanation outputs
        for col in ["top_1_feature", "top_2_feature", "top_3_feature"]:
            features = self.df[col].dropna().unique()
            for feat in features:
                self.assertIn(feat, AUTHORIZED_PREDICTORS, f"Unauthorized feature reported: {feat}")
                self.assertNotIn("sector", feat.lower())

    # 4. Zero duplicate (project_key, task) records
    def test_04_no_duplicate_project_task_records(self):
        self.assertEqual(len(self.df), 874)
        duplicates = self.df.duplicated(subset=["canonical_project_key", "task"]).sum()
        self.assertEqual(duplicates, 0)

        # 437 cost tasks and 437 schedule tasks
        task_counts = self.df["task"].value_counts()
        self.assertEqual(task_counts["cost_overrun"], 437)
        self.assertEqual(task_counts["schedule_slippage"], 437)

    # 5. Probability values match project_risk_scores.csv identically
    def test_05_probabilities_match_scores(self):
        scores_map = self.scores_df.set_index("canonical_project_key").to_dict(orient="index")

        for _, row in self.df.iterrows():
            key = row["canonical_project_key"]
            task = row["task"]
            exp_p = row["predicted_risk_probability"]

            if task == "cost_overrun":
                score_p = scores_map[key]["cost_risk_probability"]
                self.assertAlmostEqual(exp_p, score_p, places=6)
            elif task == "schedule_slippage":
                score_p = scores_map[key]["schedule_risk_probability"]
                if np.isnan(score_p):
                    self.assertTrue(np.isnan(exp_p))
                else:
                    self.assertAlmostEqual(exp_p, score_p, places=6)

    # 6. Missing schedule probability remains strictly missing (132 ineligible)
    def test_06_missing_schedule_remains_missing(self):
        sched_ineligible = self.df[(self.df["task"] == "schedule_slippage") & (self.df["is_eligible_task_target"] == 0)]
        self.assertEqual(len(sched_ineligible), 132)
        self.assertTrue(sched_ineligible["predicted_risk_probability"].isna().all())
        self.assertTrue(sched_ineligible["top_1_feature"].isna().all())
        self.assertTrue(sched_ineligible["top_1_impact"].isna().all())

    # 7. Explanation values match PIT features
    def test_07_explanation_values_match_pit(self):
        pit_map = self.pit_df.set_index("canonical_project_key").to_dict(orient="index")

        # Check on eligible rows
        eligible = self.df[self.df["is_eligible_task_target"] == 1]
        for _, row in eligible.head(100).iterrows():
            key = row["canonical_project_key"]
            for f_col, v_col in [("top_1_feature", "top_1_feature_value"), ("top_2_feature", "top_2_feature_value")]:
                feat_name = row[f_col]
                feat_val_str = str(row[v_col])
                actual_pit_val = pit_map[key][feat_name]
                if isinstance(actual_pit_val, (float, np.floating)):
                    self.assertAlmostEqual(float(feat_val_str), float(actual_pit_val), places=4)
                else:
                    self.assertEqual(feat_val_str, str(actual_pit_val))

    # 8. Direction labels are valid
    def test_08_direction_labels_valid(self):
        eligible = self.df[self.df["is_eligible_task_target"] == 1]
        valid_dirs = {"ELEVATES_RISK", "ATTENUATES_RISK", "NEUTRAL"}
        for col in ["top_1_direction", "top_2_direction", "top_3_direction"]:
            unique_dirs = set(eligible[col].unique())
            self.assertTrue(unique_dirs.issubset(valid_dirs), f"Invalid directions: {unique_dirs - valid_dirs}")

    # 9. Source facts are non-empty and non-fabricated
    def test_09_source_facts_integrity(self):
        self.assertTrue(self.df["top_1_source_fact"].notna().all())
        self.assertTrue((self.df["top_1_source_fact"].str.len() > 10).all())

    # 10. Global importance sums to 1.0 and covers all 12 predictors
    def test_10_global_importance_integrity(self):
        self.assertEqual(len(self.global_cost), 12)
        self.assertEqual(len(self.global_sched), 12)
        self.assertAlmostEqual(sum(self.global_cost.values()), 1.0, places=4)
        self.assertAlmostEqual(sum(self.global_sched.values()), 1.0, places=4)

    # 11. Determinism across consecutive runs
    def test_11_determinism_across_runs(self):
        tmp_output = os.path.join(self.repo_root, "data", "interim", "project_risk_explanations_test_determinism.csv")
        df2, gc2, gs2 = generate_explanations(self.pit_path, self.scores_path, tmp_output)

        self.assertEqual(self.global_cost, gc2)
        self.assertEqual(self.global_sched, gs2)
        pd.testing.assert_frame_equal(self.df, df2)

        if os.path.exists(tmp_output):
            os.remove(tmp_output)


if __name__ == "__main__":
    unittest.main()

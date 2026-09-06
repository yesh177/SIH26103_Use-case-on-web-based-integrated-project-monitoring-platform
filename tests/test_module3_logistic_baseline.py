"""
Unit and integration tests for Module 3 — Phase 3: Logistic Regression Baseline.

Verifies:
1. PIT dataset exists.
2. PIT SHA-256 matches expected hash.
3. Cost dataset contains 437 rows.
4. Schedule modeling dataset contains 305 rows.
5. Schedule missing rows are excluded.
6. Required predictor list is correct.
7. Prohibited future variables are absent.
8. State and agency are encoded through the preprocessing pipeline.
9. Unknown categorical levels are handled safely.
10. Logistic Regression uses max_iter >= 2000.
11. random_state = 42.
12. No class_weight balancing is used.
13. Test size = 0.20.
14. Stratification is used.
15. Predictions have probabilities between 0 and 1.
16. Both target models produce all required metrics.
17. Confusion matrices have correct dimensions.
18. Repeated execution is deterministic.
19. PIT source hash remains unchanged.
20. No upstream frozen artifact is modified.
"""

import hashlib
import os
import unittest
import numpy as np
import pandas as pd

from src.models.train_logistic_baseline import (
    CATEGORICAL_PREDICTORS,
    EXPECTED_PIT_SHA256,
    NUMERIC_PREDICTORS,
    PROHIBITED_FIELDS,
    audit_predictor_leakage,
    build_pipeline,
    train_and_evaluate_baselines,
    verify_file_sha256,
)


class TestModule3LogisticBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.report_path = os.path.join(cls.repo_root, "reports", "module3_logistic_regression_results.md")

        with open(cls.pit_path, "rb") as f:
            cls.initial_sha256 = hashlib.sha256(f.read()).hexdigest()

        cls.results = train_and_evaluate_baselines(cls.pit_path)
        cls.cost_res = cls.results["cost"]
        cls.sched_res = cls.results["schedule"]

    # 1. PIT dataset exists
    def test_01_pit_dataset_exists(self):
        self.assertTrue(os.path.exists(self.pit_path))

    # 2. PIT SHA-256 matches expected hash
    def test_02_pit_sha256_matches(self):
        self.assertEqual(self.initial_sha256, EXPECTED_PIT_SHA256)
        self.assertTrue(verify_file_sha256(self.pit_path, EXPECTED_PIT_SHA256))

    # 3. Cost dataset contains 437 rows
    def test_03_cost_dataset_contains_437_rows(self):
        self.assertEqual(self.cost_res["n_total"], 437)
        self.assertEqual(self.cost_res["n_train"] + self.cost_res["n_test"], 437)

    # 4. Schedule modeling dataset contains 305 rows
    def test_04_schedule_modeling_dataset_contains_305_rows(self):
        self.assertEqual(self.sched_res["n_eligible"], 305)
        self.assertEqual(self.sched_res["n_train"] + self.sched_res["n_test"], 305)

    # 5. Schedule missing rows are excluded
    def test_05_schedule_missing_rows_excluded(self):
        self.assertEqual(self.sched_res["n_censored"], 132)
        self.assertEqual(self.sched_res["n_cohort"], 437)
        self.assertEqual(self.sched_res["n_eligible"] + self.sched_res["n_censored"], 437)

    # 6. Required predictor list is correct
    def test_06_required_predictor_list_correct(self):
        expected_numeric = [
            "feat_log_original_cost",
            "feat_original_cost_crore",
            "feat_cumulative_expenditure_crore",
            "feat_expenditure_to_original_cost_ratio",
            "feat_physical_progress_pct",
            "feat_physical_vs_financial_divergence",
            "feat_project_age_months",
            "feat_is_missing_approval_date",
            "feat_remaining_original_duration_months",
            "feat_is_past_original_completion",
        ]
        expected_cat = ["feat_state", "feat_agency"]
        self.assertEqual(NUMERIC_PREDICTORS, expected_numeric)
        self.assertEqual(CATEGORICAL_PREDICTORS, expected_cat)

    # 7. Prohibited future variables are absent
    def test_07_prohibited_future_variables_absent(self):
        all_predictors = NUMERIC_PREDICTORS + CATEGORICAL_PREDICTORS
        for forbidden in PROHIBITED_FIELDS:
            self.assertNotIn(forbidden, all_predictors)
        # Verify audit function passes on predictors
        audit_predictor_leakage(all_predictors)

    # 8. State and agency are encoded through the preprocessing pipeline
    def test_08_state_and_agency_encoded_through_pipeline(self):
        pipe = build_pipeline()
        prep = pipe.named_steps["preprocessor"]
        transformer_names = [t[0] for t in prep.transformers]
        self.assertIn("cat", transformer_names)
        cat_cols = prep.transformers[1][2]
        self.assertEqual(cat_cols, ["feat_state", "feat_agency"])

    # 9. Unknown categorical levels are handled safely
    def test_09_unknown_categorical_levels_handled_safely(self):
        pipe = build_pipeline()
        df = pd.read_csv(self.pit_path)
        all_predictors = NUMERIC_PREDICTORS + CATEGORICAL_PREDICTORS
        X = df[all_predictors].copy()
        y = df["cost_overrun_5pct_2026"].to_numpy()

        # Fit on real data
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pipe.fit(X.iloc[:100], y[:100])

        # Create a test sample with unseen novel state and agency
        novel_sample = X.iloc[:1].copy()
        novel_sample["feat_state"] = "NONEXISTENT_STATE_XYZ"
        novel_sample["feat_agency"] = "NONEXISTENT_AGENCY_ABC"

        # Must not raise error
        probs = pipe.predict_proba(novel_sample)
        self.assertEqual(probs.shape, (1, 2))
        self.assertFalse(np.isnan(probs).any())

    # 10. Logistic Regression uses max_iter >= 2000
    def test_10_max_iter_ge_2000(self):
        pipe = build_pipeline()
        clf = pipe.named_steps["clf"]
        self.assertGreaterEqual(clf.max_iter, 2000)

    # 11. random_state = 42
    def test_11_random_state_42(self):
        pipe = build_pipeline()
        clf = pipe.named_steps["clf"]
        self.assertEqual(clf.random_state, 42)

    # 12. No class_weight balancing is used
    def test_12_no_class_weight_balancing(self):
        pipe = build_pipeline()
        clf = pipe.named_steps["clf"]
        self.assertIsNone(clf.class_weight)

    # 13. Test size = 0.20
    def test_13_test_size_20_pct(self):
        # 437 * 0.20 = 87.4 -> 88 test
        self.assertEqual(self.cost_res["n_test"], 88)
        self.assertEqual(self.cost_res["n_train"], 349)
        # 305 * 0.20 = 61 test
        self.assertEqual(self.sched_res["n_test"], 61)
        self.assertEqual(self.sched_res["n_train"], 244)

    # 14. Stratification is used
    def test_14_stratification_used(self):
        # Cost: overall pos rate ~30.2%
        test_pos_rate_c = self.cost_res["test_pos"] / self.cost_res["n_test"]
        train_pos_rate_c = self.cost_res["train_pos"] / self.cost_res["n_train"]
        self.assertAlmostEqual(test_pos_rate_c, 27 / 88, places=4)
        self.assertAlmostEqual(train_pos_rate_c, 105 / 349, places=4)

        # Schedule: overall pos rate ~84.3%
        test_pos_rate_s = self.sched_res["test_pos"] / self.sched_res["n_test"]
        train_pos_rate_s = self.sched_res["train_pos"] / self.sched_res["n_train"]
        self.assertAlmostEqual(test_pos_rate_s, 51 / 61, places=4)
        self.assertAlmostEqual(train_pos_rate_s, 206 / 244, places=4)

    # 15. Predictions have probabilities between 0 and 1
    def test_15_probabilities_bounded_0_to_1(self):
        # Evaluate probabilities on test fold
        df = pd.read_csv(self.pit_path)
        pipe_c = build_pipeline()
        all_pred = NUMERIC_PREDICTORS + CATEGORICAL_PREDICTORS
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pipe_c.fit(df[all_pred].iloc[:300], df["cost_overrun_5pct_2026"].iloc[:300])
        probs = pipe_c.predict_proba(df[all_pred].iloc[300:])[:, 1]
        self.assertTrue((probs >= 0.0).all())
        self.assertTrue((probs <= 1.0).all())

    # 16. Both target models produce all required metrics
    def test_16_both_models_produce_all_required_metrics(self):
        required_keys = [
            "accuracy", "precision", "recall", "f1", "balanced_accuracy",
            "roc_auc", "pr_auc", "brier_score", "confusion_matrix"
        ]
        for key in required_keys:
            self.assertIn(key, self.cost_res["metrics"])
            self.assertIn(key, self.sched_res["metrics"])

    # 17. Confusion matrices have correct dimensions
    def test_17_confusion_matrices_dimensions(self):
        cm_c = self.cost_res["metrics"]["confusion_matrix"]
        cm_s = self.sched_res["metrics"]["confusion_matrix"]
        self.assertEqual(len(cm_c), 2)
        self.assertEqual(len(cm_c[0]), 2)
        self.assertEqual(len(cm_s), 2)
        self.assertEqual(len(cm_s[0]), 2)
        # Check sum of confusion matrix elements equals n_test
        self.assertEqual(sum(cm_c[0]) + sum(cm_c[1]), 88)
        self.assertEqual(sum(cm_s[0]) + sum(cm_s[1]), 61)

    # 18. Repeated execution is deterministic
    def test_18_repeated_execution_is_deterministic(self):
        res2 = train_and_evaluate_baselines(self.pit_path)
        self.assertEqual(self.results["cost"]["metrics"], res2["cost"]["metrics"])
        self.assertEqual(self.results["schedule"]["metrics"], res2["schedule"]["metrics"])
        self.assertEqual(
            self.results["cost"]["coefficients"]["numeric"],
            res2["cost"]["coefficients"]["numeric"]
        )

    # 19. PIT source hash remains unchanged
    def test_19_pit_source_hash_remains_unchanged(self):
        with open(self.pit_path, "rb") as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(current_hash, EXPECTED_PIT_SHA256)
        self.assertEqual(current_hash, self.initial_sha256)

    # 20. No upstream frozen artifact is modified
    def test_20_no_upstream_frozen_artifact_modified(self):
        frozen_files = {
            "data/processed/table7_june_2025_projects.csv": "9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43",
            "data/processed/table4_july_2025_projects.csv": "ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3",
            "data/processed/table6_july_2026_projects.csv": "6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9",
            "data/processed/project_identity_map.csv": "16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb",
            "data/processed/project_snapshot_panel.csv": "9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47",
        }
        for rel_path, expected_hash in frozen_files.items():
            full_path = os.path.join(self.repo_root, rel_path)
            self.assertTrue(os.path.exists(full_path), f"Missing frozen file: {full_path}")
            with open(full_path, "rb") as f:
                computed = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(
                computed,
                expected_hash,
                f"Frozen file modified: {rel_path} ({computed} != {expected_hash})"
            )


if __name__ == "__main__":
    unittest.main()

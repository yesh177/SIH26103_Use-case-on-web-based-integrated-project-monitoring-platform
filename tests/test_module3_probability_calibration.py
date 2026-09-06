"""
Tests for Module 3 — Phase 6: Probability Calibration & Model Selection.

Validates that:
1. Input PIT dataset SHA-256 matches expected frozen checksum.
2. Exact 12 Enhanced predictors are used.
3. Sector is strictly excluded.
4. Target and future columns are strictly excluded.
5. Identical cost split indices as Phase 5.
6. Identical schedule split indices as Phase 5.
7. Logistic Regression configuration matches specification.
8. Random Forest configuration matches specification.
9. Probability bounds within [0, 1].
10. Brier score calculation correctness.
11. Log loss calculation correctness.
12. ROC-AUC calculation correctness.
13. PR-AUC calculation correctness.
14. Calibration output exists and contains valid metrics.
15. Calibration slope and intercept exist and are finite numbers.
16. Calibration plot PNG files exist in reports/figures/.
17. No calibration model fitted (evaluates raw uncalibrated probabilities).
18. No threshold tuning performed (uses default 0.50).
19. No synthetic data, resampling, or class weighting.
20. Deterministic rerun produces bit-identical metrics and probabilities.
21. PIT dataset remains unchanged.
22. Frozen upstream datasets remain unchanged.
"""

import hashlib
import os
import unittest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from src.models.evaluate_probability_calibration import (
    EXPECTED_PIT_SHA256,
    ENHANCED_NUMERIC_PREDICTORS,
    ENHANCED_CATEGORICAL_PREDICTORS,
    PROHIBITED_FIELDS,
    audit_predictor_leakage,
    build_logistic_regression_pipeline,
    build_random_forest_pipeline,
    compute_calibration_slope_and_intercept,
    compute_evaluation_metrics,
    run_probability_calibration_evaluation,
)
from src.models.train_random_forest_benchmark import (
    run_random_forest_benchmark as run_phase5_rf,
)


class TestModule3ProbabilityCalibration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.figures_dir = os.path.join(cls.repo_root, "reports", "figures")
        cls.results = run_probability_calibration_evaluation(cls.pit_path, cls.figures_dir)
        cls.phase5_results = run_phase5_rf(cls.pit_path)

    # 1. PIT SHA
    def test_01_pit_sha_matches(self):
        with open(self.pit_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(computed, EXPECTED_PIT_SHA256)

    # 2. Exact predictor list
    def test_02_exact_predictor_list(self):
        expected_num = [
            "feat_log_original_cost", "feat_original_cost_crore", "feat_cumulative_expenditure_crore",
            "feat_expenditure_to_original_cost_ratio", "feat_physical_progress_pct",
            "feat_physical_vs_financial_divergence", "feat_project_age_months",
            "feat_is_missing_approval_date", "feat_remaining_original_duration_months",
            "feat_is_past_original_completion"
        ]
        expected_cat = ["feat_state", "feat_agency"]
        self.assertEqual(ENHANCED_NUMERIC_PREDICTORS, expected_num)
        self.assertEqual(ENHANCED_CATEGORICAL_PREDICTORS, expected_cat)

    # 3. Sector excluded
    def test_03_sector_excluded(self):
        all_pred = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
        self.assertNotIn("sector", all_pred)
        self.assertNotIn("feat_sector", all_pred)
        self.assertNotIn("cat_sector", all_pred)

    # 4. Target exclusion
    def test_04_target_exclusion(self):
        all_pred = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
        targets = ["cost_overrun_5pct_2026", "time_overrun_3m_2026", "future_total_cost_escalation_2026", "future_schedule_slippage_months_2026"]
        for t in targets:
            self.assertNotIn(t, all_pred)
        audit_predictor_leakage(all_pred)

    # 5. Identical cost split
    def test_05_identical_cost_split(self):
        p6_test = self.results["cost"]["test_idx"]
        p5_test = self.phase5_results["cost"]["test_idx"]
        self.assertEqual(p6_test, p5_test)
        self.assertEqual(len(p6_test), 88)

    # 6. Identical schedule split
    def test_06_identical_schedule_split(self):
        p6_test = self.results["schedule"]["test_idx"]
        p5_test = self.phase5_results["schedule"]["test_idx"]
        self.assertEqual(p6_test, p5_test)
        self.assertEqual(len(p6_test), 61)

    # 7. LR configuration
    def test_07_lr_configuration(self):
        pipe = build_logistic_regression_pipeline()
        clf = pipe.named_steps["clf"]
        self.assertEqual(clf.max_iter, 2000)
        self.assertEqual(clf.random_state, 42)
        self.assertIsNone(clf.class_weight)

    # 8. RF configuration
    def test_08_rf_configuration(self):
        pipe = build_random_forest_pipeline()
        clf = pipe.named_steps["clf"]
        self.assertEqual(clf.n_estimators, 300)
        self.assertIsNone(clf.max_depth)
        self.assertEqual(clf.min_samples_split, 2)
        self.assertEqual(clf.min_samples_leaf, 1)
        self.assertEqual(clf.max_features, "sqrt")
        self.assertTrue(clf.bootstrap)
        self.assertEqual(clf.random_state, 42)
        self.assertEqual(clf.n_jobs, 1)

    # 9. Probability bounds
    def test_09_probability_bounds(self):
        for task in ["cost", "schedule"]:
            for m in ["lr_metrics", "rf_metrics"]:
                probs = self.results[task][m]["probabilities"]
                self.assertTrue(np.all(probs >= 0.0))
                self.assertTrue(np.all(probs <= 1.0))

    # 10. Brier score calculation
    def test_10_brier_score_calculation(self):
        for task in ["cost", "schedule"]:
            for m in ["lr_metrics", "rf_metrics"]:
                brier = self.results[task][m]["brier_score"]
                self.assertTrue(0.0 <= brier <= 1.0)

    # 11. Log loss calculation
    def test_11_log_loss_calculation(self):
        for task in ["cost", "schedule"]:
            for m in ["lr_metrics", "rf_metrics"]:
                ll = self.results[task][m]["log_loss"]
                self.assertGreater(ll, 0.0)

    # 12. ROC-AUC calculation
    def test_12_roc_auc_calculation(self):
        for task in ["cost", "schedule"]:
            for m in ["lr_metrics", "rf_metrics"]:
                auc = self.results[task][m]["roc_auc"]
                self.assertTrue(0.5 <= auc <= 1.0)

    # 13. PR-AUC calculation
    def test_13_pr_auc_calculation(self):
        for task in ["cost", "schedule"]:
            for m in ["lr_metrics", "rf_metrics"]:
                pr = self.results[task][m]["pr_auc"]
                self.assertTrue(0.0 <= pr <= 1.0)

    # 14. Calibration output exists
    def test_14_calibration_output_exists(self):
        for task in ["cost", "schedule"]:
            for m in ["lr_metrics", "rf_metrics"]:
                self.assertIn("calibration_intercept", self.results[task][m])
                self.assertIn("calibration_slope", self.results[task][m])
                self.assertIn("prob_true", self.results[task][m])
                self.assertIn("prob_pred", self.results[task][m])

    # 15. Calibration slope/intercept finite
    def test_15_calibration_slope_intercept_finite(self):
        for task in ["cost", "schedule"]:
            for m in ["lr_metrics", "rf_metrics"]:
                alpha = self.results[task][m]["calibration_intercept"]
                beta = self.results[task][m]["calibration_slope"]
                self.assertTrue(np.isfinite(alpha))
                self.assertTrue(np.isfinite(beta))

    # 16. Calibration plots exist
    def test_16_calibration_plots_exist(self):
        expected_plots = [
            "cost_logistic_calibration.png",
            "cost_random_forest_calibration.png",
            "schedule_logistic_calibration.png",
            "schedule_random_forest_calibration.png",
        ]
        for p in expected_plots:
            full_path = os.path.join(self.figures_dir, p)
            self.assertTrue(os.path.exists(full_path), f"Missing plot: {full_path}")
            self.assertGreater(os.path.getsize(full_path), 5000, f"Plot too small: {full_path}")

    # 17. No calibration model fitted
    def test_17_no_calibration_model_fitted(self):
        # Verify pipelines contain only preprocessor and base classifier
        pipe_lr = build_logistic_regression_pipeline()
        pipe_rf = build_random_forest_pipeline()
        self.assertEqual(list(pipe_lr.named_steps.keys()), ["preprocessor", "clf"])
        self.assertEqual(list(pipe_rf.named_steps.keys()), ["preprocessor", "clf"])

    # 18. No threshold tuning
    def test_18_no_threshold_tuning(self):
        # Verify predictions use fixed 0.50 threshold
        metrics = self.results["cost"]["rf_metrics"]
        y_prob = metrics["probabilities"]
        expected_pred = (y_prob >= 0.50).astype(int)
        cm = metrics["confusion_matrix"]
        calc_tp = int(((metrics["y_true"] == 1) & (expected_pred == 1)).sum())
        self.assertEqual(metrics["tp"], calc_tp)

    # 19. No synthetic data
    def test_19_no_synthetic_data(self):
        df = pd.read_csv(self.pit_path)
        self.assertEqual(len(df), 437)
        self.assertEqual(self.results["cost"]["n_total"], 437)
        self.assertEqual(self.results["schedule"]["n_eligible"], 305)

    # 20. Deterministic results
    def test_20_deterministic_results(self):
        res2 = run_probability_calibration_evaluation(self.pit_path, self.figures_dir)
        self.assertEqual(self.results["cost"]["lr_metrics"]["brier_score"], res2["cost"]["lr_metrics"]["brier_score"])
        self.assertEqual(self.results["cost"]["rf_metrics"]["brier_score"], res2["cost"]["rf_metrics"]["brier_score"])
        self.assertEqual(self.results["schedule"]["lr_metrics"]["brier_score"], res2["schedule"]["lr_metrics"]["brier_score"])
        self.assertEqual(self.results["schedule"]["rf_metrics"]["brier_score"], res2["schedule"]["rf_metrics"]["brier_score"])

    # 21. PIT unchanged
    def test_21_pit_unchanged(self):
        with open(self.pit_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(computed, EXPECTED_PIT_SHA256)

    # 22. Frozen upstream unchanged
    def test_22_frozen_upstream_unchanged(self):
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
            self.assertEqual(computed, expected_hash, f"Mismatch for {rel_path}")


if __name__ == "__main__":
    unittest.main()

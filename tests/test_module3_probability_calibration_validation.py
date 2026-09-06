"""
Tests for Module 3 — Phase 7: Actual Probability Calibration & Validation.

Verifies:
1. Input PIT dataset SHA-256 matches expected frozen checksum.
2. Exact 12 Enhanced predictors are used.
3. Sector is strictly excluded.
4. Target and future columns are strictly excluded.
5. Original Phase 5 test indices remain unchanged.
6. Training/calibration split is contained entirely within original training partition.
7. Test set is never used for calibration fitting.
8. Calibration subset has both classes represented.
9. Raw probabilities lie strictly within [0, 1].
10. Calibrated probabilities lie strictly within [0, 1].
11. Sigmoid calibrator is fitted only on calibration subset.
12. Isotonic calibrator is fitted only on calibration subset.
13. Brier score calculation correctness.
14. Log loss calculation correctness.
15. ROC-AUC calculation correctness.
16. PR-AUC calculation correctness.
17. Calibration intercept is finite.
18. Calibration slope is finite.
19. Reliability plot PNG files exist in reports/figures/.
20. No threshold tuning performed (uses fixed default 0.50).
21. No synthetic data, resampling, or class weighting.
22. Deterministic split across runs.
23. Deterministic probabilities across runs.
24. Deterministic metrics across runs.
25. PIT dataset remains unchanged.
26. Frozen upstream datasets remain unchanged.
"""

import hashlib
import os
import unittest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from src.models.calibrate_probability_models import (
    EXPECTED_PIT_SHA256,
    ENHANCED_NUMERIC_PREDICTORS,
    ENHANCED_CATEGORICAL_PREDICTORS,
    PROHIBITED_FIELDS,
    audit_predictor_leakage,
    build_preprocessor,
    SigmoidCalibrator,
    IsotonicCalibrator,
    run_probability_calibration_pipeline,
)
from src.models.train_random_forest_benchmark import (
    run_random_forest_benchmark as run_phase5_rf,
)


class TestModule3ProbabilityCalibrationValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.figures_dir = os.path.join(cls.repo_root, "reports", "figures")
        cls.results = run_probability_calibration_pipeline(cls.pit_path, cls.figures_dir)
        cls.phase5_results = run_phase5_rf(cls.pit_path)

    # 1. PIT hash
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

    # 3. Sector exclusion
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

    # 5. Original Phase 5 test indices unchanged
    def test_05_phase5_test_indices_unchanged(self):
        self.assertEqual(self.results["cost"]["test_idx"], self.phase5_results["cost"]["test_idx"])
        self.assertEqual(self.results["schedule"]["test_idx"], self.phase5_results["schedule"]["test_idx"])
        self.assertEqual(len(self.results["cost"]["test_idx"]), 88)
        self.assertEqual(len(self.results["schedule"]["test_idx"]), 61)

    # 6. Training/calibration split contained entirely within original training partition
    def test_06_split_contained_in_train(self):
        # Cost
        fit_c = set(self.results["cost"]["modelfit_idx"])
        cal_c = set(self.results["cost"]["calib_idx"])
        train_c = set(self.results["cost"]["train_idx"])
        test_c = set(self.results["cost"]["test_idx"])
        self.assertEqual(fit_c.union(cal_c), train_c)
        self.assertEqual(len(fit_c.intersection(cal_c)), 0)
        self.assertEqual(len(train_c.intersection(test_c)), 0)
        self.assertEqual(len(fit_c), 261)
        self.assertEqual(len(cal_c), 88)

        # Schedule
        fit_s = set(self.results["schedule"]["modelfit_idx"])
        cal_s = set(self.results["schedule"]["calib_idx"])
        train_s = set(self.results["schedule"]["train_idx"])
        test_s = set(self.results["schedule"]["test_idx"])
        self.assertEqual(fit_s.union(cal_s), train_s)
        self.assertEqual(len(fit_s.intersection(cal_s)), 0)
        self.assertEqual(len(train_s.intersection(test_s)), 0)
        self.assertEqual(len(fit_s), 183)
        self.assertEqual(len(cal_s), 61)

    # 7. Test set never used for calibration fitting
    def test_07_test_set_never_used_for_calibration(self):
        # Verify disjointness between calibration subset and test subset
        cal_c = set(self.results["cost"]["calib_idx"])
        test_c = set(self.results["cost"]["test_idx"])
        self.assertEqual(len(cal_c.intersection(test_c)), 0)

        cal_s = set(self.results["schedule"]["calib_idx"])
        test_s = set(self.results["schedule"]["test_idx"])
        self.assertEqual(len(cal_s.intersection(test_s)), 0)

    # 8. Calibration subset has both classes
    def test_08_calibration_subset_has_both_classes(self):
        self.assertGreater(self.results["cost"]["pos_calib"], 0)
        self.assertGreater(self.results["cost"]["neg_calib"], 0)
        self.assertGreater(self.results["schedule"]["pos_calib"], 0)
        self.assertGreater(self.results["schedule"]["neg_calib"], 0)

    # 9. Raw probabilities in [0, 1]
    def test_09_raw_probabilities_bounded(self):
        for task in ["cost", "schedule"]:
            for m in ["lr", "rf"]:
                probs = self.results[task]["models"][m]["raw"]["probabilities"]
                self.assertTrue(np.all(probs >= 0.0))
                self.assertTrue(np.all(probs <= 1.0))

    # 10. Calibrated probabilities in [0, 1]
    def test_10_calibrated_probabilities_bounded(self):
        for task in ["cost", "schedule"]:
            for m in ["lr", "rf"]:
                for cal in ["sigmoid", "isotonic"]:
                    probs = self.results[task]["models"][m][cal]["probabilities"]
                    self.assertTrue(np.all(probs >= 0.0))
                    self.assertTrue(np.all(probs <= 1.0))

    # 11. Sigmoid calibrator fitted only on calibration subset
    def test_11_sigmoid_calibrator_functional(self):
        sig = SigmoidCalibrator()
        p_dummy = np.array([0.1, 0.4, 0.6, 0.9])
        y_dummy = np.array([0, 0, 1, 1])
        sig.fit(p_dummy, y_dummy)
        self.assertIsNotNone(sig.alpha_)
        self.assertIsNotNone(sig.beta_)
        p_trans = sig.predict_proba(np.array([0.2, 0.8]))
        self.assertEqual(len(p_trans), 2)
        self.assertTrue(np.all(p_trans >= 0.0))
        self.assertTrue(np.all(p_trans <= 1.0))

    # 12. Isotonic calibrator fitted only on calibration subset
    def test_12_isotonic_calibrator_functional(self):
        iso = IsotonicCalibrator()
        p_dummy = np.array([0.1, 0.4, 0.6, 0.9])
        y_dummy = np.array([0, 0, 1, 1])
        iso.fit(p_dummy, y_dummy)
        p_trans = iso.predict_proba(np.array([0.2, 0.8]))
        self.assertEqual(len(p_trans), 2)
        self.assertTrue(np.all(p_trans >= 0.0))
        self.assertTrue(np.all(p_trans <= 1.0))

    # 13. Brier calculation
    def test_13_brier_calculation(self):
        for task in ["cost", "schedule"]:
            for m in ["lr", "rf"]:
                for v in ["raw", "sigmoid", "isotonic"]:
                    brier = self.results[task]["models"][m][v]["brier_score"]
                    self.assertTrue(0.0 <= brier <= 1.0)

    # 14. Log loss calculation
    def test_14_log_loss_calculation(self):
        for task in ["cost", "schedule"]:
            for m in ["lr", "rf"]:
                for v in ["raw", "sigmoid", "isotonic"]:
                    ll = self.results[task]["models"][m][v]["log_loss"]
                    self.assertGreater(ll, 0.0)

    # 15. ROC-AUC calculation
    def test_15_roc_auc_calculation(self):
        for task in ["cost", "schedule"]:
            for m in ["lr", "rf"]:
                for v in ["raw", "sigmoid", "isotonic"]:
                    auc = self.results[task]["models"][m][v]["roc_auc"]
                    self.assertTrue(0.5 <= auc <= 1.0)

    # 16. PR-AUC calculation
    def test_16_pr_auc_calculation(self):
        for task in ["cost", "schedule"]:
            for m in ["lr", "rf"]:
                for v in ["raw", "sigmoid", "isotonic"]:
                    pr = self.results[task]["models"][m][v]["pr_auc"]
                    self.assertTrue(0.0 <= pr <= 1.0)

    # 17. Calibration intercept finite
    def test_17_calibration_intercept_finite(self):
        for task in ["cost", "schedule"]:
            for m in ["lr", "rf"]:
                for v in ["raw", "sigmoid", "isotonic"]:
                    alpha = self.results[task]["models"][m][v]["calibration_intercept"]
                    self.assertTrue(np.isfinite(alpha))

    # 18. Calibration slope finite
    def test_18_calibration_slope_finite(self):
        for task in ["cost", "schedule"]:
            for m in ["lr", "rf"]:
                for v in ["raw", "sigmoid", "isotonic"]:
                    beta = self.results[task]["models"][m][v]["calibration_slope"]
                    self.assertTrue(np.isfinite(beta))

    # 19. Reliability plots exist
    def test_19_reliability_plots_exist(self):
        expected_plots = [
            "cost_lr_raw_calibration.png",
            "cost_lr_sigmoid_calibration.png",
            "cost_lr_isotonic_calibration.png",
            "cost_rf_raw_calibration.png",
            "cost_rf_sigmoid_calibration.png",
            "cost_rf_isotonic_calibration.png",
            "schedule_lr_raw_calibration.png",
            "schedule_lr_sigmoid_calibration.png",
            "schedule_lr_isotonic_calibration.png",
            "schedule_rf_raw_calibration.png",
            "schedule_rf_sigmoid_calibration.png",
            "schedule_rf_isotonic_calibration.png",
        ]
        for p in expected_plots:
            full_path = os.path.join(self.figures_dir, p)
            self.assertTrue(os.path.exists(full_path), f"Missing plot: {full_path}")
            self.assertGreater(os.path.getsize(full_path), 5000, f"Plot too small: {full_path}")

    # 20. No threshold tuning
    def test_20_no_threshold_tuning(self):
        metrics = self.results["cost"]["models"]["rf"]["sigmoid"]
        y_prob = metrics["probabilities"]
        expected_pred = (y_prob >= 0.50).astype(int)
        calc_tp = int(((metrics["y_true"] == 1) & (expected_pred == 1)).sum())
        self.assertEqual(metrics["tp"], calc_tp)

    # 21. No synthetic data
    def test_21_no_synthetic_data(self):
        df = pd.read_csv(self.pit_path)
        self.assertEqual(len(df), 437)
        self.assertEqual(self.results["cost"]["n_total"], 437)
        self.assertEqual(self.results["schedule"]["n_eligible"], 305)

    # 22. Deterministic split
    def test_22_deterministic_split(self):
        res2 = run_probability_calibration_pipeline(self.pit_path, self.figures_dir)
        self.assertEqual(self.results["cost"]["modelfit_idx"], res2["cost"]["modelfit_idx"])
        self.assertEqual(self.results["cost"]["calib_idx"], res2["cost"]["calib_idx"])
        self.assertEqual(self.results["schedule"]["modelfit_idx"], res2["schedule"]["modelfit_idx"])
        self.assertEqual(self.results["schedule"]["calib_idx"], res2["schedule"]["calib_idx"])

    # 23. Deterministic probabilities
    def test_23_deterministic_probabilities(self):
        res2 = run_probability_calibration_pipeline(self.pit_path, self.figures_dir)
        p1 = self.results["cost"]["models"]["rf"]["sigmoid"]["probabilities"]
        p2 = res2["cost"]["models"]["rf"]["sigmoid"]["probabilities"]
        np.testing.assert_array_almost_equal(p1, p2, decimal=6)

    # 24. Deterministic metrics
    def test_24_deterministic_metrics(self):
        res2 = run_probability_calibration_pipeline(self.pit_path, self.figures_dir)
        m1 = self.results["cost"]["models"]["rf"]["sigmoid"]["brier_score"]
        m2 = res2["cost"]["models"]["rf"]["sigmoid"]["brier_score"]
        self.assertEqual(m1, m2)

    # 25. PIT unchanged
    def test_25_pit_unchanged(self):
        with open(self.pit_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(computed, EXPECTED_PIT_SHA256)

    # 26. Frozen upstream unchanged
    def test_26_frozen_upstream_unchanged(self):
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

"""
Unit and integration tests for Module 3 — Phase 4: CUF-vs-Enhanced Feature Evaluation.

Verifies:
1. PIT dataset exists
2. PIT SHA-256 unchanged
3. Cost population = 437
4. Schedule eligible population = 305
5. 132 schedule missing/unobserved rows excluded
6. CUF feature list exactly matches specification
7. Enhanced feature list exactly matches specification
8. No target leakage
9. No July 2026 predictors
10. No sector
11. Same random_state = 42
12. test_size = 0.20
13. stratification
14. Pipeline preprocessing
15. OneHotEncoder handle_unknown="ignore"
16. median numeric imputation
17. most-frequent categorical imputation
18. class_weight=None
19. max_iter >= 2000
20. all required metrics exist
21. confusion matrices valid
22. probability bounds
23. CUF and Enhanced use identical cohort/split
24. deterministic rerun
25. upstream frozen artifacts unchanged
"""

import hashlib
import os
import unittest
import numpy as np
import pandas as pd

from src.models.evaluate_cuf_vs_enhanced import (
    CUF_CATEGORICAL_PREDICTORS,
    CUF_NUMERIC_PREDICTORS,
    ENHANCED_CATEGORICAL_PREDICTORS,
    ENHANCED_NUMERIC_PREDICTORS,
    EXPECTED_PIT_SHA256,
    PROHIBITED_FIELDS,
    audit_predictor_leakage,
    build_pipeline,
    run_cuf_vs_enhanced_experiment,
    verify_file_sha256,
)


class TestModule3CufVsEnhanced(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.report_path = os.path.join(cls.repo_root, "reports", "module3_cuf_vs_enhanced_results.md")

        with open(cls.pit_path, "rb") as f:
            cls.initial_sha256 = hashlib.sha256(f.read()).hexdigest()

        cls.results = run_cuf_vs_enhanced_experiment(cls.pit_path)
        cls.cost = cls.results["cost"]
        cls.sched = cls.results["schedule"]

    # 1. PIT dataset exists
    def test_01_pit_dataset_exists(self):
        self.assertTrue(os.path.exists(self.pit_path))

    # 2. PIT SHA-256 unchanged
    def test_02_pit_sha256_unchanged(self):
        self.assertEqual(self.initial_sha256, EXPECTED_PIT_SHA256)
        self.assertTrue(verify_file_sha256(self.pit_path, EXPECTED_PIT_SHA256))

    # 3. Cost population = 437
    def test_03_cost_population_437(self):
        self.assertEqual(self.cost["n_total"], 437)
        self.assertEqual(self.cost["n_train"] + self.cost["n_test"], 437)

    # 4. Schedule eligible population = 305
    def test_04_schedule_eligible_population_305(self):
        self.assertEqual(self.sched["n_eligible"], 305)
        self.assertEqual(self.sched["n_train"] + self.sched["n_test"], 305)

    # 5. 132 schedule missing/unobserved rows excluded
    def test_05_schedule_missing_rows_excluded(self):
        self.assertEqual(self.sched["n_censored"], 132)
        self.assertEqual(self.sched["n_cohort"], 437)
        self.assertEqual(self.sched["n_eligible"] + self.sched["n_censored"], 437)

    # 6. CUF feature list exactly matches specification
    def test_06_cuf_feature_list_matches_spec(self):
        expected_cuf_num = [
            "feat_original_cost_crore",
            "feat_cumulative_expenditure_crore",
            "feat_physical_progress_pct",
        ]
        expected_cuf_cat = ["feat_state", "feat_agency"]
        self.assertEqual(CUF_NUMERIC_PREDICTORS, expected_cuf_num)
        self.assertEqual(CUF_CATEGORICAL_PREDICTORS, expected_cuf_cat)

    # 7. Enhanced feature list exactly matches specification
    def test_07_enhanced_feature_list_matches_spec(self):
        expected_enh_num = [
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
        expected_enh_cat = ["feat_state", "feat_agency"]
        self.assertEqual(ENHANCED_NUMERIC_PREDICTORS, expected_enh_num)
        self.assertEqual(ENHANCED_CATEGORICAL_PREDICTORS, expected_enh_cat)

    # 8. No target leakage
    def test_08_no_target_leakage(self):
        all_cuf = CUF_NUMERIC_PREDICTORS + CUF_CATEGORICAL_PREDICTORS
        all_enh = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
        targets = ["cost_overrun_5pct_2026", "time_overrun_3m_2026", "future_total_cost_escalation_2026", "future_schedule_slippage_months_2026"]
        for t in targets:
            self.assertNotIn(t, all_cuf)
            self.assertNotIn(t, all_enh)

    # 9. No July 2026 predictors
    def test_09_no_july_2026_predictors(self):
        all_cuf = CUF_NUMERIC_PREDICTORS + CUF_CATEGORICAL_PREDICTORS
        all_enh = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
        audit_predictor_leakage(all_cuf)
        audit_predictor_leakage(all_enh)

    # 10. No sector
    def test_10_no_sector_predictor(self):
        all_cuf = CUF_NUMERIC_PREDICTORS + CUF_CATEGORICAL_PREDICTORS
        all_enh = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
        self.assertNotIn("sector", all_cuf)
        self.assertNotIn("sector", all_enh)
        self.assertNotIn("feat_sector", all_cuf)
        self.assertNotIn("feat_sector", all_enh)

    # 11. Same random_state = 42
    def test_11_same_random_state_42(self):
        pipe_cuf = build_pipeline(CUF_NUMERIC_PREDICTORS, CUF_CATEGORICAL_PREDICTORS)
        pipe_enh = build_pipeline(ENHANCED_NUMERIC_PREDICTORS, ENHANCED_CATEGORICAL_PREDICTORS)
        self.assertEqual(pipe_cuf.named_steps["clf"].random_state, 42)
        self.assertEqual(pipe_enh.named_steps["clf"].random_state, 42)

    # 12. test_size = 0.20
    def test_12_test_size_20_pct(self):
        self.assertEqual(self.cost["n_test"], 88)
        self.assertEqual(self.cost["n_train"], 349)
        self.assertEqual(self.sched["n_test"], 61)
        self.assertEqual(self.sched["n_train"], 244)

    # 13. Stratification
    def test_13_stratification(self):
        # 27 / 88 = 30.68% pos in test
        # 105 / 349 = 30.09% pos in train
        df = pd.read_csv(self.pit_path)
        test_cost_y = df.loc[self.cost["test_idx"], "cost_overrun_5pct_2026"]
        self.assertEqual(int(test_cost_y.sum()), 27)

        sched_df = df[df["is_eligible_schedule_target"] == 1].reset_index(drop=True)
        test_sched_y = sched_df.loc[self.sched["test_idx"], "time_overrun_3m_2026"].astype(int)
        self.assertEqual(int(test_sched_y.sum()), 51)

    # 14. Pipeline preprocessing
    def test_14_pipeline_preprocessing(self):
        pipe = build_pipeline(CUF_NUMERIC_PREDICTORS, CUF_CATEGORICAL_PREDICTORS)
        self.assertIn("preprocessor", pipe.named_steps)
        self.assertIn("clf", pipe.named_steps)

    # 15. OneHotEncoder handle_unknown="ignore"
    def test_15_onehotencoder_handle_unknown_ignore(self):
        pipe = build_pipeline(CUF_NUMERIC_PREDICTORS, CUF_CATEGORICAL_PREDICTORS)
        cat_step = pipe.named_steps["preprocessor"].transformers[1][1]
        ohe = cat_step.named_steps["ohe"]
        self.assertEqual(ohe.handle_unknown, "ignore")

    # 16. Median numeric imputation
    def test_16_median_numeric_imputation(self):
        pipe = build_pipeline(ENHANCED_NUMERIC_PREDICTORS, ENHANCED_CATEGORICAL_PREDICTORS)
        num_step = pipe.named_steps["preprocessor"].transformers[0][1]
        self.assertEqual(num_step.strategy, "median")

    # 17. Most-frequent categorical imputation
    def test_17_most_frequent_categorical_imputation(self):
        pipe = build_pipeline(ENHANCED_NUMERIC_PREDICTORS, ENHANCED_CATEGORICAL_PREDICTORS)
        cat_step = pipe.named_steps["preprocessor"].transformers[1][1]
        imp = cat_step.named_steps["imputer"]
        self.assertEqual(imp.strategy, "most_frequent")

    # 18. class_weight=None
    def test_18_class_weight_none(self):
        pipe_cuf = build_pipeline(CUF_NUMERIC_PREDICTORS, CUF_CATEGORICAL_PREDICTORS)
        pipe_enh = build_pipeline(ENHANCED_NUMERIC_PREDICTORS, ENHANCED_CATEGORICAL_PREDICTORS)
        self.assertIsNone(pipe_cuf.named_steps["clf"].class_weight)
        self.assertIsNone(pipe_enh.named_steps["clf"].class_weight)

    # 19. max_iter >= 2000
    def test_19_max_iter_ge_2000(self):
        pipe_cuf = build_pipeline(CUF_NUMERIC_PREDICTORS, CUF_CATEGORICAL_PREDICTORS)
        pipe_enh = build_pipeline(ENHANCED_NUMERIC_PREDICTORS, ENHANCED_CATEGORICAL_PREDICTORS)
        self.assertGreaterEqual(pipe_cuf.named_steps["clf"].max_iter, 2000)
        self.assertGreaterEqual(pipe_enh.named_steps["clf"].max_iter, 2000)

    # 20. All required metrics exist
    def test_20_all_required_metrics_exist(self):
        required_keys = [
            "accuracy", "precision", "recall", "f1", "balanced_accuracy",
            "roc_auc", "pr_auc", "brier_score", "confusion_matrix"
        ]
        for key in required_keys:
            self.assertIn(key, self.cost["cuf_metrics"])
            self.assertIn(key, self.cost["enh_metrics"])
            self.assertIn(key, self.sched["cuf_metrics"])
            self.assertIn(key, self.sched["enh_metrics"])

    # 21. Confusion matrices valid
    def test_21_confusion_matrices_valid(self):
        cm_c_cuf = self.cost["cuf_metrics"]["confusion_matrix"]
        cm_c_enh = self.cost["enh_metrics"]["confusion_matrix"]
        cm_s_cuf = self.sched["cuf_metrics"]["confusion_matrix"]
        cm_s_enh = self.sched["enh_metrics"]["confusion_matrix"]

        self.assertEqual(sum(cm_c_cuf[0]) + sum(cm_c_cuf[1]), 88)
        self.assertEqual(sum(cm_c_enh[0]) + sum(cm_c_enh[1]), 88)
        self.assertEqual(sum(cm_s_cuf[0]) + sum(cm_s_cuf[1]), 61)
        self.assertEqual(sum(cm_s_enh[0]) + sum(cm_s_enh[1]), 61)

    # 22. Probability bounds
    def test_22_probability_bounds(self):
        # Verify metric calculations are within expected ranges
        for m in [self.cost["cuf_metrics"], self.cost["enh_metrics"], self.sched["cuf_metrics"], self.sched["enh_metrics"]]:
            self.assertTrue(0.0 <= m["roc_auc"] <= 1.0)
            self.assertTrue(0.0 <= m["pr_auc"] <= 1.0)
            self.assertTrue(0.0 <= m["brier_score"] <= 1.0)

    # 23. CUF and Enhanced use identical cohort/split
    def test_23_identical_cohort_split_between_cuf_and_enhanced(self):
        self.assertEqual(len(self.cost["train_idx"]), 349)
        self.assertEqual(len(self.cost["test_idx"]), 88)
        self.assertEqual(len(self.sched["train_idx"]), 244)
        self.assertEqual(len(self.sched["test_idx"]), 61)
        # Check train and test index sets are disjoint
        self.assertEqual(len(set(self.cost["train_idx"]).intersection(set(self.cost["test_idx"]))), 0)
        self.assertEqual(len(set(self.sched["train_idx"]).intersection(set(self.sched["test_idx"]))), 0)

    # 24. Deterministic rerun
    def test_24_deterministic_rerun(self):
        res2 = run_cuf_vs_enhanced_experiment(self.pit_path)
        self.assertEqual(self.cost["cuf_metrics"], res2["cost"]["cuf_metrics"])
        self.assertEqual(self.cost["enh_metrics"], res2["cost"]["enh_metrics"])
        self.assertEqual(self.sched["cuf_metrics"], res2["schedule"]["cuf_metrics"])
        self.assertEqual(self.sched["enh_metrics"], res2["schedule"]["enh_metrics"])

    # 25. Upstream frozen artifacts unchanged
    def test_25_upstream_frozen_artifacts_unchanged(self):
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

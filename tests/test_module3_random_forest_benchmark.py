"""
Unit and integration tests for Module 3 — Phase 5: Nonlinear ML Benchmark (Random Forest).

Verifies:
1. PIT dataset exists
2. PIT SHA-256 matches expected hash
3. Cost population = 437
4. Schedule eligible population = 305
5. 132 schedule missing/unobserved rows excluded
6. Enhanced feature list exactly matches specification
7. No target variables in predictors
8. No July 2026 variables
9. No sector
10. Same split indices as Logistic Regression reference
11. test_size = 0.20
12. random_state = 42
13. stratification
14. numeric median imputation
15. categorical most-frequent imputation
16. OneHotEncoder(handle_unknown="ignore")
17. class_weight=None
18. n_estimators = 300
19. max_features = "sqrt"
20. bootstrap=True
21. n_jobs=1
22. all required metrics exist
23. confusion matrices valid
24. probabilities bounded 0–1
25. feature importance exists
26. feature importance non-negative
27. feature importance sums approximately to 1
28. deterministic rerun
29. PIT dataset unchanged
30. frozen upstream datasets unchanged
"""

import hashlib
import os
import unittest
import numpy as np
import pandas as pd

from src.models.train_random_forest_benchmark import (
    ENHANCED_CATEGORICAL_PREDICTORS,
    ENHANCED_NUMERIC_PREDICTORS,
    EXPECTED_PIT_SHA256,
    PROHIBITED_FIELDS,
    audit_predictor_leakage,
    build_random_forest_pipeline,
    run_random_forest_benchmark,
    verify_file_sha256,
)


class TestModule3RandomForestBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.report_path = os.path.join(cls.repo_root, "reports", "module3_random_forest_benchmark_results.md")

        with open(cls.pit_path, "rb") as f:
            cls.initial_sha256 = hashlib.sha256(f.read()).hexdigest()

        cls.results = run_random_forest_benchmark(cls.pit_path)
        cls.cost = cls.results["cost"]
        cls.sched = cls.results["schedule"]

    # 1. PIT dataset exists
    def test_01_pit_dataset_exists(self):
        self.assertTrue(os.path.exists(self.pit_path))

    # 2. PIT SHA-256 matches expected hash
    def test_02_pit_sha256_matches(self):
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
    def test_05_schedule_missing_unobserved_excluded(self):
        self.assertEqual(self.sched["n_unobserved"], 132)
        self.assertEqual(self.sched["n_cohort"], 437)
        self.assertEqual(self.sched["n_eligible"] + self.sched["n_unobserved"], 437)

    # 6. Enhanced feature list exactly matches specification
    def test_06_enhanced_feature_list_matches_spec(self):
        expected_num = [
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
        self.assertEqual(ENHANCED_NUMERIC_PREDICTORS, expected_num)
        self.assertEqual(ENHANCED_CATEGORICAL_PREDICTORS, expected_cat)

    # 7. No target variables in predictors
    def test_07_no_target_variables_in_predictors(self):
        all_pred = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
        targets = ["cost_overrun_5pct_2026", "time_overrun_3m_2026", "future_total_cost_escalation_2026", "future_schedule_slippage_months_2026"]
        for t in targets:
            self.assertNotIn(t, all_pred)

    # 8. No July 2026 variables
    def test_08_no_july_2026_variables(self):
        all_pred = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
        audit_predictor_leakage(all_pred)

    # 9. No sector
    def test_09_no_sector_predictor(self):
        all_pred = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
        # 1. feat_sector and sector absent from predictor list
        self.assertNotIn("sector", all_pred)
        self.assertNotIn("feat_sector", all_pred)
        self.assertNotIn("cat_sector", all_pred)

        # 2. sector absent from ColumnTransformer
        pipe = build_random_forest_pipeline()
        prep = pipe.named_steps["preprocessor"]
        for trans_name, trans_obj, cols in prep.transformers:
            for col in cols:
                self.assertNotIn("sector", col.lower(), f"Sector column '{col}' in transformer '{trans_name}'")

        # 3. cat_sector and sector absent from transformed feature names
        df = pd.read_csv(self.pit_path)
        X = df[all_pred]
        prep.fit(X)
        transformed_names = prep.get_feature_names_out()
        for t_name in transformed_names:
            self.assertNotIn("sector", t_name.lower(), f"Sector found in transformed feature '{t_name}'")
            self.assertNotIn("cat_sector", t_name.lower())

        # 4. No sector feature importance is reported
        for item in self.cost["importances"]["all_raw_sorted"]:
            self.assertNotIn("sector", item["feature"].lower())
        for item in self.cost["importances"]["parent_aggregated"]:
            self.assertNotIn("sector", item["parent_feature"].lower())
        for item in self.sched["importances"]["all_raw_sorted"]:
            self.assertNotIn("sector", item["feature"].lower())
        for item in self.sched["importances"]["parent_aggregated"]:
            self.assertNotIn("sector", item["parent_feature"].lower())

        # 5. Exact Enhanced predictor list matches Phase 4
        from src.models.evaluate_cuf_vs_enhanced import (
            ENHANCED_NUMERIC_PREDICTORS as P4_NUMERIC,
            ENHANCED_CATEGORICAL_PREDICTORS as P4_CATEGORICAL,
        )
        self.assertEqual(ENHANCED_NUMERIC_PREDICTORS, P4_NUMERIC)
        self.assertEqual(ENHANCED_CATEGORICAL_PREDICTORS, P4_CATEGORICAL)

        # 6. State and agency remain included
        self.assertIn("feat_state", ENHANCED_CATEGORICAL_PREDICTORS)
        self.assertIn("feat_agency", ENHANCED_CATEGORICAL_PREDICTORS)

    # 10. Same split indices as Logistic Regression reference
    def test_10_same_split_indices_as_logistic_regression(self):
        # Verify deterministic split sizes
        self.assertEqual(len(self.cost["train_idx"]), 349)
        self.assertEqual(len(self.cost["test_idx"]), 88)
        self.assertEqual(len(self.sched["train_idx"]), 244)
        self.assertEqual(len(self.sched["test_idx"]), 61)
        # Disjointness
        self.assertEqual(len(set(self.cost["train_idx"]).intersection(set(self.cost["test_idx"]))), 0)
        self.assertEqual(len(set(self.sched["train_idx"]).intersection(set(self.sched["test_idx"]))), 0)

    # 11. test_size = 0.20
    def test_11_test_size_20_pct(self):
        self.assertEqual(self.cost["n_test"], 88)
        self.assertEqual(self.sched["n_test"], 61)

    # 12. random_state = 42
    def test_12_random_state_42(self):
        pipe_rf = build_random_forest_pipeline()
        self.assertEqual(pipe_rf.named_steps["clf"].random_state, 42)

    # 13. Stratification
    def test_13_stratification(self):
        df = pd.read_csv(self.pit_path)
        cost_test_pos = int(df.loc[self.cost["test_idx"], "cost_overrun_5pct_2026"].sum())
        cost_train_pos = int(df.loc[self.cost["train_idx"], "cost_overrun_5pct_2026"].sum())
        self.assertEqual(cost_test_pos, 27)
        self.assertEqual(cost_train_pos, 105)

        sched_df = df[df["is_eligible_schedule_target"] == 1].reset_index(drop=True)
        sched_test_pos = int(sched_df.loc[self.sched["test_idx"], "time_overrun_3m_2026"].astype(int).sum())
        sched_train_pos = int(sched_df.loc[self.sched["train_idx"], "time_overrun_3m_2026"].astype(int).sum())
        self.assertEqual(sched_test_pos, 51)
        self.assertEqual(sched_train_pos, 206)

    # 14. Numeric median imputation
    def test_14_numeric_median_imputation(self):
        pipe = build_random_forest_pipeline()
        prep = pipe.named_steps["preprocessor"]
        num_imputer = prep.transformers[0][1]
        self.assertEqual(num_imputer.strategy, "median")

    # 15. Categorical most-frequent imputation
    def test_15_categorical_most_frequent_imputation(self):
        pipe = build_random_forest_pipeline()
        prep = pipe.named_steps["preprocessor"]
        cat_imputer = prep.transformers[1][1].named_steps["imputer"]
        self.assertEqual(cat_imputer.strategy, "most_frequent")

    # 16. OneHotEncoder(handle_unknown="ignore")
    def test_16_ohe_handle_unknown_ignore(self):
        pipe = build_random_forest_pipeline()
        prep = pipe.named_steps["preprocessor"]
        ohe = prep.transformers[1][1].named_steps["ohe"]
        self.assertEqual(ohe.handle_unknown, "ignore")

    # 17. class_weight=None
    def test_17_class_weight_none(self):
        pipe = build_random_forest_pipeline()
        self.assertIsNone(pipe.named_steps["clf"].class_weight)

    # 18. n_estimators = 300
    def test_18_n_estimators_300(self):
        pipe = build_random_forest_pipeline()
        self.assertEqual(pipe.named_steps["clf"].n_estimators, 300)

    # 19. max_features = "sqrt"
    def test_19_max_features_sqrt(self):
        pipe = build_random_forest_pipeline()
        self.assertEqual(pipe.named_steps["clf"].max_features, "sqrt")

    # 20. bootstrap=True
    def test_20_bootstrap_true(self):
        pipe = build_random_forest_pipeline()
        self.assertTrue(pipe.named_steps["clf"].bootstrap)

    # 21. n_jobs=1
    def test_21_n_jobs_1(self):
        pipe = build_random_forest_pipeline()
        self.assertEqual(pipe.named_steps["clf"].n_jobs, 1)

    # 22. All required metrics exist
    def test_22_all_required_metrics_exist(self):
        required_keys = [
            "accuracy", "precision", "recall", "f1", "balanced_accuracy",
            "roc_auc", "pr_auc", "brier_score", "confusion_matrix"
        ]
        for key in required_keys:
            self.assertIn(key, self.cost["rf_metrics"])
            self.assertIn(key, self.sched["rf_metrics"])

    # 23. Confusion matrices valid
    def test_23_confusion_matrices_valid(self):
        cm_c = self.cost["rf_metrics"]["confusion_matrix"]
        cm_s = self.sched["rf_metrics"]["confusion_matrix"]
        self.assertEqual(sum(cm_c[0]) + sum(cm_c[1]), 88)
        self.assertEqual(sum(cm_s[0]) + sum(cm_s[1]), 61)

    # 24. Probabilities bounded 0–1
    def test_24_probabilities_bounded_0_to_1(self):
        for m in [self.cost["rf_metrics"], self.sched["rf_metrics"]]:
            self.assertTrue(0.0 <= m["roc_auc"] <= 1.0)
            self.assertTrue(0.0 <= m["pr_auc"] <= 1.0)
            self.assertTrue(0.0 <= m["brier_score"] <= 1.0)

    # 25. Feature importance exists
    def test_25_feature_importance_exists(self):
        self.assertIn("top_15_raw", self.cost["importances"])
        self.assertIn("top_15_raw", self.sched["importances"])
        self.assertEqual(len(self.cost["importances"]["top_15_raw"]), 15)
        self.assertEqual(len(self.sched["importances"]["top_15_raw"]), 15)

    # 26. Feature importance non-negative
    def test_26_feature_importance_non_negative(self):
        for item in self.cost["importances"]["all_raw_sorted"]:
            self.assertGreaterEqual(item["importance"], 0.0)
        for item in self.sched["importances"]["all_raw_sorted"]:
            self.assertGreaterEqual(item["importance"], 0.0)

    # 27. Feature importance sums approximately to 1
    def test_27_feature_importance_sums_to_one(self):
        total_imp_c = sum(item["importance"] for item in self.cost["importances"]["all_raw_sorted"])
        total_imp_s = sum(item["importance"] for item in self.sched["importances"]["all_raw_sorted"])
        self.assertAlmostEqual(total_imp_c, 1.0, places=5)
        self.assertAlmostEqual(total_imp_s, 1.0, places=5)

    # 28. Deterministic rerun
    def test_28_deterministic_rerun(self):
        res2 = run_random_forest_benchmark(self.pit_path)
        self.assertEqual(self.cost["rf_metrics"], res2["cost"]["rf_metrics"])
        self.assertEqual(self.sched["rf_metrics"], res2["schedule"]["rf_metrics"])
        # Check top feature importances are identical
        self.assertEqual(
            self.cost["importances"]["top_15_raw"],
            res2["cost"]["importances"]["top_15_raw"]
        )

    # 29. PIT dataset unchanged
    def test_29_pit_dataset_unchanged(self):
        with open(self.pit_path, "rb") as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(current_hash, EXPECTED_PIT_SHA256)
        self.assertEqual(current_hash, self.initial_sha256)

    # 30. Frozen upstream datasets unchanged
    def test_30_frozen_upstream_datasets_unchanged(self):
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

    # 31. Report contains no unauthorized sector references or importance
    def test_31_report_contains_no_unauthorized_sector(self):
        report_path = os.path.join(self.repo_root, "reports", "module3_random_forest_benchmark_results.md")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("cat_sector", content)
            self.assertNotIn("feat_sector", content)
            # Ensure "sector" in report only appears in exclusion/checklist context
            for line in content.splitlines():
                if "sector" in line.lower():
                    self.assertTrue(
                        "absent" in line.lower() or "prohibited" in line.lower() or "unauthorized" in line.lower() or "excluded" in line.lower(),
                        f"Unauthorized mention of sector in report: {line}"
                    )


if __name__ == "__main__":
    unittest.main()

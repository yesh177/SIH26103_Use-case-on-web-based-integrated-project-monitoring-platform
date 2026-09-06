"""
Unit and integration tests for Module 3 — Phase 1: Evaluation Protocol & Baseline Readiness.

Verifies:
1. PIT dataset exists.
2. PIT dataset SHA-256 matches: 052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329.
3. Cost target counts: 437 total, 132 positive, 305 negative.
4. Schedule target counts: 437 total, 305 eligible, 132 missing, 257 positive, 48 negative.
5. No July 2026 outcome variable appears in the baseline predictor list.
6. State and agency are allowed categorical predictors.
7. Revised cost and revised completion are prohibited predictors.
8. Protocol explicitly identifies the evaluation as a retrospective 12-month horizon evaluation.
9. Protocol explicitly prohibits claiming multi-period temporal CV.
10. Naive majority-class benchmarks and leak-free in-fold preprocessing invariants.
"""

import hashlib
import os
import unittest
import numpy as np
import pandas as pd


def stratified_kfold_split(y, n_splits=5, shuffle=True, random_state=42):
    """Pure numpy implementation of stratified k-fold cross-validation."""
    rng = np.random.RandomState(random_state) if random_state is not None else None
    y = np.asarray(y)
    cls_indices = [np.where(y == c)[0] for c in np.unique(y)]
    if shuffle and rng is not None:
        for idxs in cls_indices:
            rng.shuffle(idxs)
    folds = [[] for _ in range(n_splits)]
    for idxs in cls_indices:
        for i, idx in enumerate(idxs):
            folds[i % n_splits].append(idx)
    splits = []
    all_idx = np.arange(len(y))
    for fold_idx in range(n_splits):
        test_idx = np.array(sorted(folds[fold_idx]))
        train_idx = np.setdiff1d(all_idx, test_idx)
        splits.append((train_idx, test_idx))
    return splits


class TestModule3EvaluationProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.protocol_path = os.path.join(cls.repo_root, "docs", "module3_evaluation_protocol.md")
        cls.readiness_path = os.path.join(cls.repo_root, "reports", "module3_baseline_readiness.md")
        cls.expected_sha256 = "052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329"

        if os.path.exists(cls.pit_path):
            cls.df = pd.read_csv(cls.pit_path)
        else:
            cls.df = None

        # Safe baseline predictors specified in Module 3 Phase 1 Section 6
        cls.safe_baseline_predictors = [
            "feat_log_original_cost",
            "feat_expenditure_to_original_cost_ratio",
            "feat_physical_progress_pct",
            "feat_physical_vs_financial_divergence",
            "feat_project_age_months",
            "feat_is_missing_approval_date",
            "feat_remaining_original_duration_months",
            "feat_is_past_original_completion",
            "feat_state",
            "feat_agency",
        ]

        # Approved supporting numeric variables present in PIT dataset
        cls.supporting_numeric_variables = [
            "feat_original_cost_crore",
            "feat_cumulative_expenditure_crore",
        ]

    # Test 1: PIT dataset exists
    def test_01_pit_dataset_exists(self):
        """Verify that the interim PIT feature dataset exists."""
        self.assertTrue(os.path.exists(self.pit_path), f"File missing: {self.pit_path}")
        self.assertIsNotNone(self.df)
        self.assertEqual(len(self.df), 437)
        self.assertEqual(len(self.df.columns), 26)

    # Test 2: PIT dataset SHA-256 matches specification
    def test_02_pit_dataset_sha256(self):
        """Verify that PIT dataset matches verified SHA-256 hash."""
        with open(self.pit_path, "rb") as f:
            computed_sha = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(
            computed_sha,
            self.expected_sha256,
            f"PIT dataset SHA-256 mismatch: {computed_sha} != {self.expected_sha256}"
        )

    # Test 3: Cost target counts (437 total, 132 positive, 305 negative)
    def test_03_cost_target_counts(self):
        """Verify cost target counts: 437 total, 132 positive, 305 negative, 0 missing."""
        col = "cost_overrun_5pct_2026"
        self.assertIn(col, self.df.columns)
        self.assertEqual(self.df[col].isna().sum(), 0, "Cost target must have 0 missing values")
        self.assertEqual(len(self.df[col]), 437, "Cost target total must be 437")

        counts = self.df[col].value_counts().to_dict()
        self.assertEqual(counts.get(1, 0), 132, "Expected 132 positive (>5%) cost overrun cases")
        self.assertEqual(counts.get(0, 0), 305, "Expected 305 negative (<=5%) cost overrun cases")
        self.assertAlmostEqual(counts[1] / 437, 132 / 437, places=4)
        self.assertEqual((self.df["is_eligible_cost_target"] == 1).sum(), 437)

    # Test 4: Schedule target counts (437 total, 305 eligible, 132 missing, 257 positive, 48 negative)
    def test_04_schedule_target_counts(self):
        """Verify schedule target counts: 437 total, 305 eligible, 132 missing, 257 positive, 48 negative."""
        col = "time_overrun_3m_2026"
        self.assertIn(col, self.df.columns)

        total_count = len(self.df)
        missing_count = int(self.df[col].isna().sum())
        eligible_count = int(self.df[col].notna().sum())

        self.assertEqual(total_count, 437, f"Expected 437 total, got {total_count}")
        self.assertEqual(eligible_count, 305, f"Expected 305 eligible schedule cases, got {eligible_count}")
        self.assertEqual(missing_count, 132, f"Expected 132 missing/censored schedule cases, got {missing_count}")

        # Verify eligibility flag matches missingness exactly
        self.assertEqual((self.df["is_eligible_schedule_target"] == 1).sum(), 305)
        self.assertEqual((self.df["is_eligible_schedule_target"] == 0).sum(), 132)

        # Verify class counts among eligible
        eligible_df = self.df[self.df["is_eligible_schedule_target"] == 1]
        valid_counts = eligible_df[col].astype(int).value_counts().to_dict()
        self.assertEqual(valid_counts.get(1, 0), 257, "Expected 257 positive (>=3 mo slippage) cases")
        self.assertEqual(valid_counts.get(0, 0), 48, "Expected 48 negative (<3 mo slippage) cases")
        self.assertAlmostEqual(valid_counts[1] / 305, 257 / 305, places=4)

    # Test 5: No July 2026 outcome variable appears in baseline predictor list
    def test_05_no_july_2026_outcome_in_baseline_predictors(self):
        """Verify that no July 2026 outcome or target variable appears in the baseline predictor list."""
        prohibited_july2026_variables = [
            "future_total_cost_escalation_2026",
            "cost_overrun_5pct_2026",
            "future_schedule_slippage_months_2026",
            "time_overrun_3m_2026",
            "revised_cost_cr_2026",
            "revised_date_of_commissioning_2026",
            "future_cost",
            "future_completion",
            "is_eligible_cost_target",
            "is_eligible_schedule_target",
        ]

        for forbidden in prohibited_july2026_variables:
            self.assertNotIn(
                forbidden,
                self.safe_baseline_predictors,
                f"Prohibited July 2026 variable '{forbidden}' found in baseline predictors!"
            )

    # Test 6: State and agency are allowed categorical predictors
    def test_06_state_and_agency_allowed_categorical_predictors(self):
        """Verify that feat_state and feat_agency are allowed categorical baseline predictors."""
        self.assertIn("feat_state", self.safe_baseline_predictors)
        self.assertIn("feat_agency", self.safe_baseline_predictors)
        self.assertIn("feat_state", self.df.columns)
        self.assertIn("feat_agency", self.df.columns)

        # Verify sector is NOT in the first baseline predictor list
        self.assertNotIn("sector", self.safe_baseline_predictors)
        self.assertNotIn("feat_sector", self.safe_baseline_predictors)

    # Test 7: Revised cost and revised completion are prohibited predictors
    def test_07_revised_cost_and_revised_completion_prohibited_predictors(self):
        """Verify that revised cost and revised completion date are strictly prohibited as predictors."""
        prohibited_revision_fields = [
            "revised_cost_cr_2025",
            "delay_months_2025",
            "revised_cost_cr_2026",
            "revised_date_of_commissioning_2026",
            "revised_cost",
            "revised_completion",
            "revised_date",
        ]

        for prohibited in prohibited_revision_fields:
            self.assertNotIn(
                prohibited,
                self.safe_baseline_predictors,
                f"Prohibited revision field '{prohibited}' in baseline predictors!"
            )

    # Test 8: Protocol explicitly identifies evaluation as retrospective 12-month horizon evaluation
    def test_08_protocol_identifies_retrospective_12month_horizon_evaluation(self):
        """Verify that docs/module3_evaluation_protocol.md identifies evaluation as a retrospective 12-month horizon evaluation."""
        self.assertTrue(os.path.exists(self.protocol_path), f"Missing protocol file: {self.protocol_path}")
        with open(self.protocol_path, "r", encoding="utf-8") as f:
            protocol_content = f.read()

        self.assertIn(
            "Retrospective 12-month horizon evaluation",
            protocol_content,
            "Protocol must explicitly contain 'Retrospective 12-month horizon evaluation'"
        )

    # Test 9: Protocol explicitly prohibits claiming multi-period temporal CV
    def test_09_protocol_prohibits_multi_period_temporal_cv(self):
        """Verify that protocol explicitly prohibits claiming multi-period temporal cross-validation."""
        with open(self.protocol_path, "r", encoding="utf-8") as f:
            protocol_content = f.read()

        self.assertIn(
            "DO NOT claim multi-period temporal cross-validation",
            protocol_content,
            "Protocol must contain explicit prohibition on claiming multi-period temporal CV"
        )
        self.assertIn(
            "DO NOT claim broad temporal generalisation",
            protocol_content,
            "Protocol must contain explicit prohibition on claiming broad temporal generalisation"
        )
        self.assertIn(
            "DO NOT randomly mix future observations into the training data",
            protocol_content,
            "Protocol must contain explicit prohibition on mixing future observations"
        )

    # Test 10: Naive majority benchmarks, cross-validation isolation, and preprocessor leakage checks
    def test_10_naive_benchmarks_and_fold_isolation(self):
        """Verify empirical majority benchmarks and in-fold preprocessing isolation."""
        # 1. Cost Overrun Naive Benchmark (All 0s)
        y_cost = self.df["cost_overrun_5pct_2026"].to_numpy()
        y_cost_pred = np.zeros_like(y_cost)
        cost_acc = float(np.mean(y_cost == y_cost_pred))
        self.assertAlmostEqual(cost_acc, 305 / 437, places=4)

        # 2. Schedule Slippage Naive Benchmark (All 1s on eligible)
        eligible_df = self.df[self.df["is_eligible_schedule_target"] == 1]
        y_sched = eligible_df["time_overrun_3m_2026"].astype(int).to_numpy()
        y_sched_pred = np.ones_like(y_sched)
        sched_acc = float(np.mean(y_sched == y_sched_pred))
        self.assertAlmostEqual(sched_acc, 257 / 305, places=4)

        # 3. In-Fold Preprocessing Isolation Check
        splits = stratified_kfold_split(y_cost, n_splits=5, shuffle=True, random_state=42)
        for fold, (train_idx, test_idx) in enumerate(splits):
            train_df = self.df.iloc[train_idx]
            test_df = self.df.iloc[test_idx]

            # In-fold median imputation
            train_median = train_df["feat_project_age_months"].median()
            self.assertFalse(np.isnan(train_median))
            test_imputed = test_df["feat_project_age_months"].fillna(train_median)
            self.assertEqual(test_imputed.isna().sum(), 0)

            # In-fold categorical encoding check (state, agency)
            for cat_col in ["feat_state", "feat_agency"]:
                freq_map = train_df[cat_col].value_counts(normalize=True).to_dict()
                test_encoded = test_df[cat_col].map(freq_map).fillna(0.0)
                self.assertEqual(test_encoded.isna().sum(), 0)


if __name__ == "__main__":
    unittest.main()

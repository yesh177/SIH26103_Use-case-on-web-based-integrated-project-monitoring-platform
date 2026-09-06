"""
test_pit_features.py
--------------------
Regression tests for Module 2C Phase 2 PIT Feature and Target Dataset.
Verifies:
- Expected 437 cohort rows
- Unique project keys
- Correct cutoff date (2025-07-31)
- Absence of July-2026 predictors in X_t
- Exclusion of revised cost and revised completion from X_t
- Mathematical correctness of cost and schedule targets
- Non-zero missingness semantics
- Physical progress and financial ratio bounds
- Missing approval handling
- Deterministic execution
- Source panel immutability
"""

import unittest
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

from src.features.build_pit_features import (
    build_pit_feature_dataset,
    parse_ym,
    EXPECTED_PANEL_SHA256,
    DEFAULT_INPUT_PANEL,
    DEFAULT_OUTPUT_CSV,
)


class TestPitFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel_path = DEFAULT_INPUT_PANEL
        cls.output_path = DEFAULT_OUTPUT_CSV
        if not cls.output_path.exists():
            build_pit_feature_dataset(cls.panel_path, cls.output_path)
        cls.df = pd.read_csv(cls.output_path)
        cls.panel = pd.read_csv(cls.panel_path, dtype=str)

    def test_frozen_source_hash(self):
        """Verifies that the frozen project snapshot panel remains unchanged."""
        data = self.panel_path.read_bytes()
        actual_hash = hashlib.sha256(data).hexdigest()
        self.assertEqual(
            actual_hash,
            EXPECTED_PANEL_SHA256,
            "Frozen source project_snapshot_panel.csv has been mutated!"
        )

    def test_expected_cohort_row_count(self):
        """Verifies that the primary longitudinal cohort contains exactly 437 projects."""
        self.assertEqual(len(self.df), 437)

    def test_unique_project_keys(self):
        """Verifies that canonical_project_key has 0 duplicates."""
        self.assertEqual(self.df["canonical_project_key"].nunique(), 437)

    def test_cutoff_and_snapshot_dates(self):
        """Verifies prediction cutoff date is 2025-07-31 and snapshot date is 2025-07."""
        self.assertTrue((self.df["snapshot_date"] == "2025-07").all())
        self.assertTrue((self.df["prediction_cutoff_date"] == "2025-07-31").all())

    def test_approved_feature_columns_only(self):
        """Verifies that X_t contains only the approved 12 baseline feature columns."""
        expected_feat_cols = {
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
            "feat_state",
            "feat_agency",
        }
        actual_feat_cols = {c for c in self.df.columns if c.startswith("feat_")}
        self.assertEqual(actual_feat_cols, expected_feat_cols)

    def test_revised_cost_excluded_from_x(self):
        """Verifies that revised cost is not included as a predictor in X_t."""
        self.assertNotIn("revised_cost_crore", self.df.columns)
        self.assertNotIn("feat_revised_cost_crore", self.df.columns)

    def test_revised_completion_excluded_from_x(self):
        """Verifies that revised completion date is not included as a predictor in X_t."""
        self.assertNotIn("revised_completion_date", self.df.columns)
        self.assertNotIn("feat_revised_completion_date", self.df.columns)

    def test_no_july_2026_predictors(self):
        """Verifies that no July-2026 columns appear in the feature columns."""
        for col in self.df.columns:
            if col.startswith("feat_"):
                self.assertNotIn("2026", col)
                self.assertNotIn("future", col)

    def test_correct_cost_target_calculation(self):
        """Independently recalculates future_total_cost_escalation_2026 against source panel."""
        df_25 = self.panel[self.panel["source_snapshot"] == "2025-07"].set_index("canonical_project_key")
        df_26 = self.panel[self.panel["source_snapshot"] == "2026-07"].set_index("canonical_project_key")

        for _, row in self.df.iterrows():
            k = row["canonical_project_key"]
            orig_cost = float(df_25.loc[k, "original_cost_crore"])
            rev_cost_26 = float(df_26.loc[k, "revised_cost_crore"])
            expected_esc = (rev_cost_26 - orig_cost) / orig_cost
            actual_esc = float(row["future_total_cost_escalation_2026"])
            self.assertAlmostEqual(actual_esc, expected_esc, places=5)

            expected_binary = 1 if expected_esc > 0.05 else 0
            self.assertEqual(row["cost_overrun_5pct_2026"], expected_binary)
            self.assertEqual(row["is_eligible_cost_target"], 1)

    def test_correct_schedule_target_calculation(self):
        """Independently recalculates future_schedule_slippage_months_2026 against source panel."""
        df_25 = self.panel[self.panel["source_snapshot"] == "2025-07"].set_index("canonical_project_key")
        df_26 = self.panel[self.panel["source_snapshot"] == "2026-07"].set_index("canonical_project_key")

        for _, row in self.df.iterrows():
            k = row["canonical_project_key"]
            orig_ym = parse_ym(df_25.loc[k, "original_completion_date"])
            rev_ym = parse_ym(df_26.loc[k, "revised_completion_date"])

            if orig_ym is not None and rev_ym is not None:
                expected_slip = (rev_ym[0] - orig_ym[0]) * 12 + (rev_ym[1] - orig_ym[1])
                actual_slip = float(row["future_schedule_slippage_months_2026"])
                self.assertAlmostEqual(actual_slip, expected_slip, places=5)

                expected_binary = 1 if expected_slip >= 3.0 else 0
                self.assertEqual(row["time_overrun_3m_2026"], expected_binary)
                self.assertEqual(row["is_eligible_schedule_target"], 1)
            else:
                self.assertTrue(np.isnan(row["future_schedule_slippage_months_2026"]))
                self.assertTrue(np.isnan(row["time_overrun_3m_2026"]))
                self.assertEqual(row["is_eligible_schedule_target"], 0)

    def test_missing_schedule_target_semantics(self):
        """Verifies that missing July-2026 revised completion dates are NOT converted to zero."""
        missing_sched_rows = self.df[self.df["is_eligible_schedule_target"] == 0]
        self.assertEqual(len(missing_sched_rows), 132)
        for _, row in missing_sched_rows.iterrows():
            self.assertTrue(np.isnan(row["future_schedule_slippage_months_2026"]))
            self.assertTrue(np.isnan(row["time_overrun_3m_2026"]))

    def test_physical_progress_bounds(self):
        """Verifies that physical_progress_pct is bounded in [0.0, 100.0]."""
        prog = self.df["feat_physical_progress_pct"]
        self.assertTrue((prog >= 0.0).all())
        self.assertTrue((prog <= 100.0).all())

    def test_expenditure_ratio_calculation(self):
        """Verifies that expenditure_to_original_cost_ratio matches expenditure / original_cost."""
        for _, row in self.df.iterrows():
            expected = row["feat_cumulative_expenditure_crore"] / row["feat_original_cost_crore"]
            self.assertAlmostEqual(row["feat_expenditure_to_original_cost_ratio"], expected, places=5)

    def test_divergence_calculation(self):
        """Verifies that physical_vs_financial_divergence matches (ratio * 100) - progress."""
        for _, row in self.df.iterrows():
            expected = (row["feat_expenditure_to_original_cost_ratio"] * 100.0) - row["feat_physical_progress_pct"]
            self.assertAlmostEqual(row["feat_physical_vs_financial_divergence"], expected, places=5)

    def test_missing_approval_handling(self):
        """Verifies that projects with missing approval dates have NaN age and is_missing_approval_date == 1."""
        missing_appr = self.df[self.df["feat_is_missing_approval_date"] == 1]
        self.assertEqual(len(missing_appr), 1)
        for _, row in missing_appr.iterrows():
            self.assertTrue(np.isnan(row["feat_project_age_months"]))

    def test_deterministic_output(self):
        """Verifies that running build_pit_feature_dataset produces identical output."""
        hash_before = hashlib.sha256(self.output_path.read_bytes()).hexdigest()
        build_pit_feature_dataset(self.panel_path, self.output_path)
        hash_after = hashlib.sha256(self.output_path.read_bytes()).hexdigest()
        self.assertEqual(hash_before, hash_after)


if __name__ == "__main__":
    unittest.main()

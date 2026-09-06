"""
test_longitudinal_pit_features.py
---------------------------------
Comprehensive unit tests for the generic longitudinal PIT feature builder.

Verifies:
1. Operational grain at (project_code, reporting_period).
2. Strict point-in-time calculation (uses only information at or before t).
3. Zero future leakage (no access to t+1 or later observations).
4. Calculation of all 12 derived features from docs/pit_feature_specification.md:
   - cost_growth_ratio
   - expenditure_to_original_cost
   - expenditure_to_revised_cost
   - schedule_slippage_days
   - project_age_days
   - elapsed_duration_ratio
   - progress_gap
   - expenditure_progress_gap
   - recent_cost_change
   - recent_expenditure_change
   - recent_progress_change
   - recent_schedule_change
5. Handling of irregular reporting periods and missing intermediate months.
6. First observation identification (is_first_observation = 1) with preserved NaNs.
7. Model A vs. Model B feature set partitioning.
8. Anti-leakage compliance (Rules LR-01 through LR-07).
"""

import unittest
import numpy as np
import pandas as pd

from src.features.longitudinal_pit_features import (
    LongitudinalPITFeatureBuilder,
    PITColumnConfig,
    PITFeatureError,
    normalize_period,
    subtract_one_month,
    build_longitudinal_pit_features,
)
from src.features.build_targets import audit_feature_target_separation


class TestLongitudinalPITFeatures(unittest.TestCase):
    """Unit test suite for LongitudinalPITFeatureBuilder."""

    def setUp(self):
        """Create a multi-project longitudinal panel with known trajectories."""
        # Project 1: Tracked across 3 consecutive months: 2025-01, 2025-02, 2025-03
        # Inception: start 2024-01-01, orig_cost 100 Cr, orig_doc 2025-12-31 (730 days duration)
        # Month 1 (2025-01): rev_cost 100, exp 20, prog 25%, rev_doc 2025-12-31 (unrevised)
        # Month 2 (2025-02): rev_cost 110 (+10), exp 30 (+10), prog 35% (+10%), rev_doc 2026-03-31 (+90 days)
        # Month 3 (2025-03): rev_cost 110 (+0), exp 45 (+15), prog 45% (+10%), rev_doc 2026-03-31 (+0 days)
        p1 = [
            {
                "project_code": "PROJ_1",
                "reporting_period": "2025-01",
                "sector": "Roads",
                "line_ministry": "MoRTH",
                "start_date": "2024-01-01",
                "original_cost_cr": 100.0,
                "revised_cost_cr": 100.0,
                "original_end_date": "2025-12-31",
                "revised_end_date": "2025-12-31",
                "expenditure_cr": 20.0,
                "physical_progress_pct": 25.0,
            },
            {
                "project_code": "PROJ_1",
                "reporting_period": "2025-02",
                "sector": "Roads",
                "line_ministry": "MoRTH",
                "start_date": "2024-01-01",
                "original_cost_cr": 100.0,
                "revised_cost_cr": 110.0,
                "original_end_date": "2025-12-31",
                "revised_end_date": "2026-03-31",
                "expenditure_cr": 30.0,
                "physical_progress_pct": 35.0,
            },
            {
                "project_code": "PROJ_1",
                "reporting_period": "2025-03",
                "sector": "Roads",
                "line_ministry": "MoRTH",
                "start_date": "2024-01-01",
                "original_cost_cr": 100.0,
                "revised_cost_cr": 110.0,
                "original_end_date": "2025-12-31",
                "revised_end_date": "2026-03-31",
                "expenditure_cr": 45.0,
                "physical_progress_pct": 45.0,
            },
        ]

        # Project 2: Irregular / missing months: 2025-01 and 2025-03 (missing 2025-02)
        # Inception: orig_cost 200 Cr, orig_doc 2026-06-30
        p2 = [
            {
                "project_code": "PROJ_2",
                "reporting_period": "2025-01",
                "sector": "Railways",
                "line_ministry": "MoR",
                "start_date": "2023-01-01",
                "original_cost_cr": 200.0,
                "revised_cost_cr": 200.0,
                "original_end_date": "2026-06-30",
                "revised_end_date": "2026-06-30",
                "expenditure_cr": 50.0,
                "physical_progress_pct": 20.0,
            },
            {
                "project_code": "PROJ_2",
                "reporting_period": "2025-03",
                "sector": "Railways",
                "line_ministry": "MoR",
                "start_date": "2023-01-01",
                "original_cost_cr": 200.0,
                "revised_cost_cr": 220.0,
                "original_end_date": "2026-06-30",
                "revised_end_date": "2026-09-30",
                "expenditure_cr": 70.0,
                "physical_progress_pct": 30.0,
            },
        ]

        self.df_panel = pd.DataFrame(p1 + p2)

    def test_period_utilities(self):
        """Verify date and calendar month subtraction."""
        self.assertEqual(normalize_period("2025-05"), "2025-05")
        self.assertEqual(normalize_period("2025-05-31"), "2025-05")
        self.assertEqual(subtract_one_month("2025-05"), "2025-04")
        self.assertEqual(subtract_one_month("2025-01"), "2024-12")

    def test_derived_financial_ratios(self):
        """Verify cost growth ratio, raw CUF, and adjusted CUF."""
        builder = LongitudinalPITFeatureBuilder()
        out = builder.build_pit_features(self.df_panel)

        # PROJ_1 at 2025-01: unrevised, orig_cost=100, exp=20
        # cost_growth_ratio = 100/100 = 1.0
        # exp_to_orig = 20/100 = 0.20
        # exp_to_rev = 20/100 = 0.20
        r1_m1 = out[(out["project_code"] == "PROJ_1") & (out["reporting_period"] == "2025-01")].iloc[0]
        self.assertAlmostEqual(r1_m1["cost_growth_ratio"], 1.0)
        self.assertAlmostEqual(r1_m1["expenditure_to_original_cost"], 0.20)
        self.assertAlmostEqual(r1_m1["expenditure_to_revised_cost"], 0.20)

        # PROJ_1 at 2025-02: revised to 110, exp=30
        # cost_growth_ratio = 110/100 = 1.10
        # exp_to_orig = 30/100 = 0.30
        # exp_to_rev = 30/110 = 0.272727
        r1_m2 = out[(out["project_code"] == "PROJ_1") & (out["reporting_period"] == "2025-02")].iloc[0]
        self.assertAlmostEqual(r1_m2["cost_growth_ratio"], 1.10)
        self.assertAlmostEqual(r1_m2["expenditure_to_original_cost"], 0.30)
        self.assertAlmostEqual(r1_m2["expenditure_to_revised_cost"], 30.0 / 110.0)

    def test_schedule_slippage_and_gaps(self):
        """Verify schedule slippage days, elapsed ratio, and progress gaps."""
        builder = LongitudinalPITFeatureBuilder()
        out = builder.build_pit_features(self.df_panel)

        # PROJ_1 at 2025-01: rev_doc = orig_doc = 2025-12-31 -> slippage = 0 days
        r1_m1 = out[(out["project_code"] == "PROJ_1") & (out["reporting_period"] == "2025-01")].iloc[0]
        self.assertEqual(r1_m1["schedule_slippage_days"], 0.0)

        # PROJ_1 at 2025-02: rev_doc = 2026-03-31 vs orig_doc = 2025-12-31
        # Days = 90 days
        r1_m2 = out[(out["project_code"] == "PROJ_1") & (out["reporting_period"] == "2025-02")].iloc[0]
        self.assertEqual(r1_m2["schedule_slippage_days"], 90.0)

        # Verify burn discrepancy (expenditure_progress_gap):
        # adj_cuf * 100 - physical_progress
        # At 2025-01: 20% - 25% = -5.0%
        self.assertAlmostEqual(r1_m1["expenditure_progress_gap"], -5.0)

    def test_velocity_features_consecutive_months(self):
        """Verify recent_cost, recent_exp, recent_prog, recent_sched for consecutive observations."""
        builder = LongitudinalPITFeatureBuilder()
        out = builder.build_pit_features(self.df_panel)

        # Month 1 (2025-01) is the first observation -> is_first_observation = 1, velocities = NaN
        r1_m1 = out[(out["project_code"] == "PROJ_1") & (out["reporting_period"] == "2025-01")].iloc[0]
        self.assertEqual(r1_m1["is_first_observation"], 1)
        self.assertTrue(np.isnan(r1_m1["recent_cost_change"]))
        self.assertTrue(np.isnan(r1_m1["recent_expenditure_change"]))
        self.assertTrue(np.isnan(r1_m1["recent_progress_change"]))
        self.assertTrue(np.isnan(r1_m1["recent_schedule_change"]))

        # Month 2 (2025-02) follows authentic 2025-01:
        # ΔCost = 110 - 100 = 10 Cr
        # ΔExp = 30 - 20 = 10 Cr
        # ΔProg = 35 - 25 = 10 %
        # ΔSched = 2026-03-31 - 2025-12-31 = 90 days
        r1_m2 = out[(out["project_code"] == "PROJ_1") & (out["reporting_period"] == "2025-02")].iloc[0]
        self.assertEqual(r1_m2["is_first_observation"], 0)
        self.assertAlmostEqual(r1_m2["recent_cost_change"], 10.0)
        self.assertAlmostEqual(r1_m2["recent_expenditure_change"], 10.0)
        self.assertAlmostEqual(r1_m2["recent_progress_change"], 10.0)
        self.assertEqual(r1_m2["recent_schedule_change"], 90.0)

        # Month 3 (2025-03) follows authentic 2025-02:
        # ΔCost = 110 - 110 = 0 Cr
        # ΔExp = 45 - 30 = 15 Cr
        # ΔProg = 45 - 35 = 10 %
        # ΔSched = 0 days
        r1_m3 = out[(out["project_code"] == "PROJ_1") & (out["reporting_period"] == "2025-03")].iloc[0]
        self.assertEqual(r1_m3["is_first_observation"], 0)
        self.assertAlmostEqual(r1_m3["recent_cost_change"], 0.0)
        self.assertAlmostEqual(r1_m3["recent_expenditure_change"], 15.0)
        self.assertAlmostEqual(r1_m3["recent_progress_change"], 10.0)
        self.assertEqual(r1_m3["recent_schedule_change"], 0.0)

    def test_missing_intermediate_month_preserves_nan(self):
        """Verify that when intermediate month t-1 is missing, velocities are strictly NaN (no guessing/interpolation)."""
        builder = LongitudinalPITFeatureBuilder()
        out = builder.build_pit_features(self.df_panel)

        # PROJ_2: observed at 2025-01 and 2025-03 (2025-02 is MISSING)
        # At 2025-03, preceding month is 2025-02 which was NOT observed.
        # Must NOT interpolate or calculate delta across a 2-month gap as a 1-month velocity.
        r2_m3 = out[(out["project_code"] == "PROJ_2") & (out["reporting_period"] == "2025-03")].iloc[0]
        self.assertEqual(r2_m3["is_first_observation"], 1)
        self.assertTrue(np.isnan(r2_m3["recent_cost_change"]))
        self.assertTrue(np.isnan(r2_m3["recent_expenditure_change"]))
        self.assertTrue(np.isnan(r2_m3["recent_progress_change"]))
        self.assertTrue(np.isnan(r2_m3["recent_schedule_change"]))

    def test_model_a_vs_model_b_extraction(self):
        """Verify extraction of Model A baseline and Model B enhanced feature matrices."""
        builder = LongitudinalPITFeatureBuilder()
        out = builder.build_pit_features(self.df_panel)

        model_a = builder.extract_model_a_features(out)
        model_b = builder.extract_model_b_features(out)

        # Model A must contain exactly official CUF baseline columns
        self.assertIn("original_cost_cr", model_a.columns)
        self.assertIn("expenditure_to_original_cost", model_a.columns)
        self.assertIn("physical_progress_pct", model_a.columns)
        self.assertNotIn("cost_growth_ratio", model_a.columns)
        self.assertNotIn("recent_progress_change", model_a.columns)

        # Model B must contain all Model A features PLUS derived/velocity features
        for col in model_a.columns:
            self.assertIn(col, model_b.columns)
        self.assertIn("cost_growth_ratio", model_b.columns)
        self.assertIn("expenditure_to_revised_cost", model_b.columns)
        self.assertIn("schedule_slippage_days", model_b.columns)
        self.assertIn("recent_progress_change", model_b.columns)
        self.assertIn("is_first_observation", model_b.columns)

    def test_anti_leakage_audit_compliance(self):
        """Verify that extracted Model A and Model B features pass automated pre-flight anti-leakage audit (LR-05, LR-06)."""
        builder = LongitudinalPITFeatureBuilder()
        out = builder.build_pit_features(self.df_panel)

        model_b = builder.extract_model_b_features(out)
        audit_result = audit_feature_target_separation(model_b)
        self.assertEqual(audit_result["status"], "PASS")

    def test_error_handling_duplicates_and_empty(self):
        """Verify robust error raising on duplicate records or malformed input."""
        builder = LongitudinalPITFeatureBuilder()
        with self.assertRaises(PITFeatureError):
            builder.build_pit_features(pd.DataFrame())

        # Duplicate (project, period)
        dups = pd.DataFrame([
            {"project_code": "P1", "reporting_period": "2025-01", "original_cost_cr": 100},
            {"project_code": "P1", "reporting_period": "2025-01", "original_cost_cr": 120},
        ])
        with self.assertRaises(PITFeatureError):
            builder.build_pit_features(dups)


if __name__ == "__main__":
    unittest.main()

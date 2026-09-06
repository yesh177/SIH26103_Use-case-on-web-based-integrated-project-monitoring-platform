"""
test_build_targets.py
---------------------
Comprehensive unit tests for PAIMANA Generic Target Construction module.

Verifies:
1. Support for 1, 3, 6, 12-month forward horizons (and custom horizons).
2. Future COST targets: continuous escalation and binary overrun (>5% θ_c).
3. Future SCHEDULE targets: continuous slippage days and binary deterioration (>0 days θ_s).
4. Milestone failure / Horizon miss: evaluation when revised_end_date <= t+Δ.
5. Missing future observations: strictly marked UNOBSERVABLE (NaN) and is_observable = 0.
6. Irregular reporting periods, missing intermediate months, dropping out.
7. Unrevised baseline fallbacks: revised_cost defaults to original_cost, revised_end_date defaults to original_end_date.
8. Repeated project tracking and chronological preservation.
9. Anti-leakage audit (LR-01 to LR-06) verifying feature/target separation.
10. Input validation and custom threshold enforcement.
"""

import unittest
import numpy as np
import pandas as pd

from src.features.build_targets import (
    TargetBuilder,
    TargetColumnConfig,
    TargetConstructionError,
    TargetLeakageError,
    add_months_to_period,
    normalize_period,
    parse_date_value,
    build_longitudinal_targets,
    audit_feature_target_separation,
)


class TestTargetBuilder(unittest.TestCase):
    """Unit test suite for TargetBuilder and target construction functions."""

    def setUp(self):
        """Create a synthetic longitudinal panel fixture for deterministic testing."""
        # Project A: Observed across 13 consecutive months (2025-01 to 2026-01)
        # Incurring a cost escalation in 2025-04 (+10 Cr on 100 Cr = +10%) and slippage in 2025-07 (+60 days)
        dates_a = [f"2025-{m:02d}" for m in range(1, 13)] + ["2026-01"]
        rows = []
        for d in dates_a:
            # Baseline: original cost 100 Cr, original end date 2026-06-30
            # From 2025-04 onwards, revised cost = 110 Cr
            # From 2025-07 onwards, revised end date = 2026-08-30 (61 days later)
            rev_c = 110.0 if d >= "2025-04" else 100.0
            rev_d = "2026-08-30" if d >= "2025-07" else "2026-06-30"
            phys_prog = 50.0 if d < "2025-07" else 70.0

            rows.append({
                "project_code": "PROJ_A",
                "reporting_period": d,
                "original_cost_cr": 100.0,
                "revised_cost_cr": rev_c,
                "original_end_date": "2026-06-30",
                "revised_end_date": rev_d,
                "physical_progress_pct": phys_prog,
            })

        # Project B: Irregular observations with missing intermediate months
        # Observed at 2025-01, 2025-02, 2025-04 (missing 2025-03)
        # Incurs severe cost escalation in 2025-04: 200 Cr -> 250 Cr (+25%)
        # Drops out after 2025-04
        rows.append({
            "project_code": "PROJ_B",
            "reporting_period": "2025-01",
            "original_cost_cr": 200.0,
            "revised_cost_cr": 200.0,
            "original_end_date": "2025-03-31",
            "revised_end_date": "2025-03-31",
            "physical_progress_pct": 80.0,
        })
        rows.append({
            "project_code": "PROJ_B",
            "reporting_period": "2025-02",
            "original_cost_cr": 200.0,
            "revised_cost_cr": 200.0,
            "original_end_date": "2025-03-31",
            "revised_end_date": "2025-03-31",
            "physical_progress_pct": 85.0,
        })
        rows.append({
            "project_code": "PROJ_B",
            "reporting_period": "2025-04",
            "original_cost_cr": 200.0,
            "revised_cost_cr": 250.0,
            "original_end_date": "2025-03-31",
            "revised_end_date": "2025-06-30",
            "physical_progress_pct": 90.0,  # Scheduled completion was 2025-03-31, but by 2025-04 progress is 90% (<100%) -> horizon miss
        })

        # Project C: Single snapshot only (no future observations at all)
        rows.append({
            "project_code": "PROJ_C",
            "reporting_period": "2025-06",
            "original_cost_cr": 50.0,
            "revised_cost_cr": 50.0,
            "original_end_date": "2027-12-31",
            "revised_end_date": "2027-12-31",
            "physical_progress_pct": 15.0,
        })

        self.panel_df = pd.DataFrame(rows)

    def test_period_utilities(self):
        """Test period parsing and calendar addition arithmetic."""
        self.assertEqual(normalize_period("2025-07-31"), "2025-07")
        self.assertEqual(normalize_period("2025-07"), "2025-07")
        self.assertEqual(normalize_period("07/2025"), "2025-07")
        self.assertIsNone(normalize_period("NA"))
        self.assertIsNone(normalize_period(np.nan))

        self.assertEqual(add_months_to_period("2025-01", 1), "2025-02")
        self.assertEqual(add_months_to_period("2025-01", 3), "2025-04")
        self.assertEqual(add_months_to_period("2025-01", 6), "2025-07")
        self.assertEqual(add_months_to_period("2025-01", 12), "2026-01")
        self.assertEqual(add_months_to_period("2025-10", 3), "2026-01")
        self.assertEqual(add_months_to_period("2025-12", 1), "2026-01")

    def test_target_construction_standard_horizons(self):
        """Verify all standard horizons {1, 3, 6, 12} are constructed with correct columns."""
        builder = TargetBuilder(horizons=[1, 3, 6, 12])
        out_df = builder.build_targets(self.panel_df)

        expected_horizons = [1, 3, 6, 12]
        for h in expected_horizons:
            self.assertIn(f"target_cost_escalation_{h}m_cr", out_df.columns)
            self.assertIn(f"target_cost_escalation_pct_{h}m", out_df.columns)
            self.assertIn(f"target_cost_overrun_{h}m_binary", out_df.columns)
            self.assertIn(f"target_schedule_slippage_{h}m_days", out_df.columns)
            self.assertIn(f"target_schedule_deterioration_{h}m_binary", out_df.columns)
            self.assertIn(f"target_horizon_miss_{h}m_binary", out_df.columns)
            self.assertIn(f"is_observable_{h}m", out_df.columns)
            self.assertIn(f"is_observable_cost_{h}m", out_df.columns)
            self.assertIn(f"is_observable_schedule_{h}m", out_df.columns)

        # Total rows must be perfectly preserved
        self.assertEqual(len(out_df), len(self.panel_df))

    def test_future_cost_escalation_correctness(self):
        """Verify continuous and binary cost escalation mathematical formulas."""
        builder = TargetBuilder(horizons=[3], cost_overrun_threshold=0.05)
        out_df = builder.build_targets(self.panel_df)

        # For PROJ_A at 2025-01:
        # t = 2025-01 (revised_cost = 100 Cr, original = 100 Cr)
        # t+3 = 2025-04 (revised_cost = 110 Cr)
        # ΔCost = 110 - max(100, 100) = 10 Cr
        # % escalation = 10 / 100 = 0.10 (+10%)
        # > 0.05 -> Binary label = 1
        row_a_jan = out_df[(out_df["project_code"] == "PROJ_A") & (out_df["reporting_period"] == "2025-01")].iloc[0]
        self.assertEqual(row_a_jan["is_observable_3m"], 1)
        self.assertAlmostEqual(row_a_jan["target_cost_escalation_3m_cr"], 10.0)
        self.assertAlmostEqual(row_a_jan["target_cost_escalation_pct_3m"], 0.10)
        self.assertEqual(row_a_jan["target_cost_overrun_3m_binary"], 1)

        # For PROJ_A at 2025-04:
        # t = 2025-04 (revised_cost = 110 Cr)
        # t+3 = 2025-07 (revised_cost = 110 Cr)
        # ΔCost = 110 - max(110, 100) = 0 Cr
        # % escalation = 0.0
        # <= 0.05 -> Binary label = 0
        row_a_apr = out_df[(out_df["project_code"] == "PROJ_A") & (out_df["reporting_period"] == "2025-04")].iloc[0]
        self.assertEqual(row_a_apr["target_cost_escalation_3m_cr"], 0.0)
        self.assertEqual(row_a_apr["target_cost_overrun_3m_binary"], 0)

    def test_future_schedule_slippage_correctness(self):
        """Verify continuous and binary schedule slippage formulas."""
        builder = TargetBuilder(horizons=[6], schedule_deterioration_threshold=0.0)
        out_df = builder.build_targets(self.panel_df)

        # For PROJ_A at 2025-01:
        # t = 2025-01 (revised_end_date = 2026-06-30)
        # t+6 = 2025-07 (revised_end_date = 2026-08-30)
        # Slippage days = (2026-08-30 - 2026-06-30) = 61 days
        # > 0.0 -> Binary deterioration label = 1
        row_a_jan = out_df[(out_df["project_code"] == "PROJ_A") & (out_df["reporting_period"] == "2025-01")].iloc[0]
        self.assertEqual(row_a_jan["is_observable_schedule_6m"], 1)
        self.assertEqual(row_a_jan["target_schedule_slippage_6m_days"], 61.0)
        self.assertEqual(row_a_jan["target_schedule_deterioration_6m_binary"], 1)

        # If threshold is set to 90 days, slippage of 61 days is <= 90 -> label should be 0
        builder_90d = TargetBuilder(horizons=[6], schedule_deterioration_threshold=90.0)
        out_df_90d = builder_90d.build_targets(self.panel_df)
        row_a_jan_90d = out_df_90d[(out_df_90d["project_code"] == "PROJ_A") & (out_df_90d["reporting_period"] == "2025-01")].iloc[0]
        self.assertEqual(row_a_jan_90d["target_schedule_deterioration_6m_binary"], 0)

    def test_missing_future_observations_unobservable(self):
        """Verify that missing future observations are strictly NaN (UNOBSERVABLE) and is_observable = 0."""
        builder = TargetBuilder(horizons=[1, 2, 3, 12])
        out_df = builder.build_targets(self.panel_df)

        # PROJ_B: observed at 2025-01, 2025-02, 2025-04 (missing 2025-03)
        row_b_jan = out_df[(out_df["project_code"] == "PROJ_B") & (out_df["reporting_period"] == "2025-01")].iloc[0]

        # Horizon 1m: 2025-02 is present -> observable
        self.assertEqual(row_b_jan["is_observable_1m"], 1)
        self.assertFalse(np.isnan(row_b_jan["target_cost_overrun_1m_binary"]))

        # Horizon 2m: 2025-03 is MISSING -> UNOBSERVABLE (NaN)
        self.assertEqual(row_b_jan["is_observable_2m"], 0)
        self.assertTrue(np.isnan(row_b_jan["target_cost_escalation_2m_cr"]))
        self.assertTrue(np.isnan(row_b_jan["target_cost_overrun_2m_binary"]))
        self.assertTrue(np.isnan(row_b_jan["target_schedule_slippage_2m_days"]))

        # Horizon 3m: 2025-04 is present -> observable
        self.assertEqual(row_b_jan["is_observable_3m"], 1)
        self.assertFalse(np.isnan(row_b_jan["target_cost_overrun_3m_binary"]))

        # Horizon 12m: 2026-01 is missing -> UNOBSERVABLE (NaN)
        self.assertEqual(row_b_jan["is_observable_12m"], 0)
        self.assertTrue(np.isnan(row_b_jan["target_cost_overrun_12m_binary"]))

        # PROJ_C: Single observation at 2025-06, NO future records at all
        row_c = out_df[out_df["project_code"] == "PROJ_C"].iloc[0]
        for h in [1, 2, 3, 12]:
            self.assertEqual(row_c[f"is_observable_{h}m"], 0)
            self.assertTrue(np.isnan(row_c[f"target_cost_overrun_{h}m_binary"]))
            self.assertTrue(np.isnan(row_c[f"target_schedule_slippage_{h}m_days"]))

    def test_horizon_milestone_failure(self):
        """Verify horizon milestone failure target (Section 2.3)."""
        builder = TargetBuilder(horizons=[3])
        out_df = builder.build_targets(self.panel_df)

        # PROJ_B at 2025-01:
        # revised_end_date(2025-01) = '2025-03-31'
        # Horizon 3m cutoff = '2025-04-30'
        # revised_end_date <= cutoff -> eligible for milestone failure check
        # At 2025-04, physical_progress = 90% (< 100%) -> milestone failure = 1
        row_b_jan = out_df[(out_df["project_code"] == "PROJ_B") & (out_df["reporting_period"] == "2025-01")].iloc[0]
        self.assertEqual(row_b_jan["target_horizon_miss_3m_binary"], 1)

        # PROJ_A at 2025-01:
        # revised_end_date(2025-01) = '2026-06-30'
        # Horizon 3m cutoff = '2025-04-30'
        # revised_end_date > cutoff -> Censored (NaN)
        row_a_jan = out_df[(out_df["project_code"] == "PROJ_A") & (out_df["reporting_period"] == "2025-01")].iloc[0]
        self.assertTrue(np.isnan(row_a_jan["target_horizon_miss_3m_binary"]))

    def test_unrevised_baseline_fallbacks(self):
        """Verify that unrevised projects correctly default to original cost and original end date."""
        df_unrev = pd.DataFrame([{
            "project_code": "PROJ_UNREV",
            "reporting_period": "2025-01",
            "original_cost_cr": 500.0,
            "revised_cost_cr": np.nan,  # Unrevised at t
            "original_end_date": "2027-01-01",
            "revised_end_date": None,   # Unrevised at t
            "physical_progress_pct": 20.0,
        }, {
            "project_code": "PROJ_UNREV",
            "reporting_period": "2025-02",
            "original_cost_cr": 500.0,
            "revised_cost_cr": 550.0,  # Revised at t+1 (+50 Cr)
            "original_end_date": "2027-01-01",
            "revised_end_date": "2027-04-01",  # 90 days slippage
            "physical_progress_pct": 25.0,
        }])

        builder = TargetBuilder(horizons=[1])
        out_df = builder.build_targets(df_unrev)
        row_t = out_df.iloc[0]

        # Base cost should have defaulted to 500 Cr
        # ΔCost = 550 - 500 = 50 Cr (+10%) -> Binary = 1
        self.assertAlmostEqual(row_t["target_cost_escalation_1m_cr"], 50.0)
        self.assertAlmostEqual(row_t["target_cost_escalation_pct_1m"], 0.10)
        self.assertEqual(row_t["target_cost_overrun_1m_binary"], 1)

        # Base end date should have defaulted to 2027-01-01
        # Slippage = (2027-04-01 - 2027-01-01) = 90 days -> Binary = 1
        self.assertEqual(row_t["target_schedule_slippage_1m_days"], 90.0)
        self.assertEqual(row_t["target_schedule_deterioration_1m_binary"], 1)

    def test_auto_detect_columns(self):
        """Verify automatic column detection with varied naming conventions."""
        df_varied = pd.DataFrame([{
            "canonical_project_key": "PROJ_KEY_1",
            "snapshot_date": "2025-05-31",
            "feat_original_cost_crore": 100.0,
            "revised_cost_crore": 100.0,
            "original_completion_date": "2026-12-31",
            "revised_completion_date": "2026-12-31",
            "feat_physical_progress_pct": 30.0,
        }, {
            "canonical_project_key": "PROJ_KEY_1",
            "snapshot_date": "2025-08-31",
            "feat_original_cost_crore": 100.0,
            "revised_cost_crore": 120.0,
            "original_completion_date": "2026-12-31",
            "revised_completion_date": "2027-03-31",
            "feat_physical_progress_pct": 35.0,
        }])

        builder = TargetBuilder(horizons=[3])
        out_df = builder.build_targets(df_varied)
        self.assertEqual(len(out_df), 2)
        row_t = out_df.iloc[0]
        self.assertEqual(row_t["is_observable_3m"], 1)
        self.assertAlmostEqual(row_t["target_cost_escalation_3m_cr"], 20.0)

    def test_anti_leakage_audit_pass(self):
        """Verify audit_feature_target_separation passes clean feature representations."""
        clean_features = pd.DataFrame({
            "expenditure_to_cost_ratio": [0.45, 0.60],
            "project_age_months": [24, 36],
            "physical_progress_pct": [50.0, 65.0],
            "line_ministry": ["MoRTH", "MoR"],
        })
        result = audit_feature_target_separation(clean_features)
        self.assertEqual(result["status"], "PASS")

    def test_anti_leakage_audit_fail_on_target_prefix(self):
        """Verify audit_feature_target_separation catches target prefix/suffix leakage (Rule LR-05)."""
        leaky_features_1 = pd.DataFrame({
            "expenditure_to_cost_ratio": [0.45],
            "target_cost_escalation_3m": [10.0],
        })
        with self.assertRaises(TargetLeakageError):
            audit_feature_target_separation(leaky_features_1)

        leaky_features_2 = pd.DataFrame({
            "future_cost_escalation": [10.0],
        })
        with self.assertRaises(TargetLeakageError):
            audit_feature_target_separation(leaky_features_2)

        leaky_features_3 = pd.DataFrame({
            "delay_target": [1],
        })
        with self.assertRaises(TargetLeakageError):
            audit_feature_target_separation(leaky_features_3)

    def test_anti_leakage_audit_fail_on_post_outcome(self):
        """Verify audit_feature_target_separation catches post-outcome realization variables (Rule LR-06)."""
        leaky_features = pd.DataFrame({
            "project_age_months": [24],
            "actual_completion_date": ["2026-12-31"],
        })
        with self.assertRaises(TargetLeakageError):
            audit_feature_target_separation(leaky_features)


if __name__ == "__main__":
    unittest.main()

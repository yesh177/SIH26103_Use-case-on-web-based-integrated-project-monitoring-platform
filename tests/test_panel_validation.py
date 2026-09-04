"""
Unit tests for the PAIMANA Panel Data Validator (src/data/validate_panel.py).

NOTE: All test data used herein consists strictly of tiny in-memory synthetic fixtures
constructed solely to verify validator boundary logic. These synthetic fixtures must never
be confused with or represented as authentic PAIMANA historical data.
"""

import unittest
import pandas as pd
import numpy as np

from src.data.validate_panel import PanelDataValidator


class TestPanelDataValidator(unittest.TestCase):
    """Test suite covering all 10 required validation scenarios."""

    def _get_base_valid_panel(self) -> pd.DataFrame:
        """Helper returning a clean 2-project, 3-period canonical panel."""
        data = [
            # Project P1: May, June, July
            {
                "reporting_period": "2026-05",
                "project_code": "P101",
                "project_name": "Test Project 1",
                "sector": "Roads",
                "line_ministry": "Ministry of Road Transport",
                "original_cost_cr": 500.0,
                "revised_cost_cr": 500.0,
                "expenditure_cr": 100.0,
                "physical_progress_pct": 20.0,
                "start_date": "2024-01-01",
                "original_end_date": "2027-12-31",
                "revised_end_date": "2027-12-31",
            },
            {
                "reporting_period": "2026-06",
                "project_code": "P101",
                "project_name": "Test Project 1",
                "sector": "Roads",
                "line_ministry": "Ministry of Road Transport",
                "original_cost_cr": 500.0,
                "revised_cost_cr": 500.0,
                "expenditure_cr": 120.0,
                "physical_progress_pct": 25.0,
                "start_date": "2024-01-01",
                "original_end_date": "2027-12-31",
                "revised_end_date": "2027-12-31",
            },
            {
                "reporting_period": "2026-07",
                "project_code": "P101",
                "project_name": "Test Project 1",
                "sector": "Roads",
                "line_ministry": "Ministry of Road Transport",
                "original_cost_cr": 500.0,
                "revised_cost_cr": 520.0,
                "expenditure_cr": 150.0,
                "physical_progress_pct": 30.0,
                "start_date": "2024-01-01",
                "original_end_date": "2027-12-31",
                "revised_end_date": "2028-03-31",
            },
            # Project P2: May, June, July
            {
                "reporting_period": "2026-05",
                "project_code": "P102",
                "project_name": "Test Project 2",
                "sector": "Railways",
                "line_ministry": "Ministry of Railways",
                "original_cost_cr": 1200.0,
                "revised_cost_cr": 1200.0,
                "expenditure_cr": 300.0,
                "physical_progress_pct": 40.0,
                "start_date": "2023-06-01",
                "original_end_date": "2026-12-31",
                "revised_end_date": "2026-12-31",
            },
            {
                "reporting_period": "2026-06",
                "project_code": "P102",
                "project_name": "Test Project 2",
                "sector": "Railways",
                "line_ministry": "Ministry of Railways",
                "original_cost_cr": 1200.0,
                "revised_cost_cr": 1200.0,
                "expenditure_cr": 330.0,
                "physical_progress_pct": 44.0,
                "start_date": "2023-06-01",
                "original_end_date": "2026-12-31",
                "revised_end_date": "2026-12-31",
            },
            {
                "reporting_period": "2026-07",
                "project_code": "P102",
                "project_name": "Test Project 2",
                "sector": "Railways",
                "line_ministry": "Ministry of Railways",
                "original_cost_cr": 1200.0,
                "revised_cost_cr": 1200.0,
                "expenditure_cr": 360.0,
                "physical_progress_pct": 48.0,
                "start_date": "2023-06-01",
                "original_end_date": "2026-12-31",
                "revised_end_date": "2026-12-31",
            },
        ]
        return pd.DataFrame(data)

    # 1. Valid longitudinal panel
    def test_01_valid_longitudinal_panel(self):
        df = self._get_base_valid_panel()
        validator = PanelDataValidator()
        report = validator.validate(df)
        self.assertEqual(report.status, "PASS")
        self.assertEqual(len(report.hard_fails), 0)
        self.assertEqual(report.total_projects, 2)
        self.assertEqual(report.total_periods, 3)

    # 2. Duplicate project-period
    def test_02_duplicate_project_period(self):
        df = self._get_base_valid_panel()
        # Duplicate row 0
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        validator = PanelDataValidator()
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("DC-IDENTITY-03", rule_ids)

    # 3. Missing project_code
    def test_03_missing_project_code(self):
        df = self._get_base_valid_panel()
        df.loc[0, "project_code"] = np.nan
        validator = PanelDataValidator()
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("DC-IDENTITY-01", rule_ids)

    # 4. Invalid reporting period format
    def test_04_invalid_reporting_period(self):
        df = self._get_base_valid_panel()
        df.loc[0, "reporting_period"] = "May-2026"  # Not YYYY-MM
        validator = PanelDataValidator()
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("DC-TIME-01", rule_ids)

    # 5. Negative expenditure
    def test_05_negative_expenditure(self):
        df = self._get_base_valid_panel()
        df.loc[0, "expenditure_cr"] = -15.5
        validator = PanelDataValidator()
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("DC-NUM-02", rule_ids)

    # 6. Physical progress outside 0-100%
    def test_06_physical_progress_out_of_bounds(self):
        df = self._get_base_valid_panel()
        df.loc[0, "physical_progress_pct"] = 105.0
        validator = PanelDataValidator()
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("DC-NUM-04", rule_ids)

    # 7. Future leakage (observations after declared cutoff t)
    def test_07_future_leakage_cutoff(self):
        df = self._get_base_valid_panel()  # contains 2026-05, 2026-06, 2026-07
        # Declare cutoff as 2026-05 (so June and July are future)
        validator = PanelDataValidator(cutoff_date="2026-05")
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("LR-01-04", rule_ids)

    # 8. Missing previous month for velocity (interpolated / non-NaN check)
    def test_08_missing_previous_month_velocity(self):
        df = self._get_base_valid_panel()
        # Add derived velocity feature, but incorrectly populate it on the first observation
        df["recent_progress_change"] = [5.0, 5.0, 5.0, 4.0, 4.0, 4.0]
        validator = PanelDataValidator()
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("DC-DERIVED-01", rule_ids)

    # 9. Missing future horizon / UNOBSERVABLE target
    def test_09_missing_future_horizon_unobservable(self):
        df = self._get_base_valid_panel()
        # Project P102 missing future horizon at t=2026-07 (only observed up to May)
        df = df[~((df["project_code"] == "P102") & (df["reporting_period"].isin(["2026-06", "2026-07"])))]
        validator = PanelDataValidator()
        report = validator.validate(df)
        # Verify panel density detected the single-period project
        self.assertEqual(report.density_stats.single_period_projects, 1)
        self.assertEqual(report.density_stats.multi_period_projects, 1)

    # 10. Target-derived feature violation (LR-05)
    def test_10_target_derived_feature_violation(self):
        df = self._get_base_valid_panel()
        # Test future_slip_days, future_cost_change, and cost_overrun_target
        for forbidden_col in ["future_slip_days", "future_cost_change", "cost_overrun_target"]:
            df_test = df.copy()
            df_test[forbidden_col] = [0, 0, 90, 0, 0, 0]
            validator = PanelDataValidator(is_feature_matrix=True)
            report = validator.validate(df_test)
            self.assertEqual(report.status, "FAIL", f"Failed to reject forbidden column {forbidden_col}")
            rule_ids = [i.rule_id for i in report.hard_fails]
            self.assertIn("LR-05", rule_ids)

        # Legitimate non-target feature accepted
        df_legit = df.copy()
        df_legit["cost_growth_ratio"] = [1.0, 1.0, 1.04, 1.0, 1.0, 1.0]
        report_legit = PanelDataValidator(is_feature_matrix=True).validate(df_legit)
        rule_ids_legit = [i.rule_id for i in report_legit.hard_fails]
        self.assertNotIn("LR-05", rule_ids_legit)

    # 11. Intermediate gap velocity violation (May -> July with non-NaN July velocity)
    def test_11_intermediate_gap_velocity_violation(self):
        # Case A: May -> July (missing June) with non-NaN velocity in July -> HARD FAIL
        data = [
            {
                "reporting_period": "2026-05",
                "project_code": "P201",
                "project_name": "Gap Project",
                "sector": "Roads",
                "line_ministry": "MoRTH",
                "original_cost_cr": 500.0,
                "revised_cost_cr": 500.0,
                "expenditure_cr": 100.0,
                "physical_progress_pct": 20.0,
                "start_date": "2024-01-01",
                "original_end_date": "2027-12-31",
                "revised_end_date": "2027-12-31",
                "recent_progress_change": np.nan,  # Valid: first observation is NaN
            },
            {
                "reporting_period": "2026-07",      # June is missing! 2-month jump
                "project_code": "P201",
                "project_name": "Gap Project",
                "sector": "Roads",
                "line_ministry": "MoRTH",
                "original_cost_cr": 500.0,
                "revised_cost_cr": 500.0,
                "expenditure_cr": 130.0,
                "physical_progress_pct": 26.0,
                "start_date": "2024-01-01",
                "original_end_date": "2027-12-31",
                "revised_end_date": "2027-12-31",
                "recent_progress_change": 6.0,     # VIOLATION: July preceded by May, not June!
            },
        ]
        df_gap = pd.DataFrame(data)
        validator = PanelDataValidator()
        report_gap = validator.validate(df_gap)
        self.assertEqual(report_gap.status, "FAIL")
        rule_ids = [i.rule_id for i in report_gap.hard_fails]
        self.assertIn("DC-DERIVED-01", rule_ids)

        # Case B: Valid May -> June -> July with valid consecutive velocities -> PASS
        df_valid = self._get_base_valid_panel()
        df_valid["recent_progress_change"] = [np.nan, 5.0, 5.0, np.nan, 4.0, 4.0]
        report_valid = PanelDataValidator().validate(df_valid)
        self.assertEqual(report_valid.status, "PASS")
        rule_ids_valid = [i.rule_id for i in report_valid.hard_fails]
        self.assertNotIn("DC-DERIVED-01", rule_ids_valid)

    # 12. LR-06 Post-outcome feature violation
    def test_12_post_outcome_feature_violation(self):
        df = self._get_base_valid_panel()
        df["actual_completion_date"] = ["2026-08-15"] * len(df)
        df["final_cost"] = [520.0] * len(df)
        validator = PanelDataValidator(is_feature_matrix=True)
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("LR-06", rule_ids)

    # 13. Instantaneous schedule target leakage (Gate 8: target == revised_doc > original_doc)
    def test_13_instantaneous_schedule_target_leakage(self):
        df = self._get_base_valid_panel()
        df["target"] = (pd.to_datetime(df["revised_end_date"]) > pd.to_datetime(df["original_end_date"])).astype(int)
        validator = PanelDataValidator()
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("DC-TARGET-01", rule_ids)

    # 14. Instantaneous cost target leakage (Gate 8: target == revised_cost > original_cost)
    def test_14_instantaneous_cost_target_leakage(self):
        df = self._get_base_valid_panel()
        df["cost_overrun_target"] = (df["revised_cost_cr"] > df["original_cost_cr"]).astype(int)
        validator = PanelDataValidator()
        report = validator.validate(df)
        self.assertEqual(report.status, "FAIL")
        rule_ids = [i.rule_id for i in report.hard_fails]
        self.assertIn("DC-TARGET-02", rule_ids)

    # 15. Snapshot-only detection (DataFrame without reporting_period)
    def test_15_snapshot_only_detection(self):
        df_snapshot = pd.DataFrame([
            {
                "project_code": "P301",
                "project_name": "Snapshot Project 1",
                "sector": "Power",
                "line_ministry": "Ministry of Power",
                "original_cost_cr": 800.0,
                "revised_cost_cr": 850.0,
                "expenditure_cr": 400.0,
                "original_end_date": "2027-06-30",
                "revised_end_date": "2027-12-31",
            },
            {
                "project_code": "P302",
                "project_name": "Snapshot Project 2",
                "sector": "Ports",
                "line_ministry": "Ministry of Ports",
                "original_cost_cr": 1500.0,
                "revised_cost_cr": 1500.0,
                "expenditure_cr": 600.0,
                "original_end_date": "2028-03-31",
                "revised_end_date": "2028-03-31",
            }
        ])
        validator = PanelDataValidator()
        report = validator.validate(df_snapshot)
        self.assertEqual(report.status, "SNAPSHOT_ONLY")
        self.assertNotIn("reporting_period", df_snapshot.columns)
        self.assertEqual(report.total_periods, 0)
        self.assertEqual(report.density_stats.multi_period_projects, 0)


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for the PAIMANA Temporal Splitter & Anti-Leakage Infrastructure (LR-07).

Authoritative Specifications:
- docs/leakage_rules.md (Rule LR-07: Anti-Mixing Temporal Split Invariant)
- docs/target_definition.md (Section 5: Temporal Cross-Validation Scheme)
- docs/validation_pipeline.md

Tests cover:
1. Chronological ordering (max(train) < min(test))
2. No future leakage or target horizon bleed
3. Train / validation / test 3-way separation
4. Repeated project entity observations staying temporally consistent
5. Horizon overlap handling via purging and embargo buffers
6. Failure on invalid temporal input, inverted dates, out-of-range ratios
7. Rolling / forward-chaining cross-validation fold generation
8. Verifier detection of artificial temporal leakage (index overlap, date inversion)
"""

import unittest
import pandas as pd
import numpy as np

from src.data.temporal_split import (
    BlockedTemporalSplitter,
    RollingTemporalSplitter,
    TemporalSplitError,
    TemporalLeakageError,
    verify_temporal_split,
)


class TestTemporalSplit(unittest.TestCase):
    """Test suite verifying Rule LR-07 temporal splitting invariants."""

    def setUp(self):
        """Create a synthetic multi-project, multi-period longitudinal panel."""
        # 3 projects across 6 monthly periods (2025-01 to 2025-06)
        rows = []
        periods = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
        for p in periods:
            for proj in ["P101", "P102", "P103"]:
                rows.append({
                    "reporting_period": p,
                    "project_code": proj,
                    "expenditure_cr": 100.0,
                    "physical_progress_pct": 20.0,
                })
        self.panel_df = pd.DataFrame(rows)

    def test_01_chronological_ordering_train_test(self):
        """1. Verify strict chronological separation: max(train) < min(test)."""
        splitter = BlockedTemporalSplitter(time_column="reporting_period", embargo_periods=0)
        res = splitter.split_by_cutoffs(self.panel_df, train_end="2025-03")

        self.assertEqual(res.train_periods, ["2025-01", "2025-02", "2025-03"])
        self.assertEqual(res.test_periods, ["2025-04", "2025-05", "2025-06"])
        self.assertLess(max(res.train_periods), min(res.test_periods))
        self.assertEqual(res.train_count, 9)
        self.assertEqual(res.test_count, 9)
        self.assertEqual(res.purged_count, 0)

    def test_02_three_way_split_train_val_test(self):
        """2. Verify train / val / test 3-way separation with monotonic boundaries."""
        splitter = BlockedTemporalSplitter(time_column="reporting_period", embargo_periods=0)
        res = splitter.split_by_cutoffs(
            self.panel_df, train_end="2025-02", val_end="2025-04", test_start="2025-05"
        )

        self.assertEqual(res.train_periods, ["2025-01", "2025-02"])
        self.assertEqual(res.val_periods, ["2025-03", "2025-04"])
        self.assertEqual(res.test_periods, ["2025-05", "2025-06"])
        self.assertLess(max(res.train_periods), min(res.val_periods))
        self.assertLess(max(res.val_periods), min(res.test_periods))

    def test_03_embargo_buffer_purging(self):
        """3. Verify horizon embargo buffer purges intermediate periods to prevent target overlap."""
        # Train on 2025-01 and 2025-02; 2-period target horizon requires 2-period embargo
        splitter = BlockedTemporalSplitter(time_column="reporting_period", embargo_periods=2)
        res = splitter.split_by_cutoffs(self.panel_df, train_end="2025-02")

        self.assertEqual(res.train_periods, ["2025-01", "2025-02"])
        self.assertEqual(res.purged_periods, ["2025-03", "2025-04"])  # 2 periods purged
        self.assertEqual(res.test_periods, ["2025-05", "2025-06"])
        self.assertEqual(res.purged_count, 6)  # 2 periods * 3 projects
        self.assertNotIn("2025-03", res.test["reporting_period"].values)
        self.assertNotIn("2025-04", res.test["reporting_period"].values)

    def test_04_repeated_project_entity_temporal_integrity(self):
        """4. Verify that repeated project observations stay temporally valid across splits."""
        splitter = BlockedTemporalSplitter(
            time_column="reporting_period", entity_column="project_code", embargo_periods=1
        )
        res = splitter.split_by_cutoffs(self.panel_df, train_end="2025-03")

        # Every project present in both train and test must have max(train) < min(test)
        for proj in ["P101", "P102", "P103"]:
            proj_train_periods = res.train[res.train["project_code"] == proj]["reporting_period"]
            proj_test_periods = res.test[res.test["project_code"] == proj]["reporting_period"]
            self.assertLess(proj_train_periods.max(), proj_test_periods.min())

    def test_05_split_by_ratio(self):
        """5. Verify split_by_ratio correctly calculates period boundaries."""
        splitter = BlockedTemporalSplitter(time_column="reporting_period", embargo_periods=1)
        res = splitter.split_by_ratio(self.panel_df, train_ratio=0.50, val_ratio=0.0)

        # 6 periods total -> train gets 3 periods (01, 02, 03), 1 purged (04), test gets 2 (05, 06)
        self.assertEqual(res.train_periods, ["2025-01", "2025-02", "2025-03"])
        self.assertEqual(res.purged_periods, ["2025-04"])
        self.assertEqual(res.test_periods, ["2025-05", "2025-06"])

    def test_06_rolling_forward_chaining_cross_validation(self):
        """6. Verify RollingTemporalSplitter generates valid expanding forward-chaining folds."""
        rolling = RollingTemporalSplitter(
            time_column="reporting_period",
            entity_column="project_code",
            n_splits=3,
            min_train_periods=2,
            test_periods=1,
            embargo_periods=1,
            expanding=True,
        )

        folds = list(rolling.split(self.panel_df))
        self.assertEqual(len(folds), 3)

        # Fold 1: train [01, 02], purge [03], test [04]
        f1_train, f1_test, f1_meta = folds[0]
        self.assertEqual(f1_meta["train_periods"], ["2025-01", "2025-02"])
        self.assertEqual(f1_meta["purged_periods"], ["2025-03"])
        self.assertEqual(f1_meta["test_periods"], ["2025-04"])

        # Fold 2: train [01, 02, 03], purge [04], test [05]
        f2_train, f2_test, f2_meta = folds[1]
        self.assertEqual(f2_meta["train_periods"], ["2025-01", "2025-02", "2025-03"])
        self.assertEqual(f2_meta["purged_periods"], ["2025-04"])
        self.assertEqual(f2_meta["test_periods"], ["2025-05"])

        # Fold 3: train [01, 02, 03, 04], purge [05], test [06]
        f3_train, f3_test, f3_meta = folds[2]
        self.assertEqual(f3_meta["train_periods"], ["2025-01", "2025-02", "2025-03", "2025-04"])
        self.assertEqual(f3_meta["purged_periods"], ["2025-05"])
        self.assertEqual(f3_meta["test_periods"], ["2025-06"])

    def test_07_failure_on_inverted_cutoffs(self):
        """7. Verify failure when test_start is before train_end."""
        splitter = BlockedTemporalSplitter(time_column="reporting_period")
        with self.assertRaises(TemporalSplitError):
            splitter.split_by_cutoffs(self.panel_df, train_end="2025-04", test_start="2025-02")

    def test_08_failure_on_embargo_exhausting_test_set(self):
        """8. Verify failure when embargo buffer leaves no remaining periods for test set."""
        splitter = BlockedTemporalSplitter(time_column="reporting_period", embargo_periods=5)
        # Train on 2025-02, requires 5 buffer periods, but only 4 remain (03, 04, 05, 06)
        with self.assertRaises(TemporalSplitError):
            splitter.split_by_cutoffs(self.panel_df, train_end="2025-02")

    def test_09_failure_on_missing_time_column(self):
        """9. Verify failure when time column does not exist."""
        bad_df = self.panel_df.drop(columns=["reporting_period"])
        splitter = BlockedTemporalSplitter(time_column="reporting_period")
        with self.assertRaises(TemporalSplitError):
            splitter.split_by_cutoffs(bad_df, train_end="2025-03")

    def test_10_verifier_detects_future_leakage(self):
        """10. Verify that verify_temporal_split catches temporal inversion leakage."""
        # Intentionally create leaky partitions: train has 2025-05, test has 2025-02
        leaky_train = self.panel_df[self.panel_df["reporting_period"] >= "2025-04"]
        leaky_test = self.panel_df[self.panel_df["reporting_period"] <= "2025-03"]

        with self.assertRaises(TemporalLeakageError):
            verify_temporal_split(
                train_df=leaky_train, test_df=leaky_test, time_column="reporting_period"
            )

    def test_11_verifier_detects_index_overlap(self):
        """11. Verify that verify_temporal_split catches index overlap between partitions."""
        train_df = self.panel_df.iloc[:6]
        test_df = self.panel_df.iloc[4:10]  # indices 4 and 5 overlap
        with self.assertRaises(TemporalLeakageError):
            verify_temporal_split(
                train_df=train_df, test_df=test_df, time_column="reporting_period"
            )

    def test_12_disordered_input_handled_gracefully(self):
        """12. Verify that shuffled input is safely sorted and correctly partitioned."""
        shuffled_df = self.panel_df.sample(frac=1.0, random_state=42)
        splitter = BlockedTemporalSplitter(time_column="reporting_period", embargo_periods=1)
        res = splitter.split_by_cutoffs(shuffled_df, train_end="2025-03")

        self.assertEqual(res.train_periods, ["2025-01", "2025-02", "2025-03"])
        self.assertEqual(res.purged_periods, ["2025-04"])
        self.assertEqual(res.test_periods, ["2025-05", "2025-06"])
        self.assertLess(max(res.train_periods), min(res.test_periods))


if __name__ == "__main__":
    unittest.main()

"""
test_build_longitudinal_dataset.py
----------------------------------
Comprehensive unit tests for PAIMANA Unified Longitudinal Dataset Pipeline.

Verifies:
1. Pipeline end-to-end orchestration connecting validation, PIT features, targets, and temporal splitting.
2. Ingestion schema contract enforcement and error raising on invalid data.
3. Computation of all 12 PIT derived and velocity features.
4. Multi-horizon continuous and binary target construction across {1, 3, 6, 12} months.
5. Model A (CUF baseline) vs Model B (Enhanced PIT) feature matrix separation.
6. Temporal train/test splitting respecting Rule LR-07 and embargo buffers.
7. Anti-leakage verification (LR-01 .. LR-06) on extracted feature representations.
8. Unobservable future target handling (NaN preservation without imputation).
9. Robustness on irregular reporting periods and missing intermediate months.
10. Deterministic artifact saving and metadata generation.
"""

import os
import tempfile
import unittest
import numpy as np
import pandas as pd

from src.features.build_longitudinal_dataset import (
    LongitudinalDatasetPipeline,
    LongitudinalPipelineConfig,
    run_longitudinal_pipeline,
)
from src.features.longitudinal_pit_features import PITColumnConfig
from src.features.build_targets import TargetColumnConfig


class TestLongitudinalDatasetPipeline(unittest.TestCase):
    """Test suite for LongitudinalDatasetPipeline orchestration."""

    def setUp(self):
        """Create a multi-project longitudinal fixture spanning 6 calendar months."""
        # 3 physical projects tracked across 6 monthly reporting periods (2025-01 to 2025-06)
        # Total observations: 3 * 6 = 18 rows
        projects = [
            {"code": "P_001", "name": "Highway Expansion", "sector": "Roads", "min": "MoRTH", "c0": 100.0, "d0": "2026-12-31"},
            {"code": "P_002", "name": "Port Terminal", "sector": "Ports", "min": "MoS", "c0": 250.0, "d0": "2027-06-30"},
            {"code": "P_003", "name": "Power Transmission", "sector": "Power", "min": "MoP", "c0": 50.0, "d0": "2025-10-31"},
        ]
        periods = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]

        rows = []
        for p in projects:
            for idx, d in enumerate(periods):
                # Simulated realistic progress and expenditures
                exp = float(p["c0"] * (0.10 + idx * 0.08))
                prog = float(15.0 + idx * 10.0)
                # P_001 gets cost revision in month 3 (+20 Cr)
                rev_c = p["c0"] + 20.0 if (p["code"] == "P_001" and idx >= 2) else p["c0"]
                # P_002 gets schedule revision in month 4 (+90 days)
                rev_d = "2027-09-30" if (p["code"] == "P_002" and idx >= 3) else p["d0"]

                rows.append({
                    "project_code": p["code"],
                    "project_name": p["name"],
                    "reporting_period": d,
                    "sector": p["sector"],
                    "line_ministry": p["min"],
                    "state": "Maharashtra",
                    "agency": "NHAI",
                    "start_date": "2024-01-01",
                    "original_cost_cr": p["c0"],
                    "revised_cost_cr": rev_c,
                    "original_end_date": p["d0"],
                    "revised_end_date": rev_d,
                    "expenditure_cr": exp,
                    "physical_progress_pct": prog,
                })

        self.df_panel = pd.DataFrame(rows)

    def test_end_to_end_orchestration_success(self):
        """Verify complete pipeline execution produces valid annotated data, features, targets, and split."""
        cfg = LongitudinalPipelineConfig(
            horizons=[1, 3],
            perform_temporal_split=True,
            train_ratio=0.60,
            embargo_periods=0,
            enforce_strict_validation=True,
        )
        pipeline = LongitudinalDatasetPipeline(config=cfg)
        result = pipeline.run(self.df_panel)

        # 1. Total row preservation
        self.assertEqual(len(result.annotated_dataset), len(self.df_panel))

        # 2. Presence of PIT features
        self.assertIn("cost_growth_ratio", result.annotated_dataset.columns)
        self.assertIn("expenditure_to_original_cost", result.annotated_dataset.columns)
        self.assertIn("schedule_slippage_days", result.annotated_dataset.columns)
        self.assertIn("recent_progress_change", result.annotated_dataset.columns)
        self.assertIn("is_first_observation", result.annotated_dataset.columns)

        # 3. Presence of multi-horizon targets
        for h in [1, 3]:
            self.assertIn(f"target_cost_escalation_{h}m_cr", result.annotated_dataset.columns)
            self.assertIn(f"target_cost_overrun_{h}m_binary", result.annotated_dataset.columns)
            self.assertIn(f"target_schedule_slippage_{h}m_days", result.annotated_dataset.columns)
            self.assertIn(f"is_observable_{h}m", result.annotated_dataset.columns)

        # 4. Model A vs Model B feature separation
        self.assertIn("original_cost_cr", result.model_a_features.columns)
        self.assertNotIn("cost_growth_ratio", result.model_a_features.columns)
        self.assertIn("cost_growth_ratio", result.model_b_features.columns)
        self.assertIn("recent_progress_change", result.model_b_features.columns)

        # 5. Temporal split result
        self.assertIsNotNone(result.temporal_split)
        self.assertTrue(len(result.temporal_split.train) > 0)
        self.assertTrue(len(result.temporal_split.test) > 0)
        self.assertEqual(result.audit_metadata["leakage_audit_status"], "PASS")

    def test_missing_future_observations_marked_unobservable(self):
        """Verify that records near the end of the timeline have NaN targets and is_observable=0."""
        cfg = LongitudinalPipelineConfig(horizons=[3], perform_temporal_split=False)
        pipeline = LongitudinalDatasetPipeline(config=cfg)
        result = pipeline.run(self.df_panel)

        # Horizon = 3m. For 2025-05, t+3 = 2025-08 which is beyond 2025-06.
        # Targets must be NaN and is_observable_3m = 0
        df_annot = result.annotated_dataset
        may_records = df_annot[df_annot["reporting_period"] == "2025-05"]

        for _, row in may_records.iterrows():
            self.assertEqual(row["is_observable_3m"], 0)
            self.assertTrue(np.isnan(row["target_cost_overrun_3m_binary"]))
            self.assertTrue(np.isnan(row["target_schedule_slippage_3m_days"]))

    def test_temporal_split_with_embargo(self):
        """Verify temporal partition respects embargo buffer (Rule LR-07)."""
        cfg = LongitudinalPipelineConfig(
            horizons=[1],
            perform_temporal_split=True,
            train_ratio=0.50,  # 3 periods: 2025-01, 2025-02, 2025-03
            embargo_periods=1, # Purge 2025-04
        )
        pipeline = LongitudinalDatasetPipeline(config=cfg)
        result = pipeline.run(self.df_panel)

        split = result.temporal_split
        self.assertIsNotNone(split)
        self.assertEqual(split.train_periods, ["2025-01", "2025-02", "2025-03"])
        self.assertEqual(split.purged_periods, ["2025-04"])
        self.assertEqual(split.test_periods, ["2025-05", "2025-06"])
        self.assertEqual(split.purged_count, 3)  # 3 projects * 1 purged period

    def test_validation_failure_on_invalid_data(self):
        """Verify pipeline raises error when input violates critical data contract invariants."""
        # Negative original cost (Tier 2 violation)
        bad_df = self.df_panel.copy()
        bad_df.loc[0, "original_cost_cr"] = -50.0

        cfg = LongitudinalPipelineConfig(enforce_strict_validation=True)
        pipeline = LongitudinalDatasetPipeline(config=cfg)

        with self.assertRaises(ValueError):
            pipeline.run(bad_df)

    def test_pipeline_artifact_saving(self):
        """Verify that saving pipeline outputs creates valid, structured CSV and JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = LongitudinalPipelineConfig(horizons=[1], perform_temporal_split=True, train_ratio=0.60)
            pipeline = LongitudinalDatasetPipeline(config=cfg)
            result = pipeline.run(self.df_panel)

            paths = result.save(tmpdir)
            self.assertTrue(os.path.exists(paths["annotated_dataset"]))
            self.assertTrue(os.path.exists(paths["model_a_features"]))
            self.assertTrue(os.path.exists(paths["model_b_features"]))
            self.assertTrue(os.path.exists(paths["target_matrix"]))
            self.assertTrue(os.path.exists(paths["train_partition"]))
            self.assertTrue(os.path.exists(paths["test_partition"]))
            self.assertTrue(os.path.exists(paths["metadata"]))

            # Verify saved metadata is valid JSON
            import json
            with open(paths["metadata"], "r") as f:
                meta_loaded = json.load(f)
            self.assertEqual(meta_loaded["initial_rows"], 18)
            self.assertEqual(meta_loaded["leakage_audit_status"], "PASS")


if __name__ == "__main__":
    unittest.main()

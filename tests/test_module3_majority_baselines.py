"""
Unit and integration tests for Module 3 — Phase 2: Empirical Majority-Class Baselines.

Verifies:
1. Input exists.
2. Input SHA-256 matches.
3. Cost N = 437.
4. Cost positives = 132.
5. Cost negatives = 305.
6. Cost confusion matrix = [[305,0],[132,0]].
7. Schedule eligible N = 305.
8. Schedule positives = 257.
9. Schedule negatives = 48.
10. Schedule confusion matrix = [[0,48],[0,257]].
11. Cost accuracy equals 305/437.
12. Schedule accuracy equals 257/305.
13. Schedule recall equals 1.0.
14. Schedule balanced accuracy equals 0.5.
15. No source data modification occurs.
"""

import hashlib
import os
import unittest
import numpy as np
import pandas as pd

from src.models.build_majority_baselines import (
    EXPECTED_PIT_SHA256,
    compute_binary_metrics,
    run_majority_baselines,
    verify_file_sha256,
)


class TestModule3MajorityBaselines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.report_path = os.path.join(cls.repo_root, "reports", "module3_majority_baseline_results.md")

        # Record hash before any operation
        with open(cls.pit_path, "rb") as f:
            cls.initial_sha256 = hashlib.sha256(f.read()).hexdigest()

        cls.results = run_majority_baselines(cls.pit_path)
        cls.cost_res = cls.results["cost"]
        cls.sched_res = cls.results["schedule"]

    # 1. Input exists
    def test_01_input_exists(self):
        """Verify that the interim PIT feature dataset exists."""
        self.assertTrue(os.path.exists(self.pit_path), f"File missing: {self.pit_path}")

    # 2. Input SHA-256 matches
    def test_02_input_sha256_matches(self):
        """Verify that PIT dataset SHA-256 matches expected hash."""
        self.assertEqual(self.initial_sha256, EXPECTED_PIT_SHA256)
        self.assertTrue(verify_file_sha256(self.pit_path, EXPECTED_PIT_SHA256))

    # 3. Cost N = 437
    def test_03_cost_n(self):
        """Verify Cost target total count N = 437."""
        self.assertEqual(self.cost_res["n_total"], 437)

    # 4. Cost positives = 132
    def test_04_cost_positives(self):
        """Verify Cost target positive count = 132."""
        self.assertEqual(self.cost_res["positives"], 132)

    # 5. Cost negatives = 305
    def test_05_cost_negatives(self):
        """Verify Cost target negative count = 305."""
        self.assertEqual(self.cost_res["negatives"], 305)

    # 6. Cost confusion matrix = [[305,0],[132,0]]
    def test_06_cost_confusion_matrix(self):
        """Verify Cost confusion matrix equals [[305, 0], [132, 0]]."""
        expected_cm = [[305, 0], [132, 0]]
        self.assertEqual(self.cost_res["metrics"]["confusion_matrix"], expected_cm)
        self.assertEqual(self.cost_res["metrics"]["tn"], 305)
        self.assertEqual(self.cost_res["metrics"]["fp"], 0)
        self.assertEqual(self.cost_res["metrics"]["fn"], 132)
        self.assertEqual(self.cost_res["metrics"]["tp"], 0)

    # 7. Schedule eligible N = 305
    def test_07_schedule_eligible_n(self):
        """Verify Schedule target eligible count N = 305."""
        self.assertEqual(self.sched_res["n_eligible"], 305)
        self.assertEqual(self.sched_res["n_censored"], 132)

    # 8. Schedule positives = 257
    def test_08_schedule_positives(self):
        """Verify Schedule target positive count = 257."""
        self.assertEqual(self.sched_res["positives"], 257)

    # 9. Schedule negatives = 48
    def test_09_schedule_negatives(self):
        """Verify Schedule target negative count = 48."""
        self.assertEqual(self.sched_res["negatives"], 48)

    # 10. Schedule confusion matrix = [[0,48],[0,257]]
    def test_10_schedule_confusion_matrix(self):
        """Verify Schedule confusion matrix equals [[0, 48], [0, 257]]."""
        expected_cm = [[0, 48], [0, 257]]
        self.assertEqual(self.sched_res["metrics"]["confusion_matrix"], expected_cm)
        self.assertEqual(self.sched_res["metrics"]["tn"], 0)
        self.assertEqual(self.sched_res["metrics"]["fp"], 48)
        self.assertEqual(self.sched_res["metrics"]["fn"], 0)
        self.assertEqual(self.sched_res["metrics"]["tp"], 257)

    # 11. Cost accuracy equals 305/437
    def test_11_cost_accuracy(self):
        """Verify Cost accuracy equals 305 / 437."""
        expected_acc = 305.0 / 437.0
        self.assertAlmostEqual(self.cost_res["metrics"]["accuracy"], expected_acc, places=6)
        self.assertEqual(self.cost_res["metrics"]["recall"], 0.0)
        self.assertEqual(self.cost_res["metrics"]["f1"], 0.0)
        self.assertEqual(self.cost_res["metrics"]["balanced_accuracy"], 0.5)

    # 12. Schedule accuracy equals 257/305
    def test_12_schedule_accuracy(self):
        """Verify Schedule accuracy equals 257 / 305."""
        expected_acc = 257.0 / 305.0
        self.assertAlmostEqual(self.sched_res["metrics"]["accuracy"], expected_acc, places=6)
        self.assertAlmostEqual(self.sched_res["metrics"]["precision"], expected_acc, places=6)

    # 13. Schedule recall equals 1.0
    def test_13_schedule_recall(self):
        """Verify Schedule recall equals 1.0."""
        self.assertEqual(self.sched_res["metrics"]["recall"], 1.0)
        expected_f1 = 2 * (257.0 / 305.0 * 1.0) / (257.0 / 305.0 + 1.0)
        self.assertAlmostEqual(self.sched_res["metrics"]["f1"], expected_f1, places=6)
        self.assertAlmostEqual(self.sched_res["metrics"]["f1"], 0.914591, places=4)

    # 14. Schedule balanced accuracy equals 0.5
    def test_14_schedule_balanced_accuracy(self):
        """Verify Schedule balanced accuracy equals 0.5."""
        self.assertEqual(self.sched_res["metrics"]["balanced_accuracy"], 0.5)

    # 15. No source data modification occurs
    def test_15_no_source_data_modification(self):
        """Verify that PIT dataset SHA-256 remains byte-for-byte identical after all operations."""
        with open(self.pit_path, "rb") as f:
            current_sha256 = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(
            current_sha256,
            self.initial_sha256,
            "Source dataset has been modified during baseline computation!"
        )
        self.assertEqual(current_sha256, EXPECTED_PIT_SHA256)


if __name__ == "__main__":
    unittest.main()

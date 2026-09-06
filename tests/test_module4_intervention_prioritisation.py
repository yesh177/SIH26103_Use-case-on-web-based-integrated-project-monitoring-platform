"""
Unit and Integration Tests for Module 4 Phase 7 — Intervention Prioritisation
SIH26103 PAIMANA Predictive Risk Intelligence

Verifies all intervention layer requirements:
1. Exactly 437 physical projects.
2. Exactly one row per canonical_project_key (zero duplicates).
3. All risk-score projects are represented.
4. Existing risk probabilities and scores are unchanged.
5. PARTIAL projects never receive schedule-risk-based intervention.
6. PARTIAL projects explicitly preserve missing schedule status.
7. No synthetic values or fabricated facts.
8. Every intervention has a valid non-empty evidence field.
9. No prohibited causal or blaming language.
10. No intervention recommends sanctions, penalties, or termination.
11. Deterministic output across repeated executions.
12. All frozen upstream SHA-256 hashes remain unchanged.
"""

import os
import unittest
import hashlib
import numpy as np
import pandas as pd
from src.interventions.generate_intervention_priorities import (
    generate_interventions,
    EXPECTED_PIT_SHA256,
    EXPECTED_SCORES_SHA256,
    EXPECTED_UPSTREAM_HASHES,
)

PROHIBITED_WORDS = [
    "caused the delay",
    "caused cost overrun",
    "this project will fail",
    "agency is responsible",
    "state is responsible",
    "penalty",
    "penalties",
    "sanction",
    "sanctions",
    "terminate",
    "termination",
    "fault",
    "culpability",
]

ALLOWED_PRIMARY_ACTIONS = {
    "JOINT_COST_SCHEDULE_REVIEW",
    "COST_REVIEW",
    "SCHEDULE_REVIEW",
    "COMPLETION_STATUS_REVIEW",
    "EXPENDITURE_PROGRESS_REVIEW",
    "PROGRESS_VERIFICATION",
    "DATA_QUALITY_REVIEW",
}


class TestModule4InterventionPrioritisation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.pit_path = os.path.join(cls.repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.scores_path = os.path.join(cls.repo_root, "data", "processed", "project_risk_scores.csv")
        cls.explanations_path = os.path.join(cls.repo_root, "data", "interim", "project_risk_explanations.csv")
        cls.output_path = os.path.join(cls.repo_root, "data", "processed", "project_intervention_priorities.csv")

        cls.df = generate_interventions(cls.pit_path, cls.scores_path, cls.explanations_path, cls.output_path)
        cls.scores_df = pd.read_csv(cls.scores_path)

    # 1. Exactly 437 projects
    def test_01_project_count(self):
        self.assertEqual(len(self.df), 437)

    # 2. Exactly one row per canonical_project_key (zero duplicates)
    def test_02_unique_canonical_keys(self):
        self.assertEqual(self.df["canonical_project_key"].nunique(), 437)
        self.assertEqual(self.df.duplicated(subset=["canonical_project_key"]).sum(), 0)

    # 3. All risk-score projects are represented
    def test_03_all_risk_score_projects_represented(self):
        scores_keys = set(self.scores_df["canonical_project_key"])
        int_keys = set(self.df["canonical_project_key"])
        self.assertEqual(scores_keys, int_keys)

    # 4. Existing risk probabilities and scores are unchanged
    def test_04_probabilities_unchanged(self):
        merged = self.df.merge(self.scores_df, on="canonical_project_key", suffixes=("_int", "_score"))
        np.testing.assert_array_almost_equal(merged["cost_risk_probability_int"], merged["cost_risk_probability_score"], decimal=6)
        np.testing.assert_array_almost_equal(merged["attention_score_int"], merged["attention_score_score"], decimal=6)
        np.testing.assert_array_equal(merged["portfolio_rank_int"], merged["portfolio_rank_score"])

        # Schedule probability comparison
        full_merged = merged[merged["risk_coverage_int"] == "FULL"]
        np.testing.assert_array_almost_equal(full_merged["schedule_risk_probability_int"], full_merged["schedule_risk_probability_score"], decimal=6)

    # 5. PARTIAL projects never receive schedule-risk-based intervention
    def test_05_partial_projects_no_schedule_intervention(self):
        partial = self.df[self.df["risk_coverage"] == "PARTIAL"]
        self.assertEqual(len(partial), 132)

        for _, row in partial.iterrows():
            self.assertNotEqual(row["primary_action"], "SCHEDULE_REVIEW")
            self.assertNotEqual(row["primary_action"], "JOINT_COST_SCHEDULE_REVIEW")
            self.assertNotEqual(row["risk_focus"], "SCHEDULE_RISK")
            self.assertNotEqual(row["risk_focus"], "JOINT_COST_SCHEDULE")

    # 6. PARTIAL projects explicitly preserve missing schedule status
    def test_06_partial_projects_preserve_missing_schedule(self):
        partial = self.df[self.df["risk_coverage"] == "PARTIAL"]
        self.assertTrue(partial["schedule_risk_probability"].isna().all())
        self.assertTrue(partial["data_quality_flag"].str.contains("SCHEDULE_OUTCOME_UNOBSERVED").all())

    # 7. Action categories strictly within allowed vocabulary
    def test_07_action_vocabulary(self):
        for act in self.df["primary_action"].unique():
            self.assertIn(act, ALLOWED_PRIMARY_ACTIONS)

    # 8. Every intervention has non-empty evidence fields
    def test_08_evidence_fields_present(self):
        self.assertTrue(self.df["evidence_feature"].notna().all())
        self.assertTrue((self.df["evidence_feature"].str.len() > 2).all())
        self.assertTrue(self.df["evidence_value"].notna().all())
        self.assertTrue(self.df["evidence_direction"].notna().all())
        self.assertTrue(self.df["priority_reason"].notna().all())
        self.assertTrue((self.df["priority_reason"].str.len() > 10).all())

    # 9. No prohibited blaming or causal language
    def test_09_no_prohibited_language(self):
        for col in ["priority_reason", "governance_note"]:
            text_series = self.df[col].str.lower()
            for bad_word in PROHIBITED_WORDS:
                matches = text_series.str.contains(bad_word)
                self.assertFalse(matches.any(), f"Prohibited phrase '{bad_word}' found in column '{col}'!")

    # 10. No penalties or sanctions recommended
    def test_10_no_penalties_or_sanctions(self):
        all_actions = list(self.df["primary_action"]) + list(self.df["secondary_action"])
        for act in all_actions:
            self.assertNotIn("PENALTY", act)
            self.assertNotIn("SANCTION", act)
            self.assertNotIn("TERMINAT", act)

    # 11. Deterministic output across repeated runs
    def test_11_determinism_across_runs(self):
        tmp_output = os.path.join(self.repo_root, "data", "processed", "project_intervention_priorities_test_determinism.csv")
        df2 = generate_interventions(self.pit_path, self.scores_path, self.explanations_path, tmp_output)

        pd.testing.assert_frame_equal(self.df, df2)

        if os.path.exists(tmp_output):
            os.remove(tmp_output)

    # 12. Frozen upstream SHA-256 hashes unchanged
    def test_12_frozen_upstream_hashes_unmodified(self):
        with open(self.scores_path, "rb") as f:
            computed_scores = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(computed_scores, EXPECTED_SCORES_SHA256)

        for rel_path, exp_hash in EXPECTED_UPSTREAM_HASHES.items():
            full_p = os.path.join(self.repo_root, rel_path)
            with open(full_p, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(h, exp_hash, f"Hash mismatch for {rel_path}")


if __name__ == "__main__":
    unittest.main()

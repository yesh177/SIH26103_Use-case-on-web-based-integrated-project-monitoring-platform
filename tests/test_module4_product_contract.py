import os
import unittest
import hashlib
import pandas as pd

class TestModule4ProductContract(unittest.TestCase):
    """
    Unit test suite verifying Phase 8 Product Contract and Team Handoff Specification.
    Validates schemas, null semantics, compound exposure, tier distributions,
    absence of prohibited terms, key alignment, and frozen hashes.
    """

    @classmethod
    def setUpClass(cls):
        # Resolve repository root
        cls.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # Frozen CSV paths
        cls.pit_path = os.path.join(cls.root_dir, "data", "interim", "pit_features_july2025_to_july2026.csv")
        cls.risk_scores_path = os.path.join(cls.root_dir, "data", "processed", "project_risk_scores.csv")
        cls.explanations_path = os.path.join(cls.root_dir, "data", "interim", "project_risk_explanations.csv")
        cls.interventions_path = os.path.join(cls.root_dir, "data", "processed", "project_intervention_priorities.csv")

        # Documentation paths
        cls.product_contract_path = os.path.join(cls.root_dir, "reports", "module4_product_contract.md")
        cls.handoff_path = os.path.join(cls.root_dir, "reports", "module4_frontend_backend_handoff.md")

        # Load datasets
        cls.df_pit = pd.read_csv(cls.pit_path)
        cls.df_scores = pd.read_csv(cls.risk_scores_path)
        cls.df_explanations = pd.read_csv(cls.explanations_path)
        cls.df_interventions = pd.read_csv(cls.interventions_path)

    def test_frozen_artifacts_exist_and_hashes_intact(self):
        """1. Verify all frozen artifacts exist and match their authoritative SHA-256 hashes."""
        expected_hashes = {
            self.pit_path: "052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329",
            self.risk_scores_path: "6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d",
            self.explanations_path: "5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2",
            self.interventions_path: "3dfacd2805610e0a1a9ff3f10461c97322a3bf62ca1dc348fc6baca13e012ec5"
        }
        for file_path, expected_hash in expected_hashes.items():
            self.assertTrue(os.path.exists(file_path), f"Missing artifact: {file_path}")
            with open(file_path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {file_path}")

    def test_risk_scores_contract_schema_and_types(self):
        """2. Verify project_risk_scores schema has exactly 21 columns, 437 rows, and valid types."""
        self.assertEqual(len(self.df_scores), 437)
        self.assertEqual(len(self.df_scores.columns), 21)
        expected_columns = [
            "canonical_project_key", "source_project_id", "project_name", "state", "agency",
            "snapshot_date", "prediction_cutoff_date", "is_eligible_cost_target", "is_eligible_schedule_target",
            "cost_risk_probability", "schedule_risk_probability", "risk_coverage", "attention_score",
            "compound_exposure", "attention_tier", "portfolio_rank", "cost_model_name", "schedule_model_name",
            "cost_probability_variant", "schedule_probability_variant", "scoring_method_version"
        ]
        self.assertListEqual(list(self.df_scores.columns), expected_columns)
        self.assertTrue(self.df_scores["canonical_project_key"].is_unique)
        self.assertTrue((self.df_scores["cost_risk_probability"] >= 0.0).all())
        self.assertTrue((self.df_scores["cost_risk_probability"] <= 1.0).all())
        self.assertTrue((self.df_scores["attention_score"] >= 0.0).all())
        self.assertTrue((self.df_scores["attention_score"] <= 1.0).all())
        self.assertEqual(self.df_scores["portfolio_rank"].min(), 1)
        self.assertEqual(self.df_scores["portfolio_rank"].max(), 419)
        self.assertEqual(self.df_scores["portfolio_rank"].nunique(), 136)

    def test_risk_explanations_contract_schema_and_types(self):
        """3. Verify project_risk_explanations has exactly 29 columns and 874 rows (2 tasks x 437)."""
        self.assertEqual(len(self.df_explanations), 874)
        self.assertEqual(len(self.df_explanations.columns), 29)
        expected_columns = [
            "canonical_project_key", "source_project_id", "project_name", "state", "agency",
            "task", "is_eligible_task_target", "predicted_risk_probability", "attention_score",
            "attention_tier", "portfolio_rank", "risk_coverage",
            "top_1_feature", "top_1_feature_value", "top_1_impact", "top_1_direction", "top_1_source_fact",
            "top_2_feature", "top_2_feature_value", "top_2_impact", "top_2_direction", "top_2_source_fact",
            "top_3_feature", "top_3_feature_value", "top_3_impact", "top_3_direction", "top_3_source_fact",
            "explanation_method", "explanation_disclaimer"
        ]
        self.assertListEqual(list(self.df_explanations.columns), expected_columns)
        task_counts = self.df_explanations["task"].value_counts().to_dict()
        self.assertEqual(task_counts.get("cost_overrun"), 437)
        self.assertEqual(task_counts.get("schedule_slippage"), 437)

    def test_intervention_priorities_contract_schema_and_types(self):
        """4. Verify project_intervention_priorities has exactly 16 columns and 437 rows."""
        self.assertEqual(len(self.df_interventions), 437)
        self.assertEqual(len(self.df_interventions.columns), 16)
        expected_columns = [
            "canonical_project_key", "cost_risk_probability", "schedule_risk_probability",
            "attention_score", "risk_coverage", "portfolio_rank", "intervention_priority",
            "primary_action", "secondary_action", "risk_focus", "priority_reason",
            "evidence_feature", "evidence_value", "evidence_direction", "data_quality_flag", "governance_note"
        ]
        self.assertListEqual(list(self.df_interventions.columns), expected_columns)
        self.assertTrue(self.df_interventions["canonical_project_key"].is_unique)

        # Verify priority taxonomy counts: PRIORITY_1: 44, PRIORITY_2: 73, PRIORITY_3: 102, PRIORITY_4: 218
        priority_counts = self.df_interventions["intervention_priority"].value_counts().to_dict()
        self.assertEqual(priority_counts.get("PRIORITY_1"), 44)
        self.assertEqual(priority_counts.get("PRIORITY_2"), 73)
        self.assertEqual(priority_counts.get("PRIORITY_3"), 102)
        self.assertEqual(priority_counts.get("PRIORITY_4"), 218)

    def test_partial_coverage_null_semantics(self):
        """5. Verify PARTIAL coverage projects strictly have null schedule probability and compound exposure."""
        partial_scores = self.df_scores[self.df_scores["risk_coverage"] == "PARTIAL"]
        full_scores = self.df_scores[self.df_scores["risk_coverage"] == "FULL"]
        self.assertEqual(len(partial_scores), 132)
        self.assertEqual(len(full_scores), 305)

        # In scores:
        self.assertTrue(partial_scores["schedule_risk_probability"].isna().all())
        self.assertTrue(partial_scores["compound_exposure"].isna().all())
        self.assertTrue(full_scores["schedule_risk_probability"].notna().all())
        self.assertTrue(full_scores["compound_exposure"].notna().all())

        # In interventions:
        partial_interv = self.df_interventions[self.df_interventions["risk_coverage"] == "PARTIAL"]
        full_interv = self.df_interventions[self.df_interventions["risk_coverage"] == "FULL"]
        self.assertTrue(partial_interv["schedule_risk_probability"].isna().all())
        self.assertTrue(full_interv["schedule_risk_probability"].notna().all())
        self.assertTrue((partial_interv["data_quality_flag"] == "SCHEDULE_OUTCOME_UNOBSERVED").all())
        self.assertEqual(len(full_interv[full_interv["data_quality_flag"] == "COMPLETE_BASELINE_DATA"]), 304)
        self.assertEqual(len(full_interv[full_interv["data_quality_flag"] == "MISSING_APPROVAL_DATE"]), 1)

    def test_compound_exposure_semantics(self):
        """6. Verify compound_exposure equals min(Pc, Ps) for all FULL coverage projects and is bounded [0, 1]."""
        full_scores = self.df_scores[self.df_scores["risk_coverage"] == "FULL"]
        expected_compound = full_scores[["cost_risk_probability", "schedule_risk_probability"]].min(axis=1)
        self.assertTrue((full_scores["compound_exposure"] == expected_compound).all())
        self.assertTrue((full_scores["compound_exposure"] >= 0.0).all())
        self.assertTrue((full_scores["compound_exposure"] <= 1.0).all())

    def test_attention_tier_quantiles_and_terminology(self):
        """7. Verify exact quantile counts and absence of prohibited tier labels in dataset."""
        tier_counts = self.df_scores["attention_tier"].value_counts().to_dict()
        self.assertEqual(tier_counts.get("Tier 1"), 44)
        self.assertEqual(tier_counts.get("Tier 2"), 73)
        self.assertEqual(tier_counts.get("Tier 3"), 102)
        self.assertEqual(tier_counts.get("Tier 4"), 218)

        # Check that no prohibited terminology appears in the tier column
        prohibited_tier_names = ["Critical Risk", "High Risk", "Medium Risk", "Low Risk"]
        for bad_name in prohibited_tier_names:
            self.assertFalse((self.df_scores["attention_tier"] == bad_name).any())

    def test_canonical_project_keys_alignment_across_all_tables(self):
        """8. Verify exact key alignment across PIT, scores, explanations, and interventions."""
        pit_keys = set(self.df_pit["canonical_project_key"])
        score_keys = set(self.df_scores["canonical_project_key"])
        explanation_keys = set(self.df_explanations["canonical_project_key"])
        intervention_keys = set(self.df_interventions["canonical_project_key"])

        self.assertEqual(len(pit_keys), 437)
        self.assertEqual(pit_keys, score_keys)
        self.assertEqual(pit_keys, explanation_keys)
        self.assertEqual(pit_keys, intervention_keys)

        # Explanations must have each key exactly twice
        exp_counts = self.df_explanations["canonical_project_key"].value_counts()
        self.assertTrue((exp_counts == 2).all())

    def test_no_causal_or_punitive_language_in_artifacts(self):
        """9. Verify that textual fields in intervention priorities do NOT contain prohibited punitive terms."""
        prohibited_punitive_words = ["sanction", "penalty", "penalties", "punitive", "blacklist", "corrupt", "fault"]
        text_cols = ["primary_action", "secondary_action", "priority_reason"]

        for col in text_cols:
            for val in self.df_interventions[col].astype(str):
                for word in prohibited_punitive_words:
                    self.assertNotIn(word, val.lower(), f"Prohibited word '{word}' found in {col}: '{val}'")

    def test_contract_documentation_files_exist_and_cover_specifications(self):
        """10. Verify that product contract and handoff markdown reports exist and meet length/content criteria."""
        self.assertTrue(os.path.exists(self.product_contract_path))
        self.assertTrue(os.path.exists(self.handoff_path))

        with open(self.product_contract_path, "r", encoding="utf-8") as f:
            contract_text = f.read()
        with open(self.handoff_path, "r", encoding="utf-8") as f:
            handoff_text = f.read()

        self.assertGreater(len(contract_text), 5000)
        self.assertGreater(len(handoff_text), 5000)

        # Check endpoints in handoff
        required_endpoints = [
            "/projects",
            "/projects/{canonical_project_key}",
            "/projects/ranking",
            "/projects/{canonical_project_key}/risk",
            "/projects/{canonical_project_key}/drivers",
            "/projects/{canonical_project_key}/interventions",
            "/portfolio/summary"
        ]
        for ep in required_endpoints:
            self.assertIn(ep, handoff_text)

        # Check entities in handoff
        required_entities = [
            "projects",
            "project_risk_scores",
            "project_risk_explanations",
            "project_intervention_priorities"
        ]
        for ent in required_entities:
            self.assertIn(ent, handoff_text)

        # Check frontend components in handoff
        required_components = [
            "Portfolio Overview Dashboard",
            "Risk Ranking",
            "Project Detail",
            "Explainable Risk Drivers Panel",
            "Intervention Action Panel"
        ]
        for comp in required_components:
            self.assertIn(comp, handoff_text)

    def test_attention_score_is_explicitly_prioritization_index_not_joint_probability(self):
        """11. Verify attention_score is explicitly defined as a comparative portfolio prioritization index, not joint probability."""
        with open(self.product_contract_path, "r", encoding="utf-8") as f:
            contract_text = f.read()
        self.assertIn("comparative portfolio prioritization index, not a calibrated probability of joint failure", contract_text)

        prd_path = os.path.join(self.root_dir, "reports", "MASTER_PRD.md")
        with open(prd_path, "r", encoding="utf-8") as f:
            prd_text = f.read()
        self.assertIn("comparative portfolio prioritization index, not a calibrated probability of joint failure", prd_text)

if __name__ == "__main__":
    unittest.main()

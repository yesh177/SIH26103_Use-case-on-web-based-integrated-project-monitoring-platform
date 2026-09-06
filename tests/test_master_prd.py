import os
import unittest

class TestMasterPRD(unittest.TestCase):
    """
    Unit test suite verifying the authoritative Master PRD (Module 5 Phase 9A).
    Validates existence, mandatory sections, SIH requirements, PIT methodology,
    feature rules, partial coverage semantics, compound exposure non-joint representation,
    governance constraints, frozen artifact checksums, and absence of prohibited claims.
    """

    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.prd_path = os.path.join(cls.root_dir, "reports", "MASTER_PRD.md")

        # Ensure file exists
        if not os.path.exists(cls.prd_path):
            raise FileNotFoundError(f"MASTER_PRD.md not found at {cls.prd_path}")

        with open(cls.prd_path, "r", encoding="utf-8") as f:
            cls.prd_text = f.read()

    def test_01_master_prd_exists_and_non_empty(self):
        """1. Verify MASTER_PRD.md exists and is substantial (> 10,000 characters)."""
        self.assertTrue(os.path.exists(self.prd_path))
        self.assertGreater(len(self.prd_text), 10000)

    def test_02_all_mandatory_sections_exist(self):
        """2. Verify all 32 mandatory sections exist with exact numbering."""
        expected_sections = [
            "# 1. Document Control",
            "# 2. Executive Summary",
            "# 3. Problem Statement",
            "# 4. Product Vision",
            "# 5. Core USP",
            "# 6. Users & Stakeholders",
            "# 7. End-to-End Product Workflow",
            "# 8. Data Architecture",
            "# 9. Point-in-Time Methodology",
            "# 10. Feature Architecture",
            "# 11. ML Architecture",
            "# 12. Model Evaluation",
            "# 13. CUF vs Enhanced Evaluation",
            "# 14. Risk Scoring",
            "# 15. Risk Ranking",
            "# 16. Explainability",
            "# 17. Intervention Prioritisation",
            "# 18. Partial Coverage",
            "# 19. Product Requirements",
            "# 20. Frontend Requirements",
            "# 21. Backend Requirements",
            "# 22. Database Requirements",
            "# 23. Non-Functional Requirements",
            "# 24. Governance & Safety",
            "# 25. Success Metrics",
            "# 26. Team Responsibility Matrix",
            "# 27. Implementation Boundaries",
            "# 28. Demo Flow",
            "# 29. Pitch Technical Story",
            "# 30. Limitations",
            "# 31. Future Roadmap",
            "# 32. Traceability Matrix"
        ]
        for section in expected_sections:
            self.assertIn(section, self.prd_text, f"Missing mandatory section: {section}")

    def test_03_sih_problem_statement_referenced(self):
        """3. Verify SIH26103 is explicitly referenced."""
        self.assertIn("SIH26103", self.prd_text)

    def test_04_seven_sih_capabilities_represented(self):
        """4. Verify all seven required SIH capabilities are mapped."""
        sih_capabilities = [
            "Cost-Overrun Prediction",
            "Time-Overrun Prediction",
            "Project Risk Ranking",
            "Driver Analysis",
            "ML vs Conventional Statistical Methods",
            "CUF vs Enhanced Variables",
            "Early-Warning Decision Support"
        ]
        for cap in sih_capabilities:
            self.assertIn(cap, self.prd_text, f"Missing SIH capability: {cap}")

    def test_05_point_in_time_methodology_represented(self):
        """5. Verify Point-in-Time methodology and cutoff dates are documented."""
        self.assertIn("July 31, 2025", self.prd_text)
        self.assertIn("12 Months Forward", self.prd_text)
        self.assertIn("Leakage Prevention", self.prd_text)

    def test_06_cost_and_schedule_targets_represented(self):
        """6. Verify cost and schedule target names and definitions are documented."""
        self.assertIn("cost_overrun_5pct_2026", self.prd_text)
        self.assertIn("time_overrun_3m_2026", self.prd_text)

    def test_07_authorized_feature_list_represented(self):
        """7. Verify all 10 numeric features and 2 categorical features are listed."""
        required_features = [
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
            "feat_agency"
        ]
        for feat in required_features:
            self.assertIn(feat, self.prd_text, f"Missing authorized feature: {feat}")

    def test_08_sector_exclusion_represented(self):
        """8. Verify Sector exclusion is explicitly documented."""
        self.assertIn("Sector is strictly excluded", self.prd_text)

    def test_09_partial_coverage_semantics_represented(self):
        """9. Verify 132 partial coverage projects and strict NULL handling are documented."""
        self.assertIn("132", self.prd_text)
        self.assertIn("PARTIAL", self.prd_text)
        self.assertIn("SCHEDULE_OUTCOME_UNOBSERVED", self.prd_text)

    def test_10_compound_exposure_is_explicitly_non_joint(self):
        """10. Verify compound exposure is explicitly stated as NOT a joint probability."""
        self.assertIn("NOT a joint mathematical probability", self.prd_text)

    def test_11_tier_semantics_represented(self):
        """11. Verify quantile tiers and prohibition of Low/Medium/High/Critical risk labels."""
        self.assertIn("Tier 1", self.prd_text)
        self.assertIn("Tier 2", self.prd_text)
        self.assertIn("Tier 3", self.prd_text)
        self.assertIn("Tier 4", self.prd_text)
        self.assertIn('MUST NEVER be described as "Critical Risk"', self.prd_text)

    def test_12_explainability_non_causal_semantics_represented(self):
        """12. Verify MDI global and marginal perturbation local explainability are non-causal."""
        self.assertIn("Marginal Reference Perturbation", self.prd_text)
        self.assertIn("never causal roots", self.prd_text)

    def test_13_intervention_governance_represented(self):
        """13. Verify all 7 actions and prohibition of automated sanctions/penalties."""
        required_actions = [
            "DATA_QUALITY_REVIEW",
            "JOINT_COST_SCHEDULE_REVIEW",
            "SCHEDULE_REVIEW",
            "COMPLETION_STATUS_REVIEW",
            "COST_REVIEW",
            "PROGRESS_VERIFICATION",
            "EXPENDITURE_PROGRESS_REVIEW"
        ]
        for act in required_actions:
            self.assertIn(act, self.prd_text, f"Missing action: {act}")
        self.assertIn("Automated administrative sanctions", self.prd_text)

    def test_14_seven_api_endpoints_represented(self):
        """14. Verify all seven REST API endpoints are documented."""
        required_endpoints = [
            "GET /projects",
            "GET /projects/{canonical_project_key}",
            "GET /projects/ranking",
            "GET /projects/{canonical_project_key}/risk",
            "GET /projects/{canonical_project_key}/drivers",
            "GET /projects/{canonical_project_key}/interventions",
            "GET /portfolio/summary"
        ]
        for ep in required_endpoints:
            self.assertIn(ep, self.prd_text, f"Missing API endpoint: {ep}")

    def test_15_four_database_entities_represented(self):
        """15. Verify all four database entities are documented."""
        required_entities = [
            "`projects`",
            "`project_risk_scores`",
            "`project_risk_explanations`",
            "`project_intervention_priorities`"
        ]
        for ent in required_entities:
            self.assertIn(ent, self.prd_text, f"Missing database entity: {ent}")

    def test_16_five_frontend_components_represented(self):
        """16. Verify all five frontend components/screens are documented."""
        required_screens = [
            "Portfolio Overview Dashboard",
            "Risk Ranking Leaderboard",
            "Project Detail Profile",
            "Explainable Risk Drivers Panel",
            "Intervention Action Panel"
        ]
        for screen in required_screens:
            self.assertIn(screen, self.prd_text, f"Missing frontend screen: {screen}")

    def test_17_limitations_represented(self):
        """17. Verify mandatory limitations are documented."""
        self.assertIn("# 30. Limitations", self.prd_text)
        self.assertIn("Retrospective Holdout Scope", self.prd_text)
        self.assertIn("Schedule Outcome Missingness", self.prd_text)

    def test_18_future_roadmap_separated_from_done(self):
        """18. Verify clear demarcation between DONE, NEXT, and FUTURE."""
        self.assertIn("# 27. Implementation Boundaries", self.prd_text)
        self.assertIn("DONE (Completed & Frozen)", self.prd_text)
        self.assertIn("NEXT (Module 5 Application Phase)", self.prd_text)
        self.assertIn("FUTURE (Post-Hackathon / Production Roadmaps)", self.prd_text)

    def test_19_no_prohibited_claims_present(self):
        """19. Verify prohibited claims (guaranteed prediction, corruption proof, etc.) are absent or explicitly banned."""
        self.assertIn("No Causal Claims", self.prd_text)
        self.assertIn("No Agency or State Blaming", self.prd_text)
        self.assertIn("No Autonomous Sanctions", self.prd_text)
        self.assertIn("No Guaranteed Outcomes", self.prd_text)

    def test_20_frozen_artifact_hashes_referenced(self):
        """20. Verify SHA-256 hashes of frozen artifacts are referenced in the document."""
        required_hashes = [
            "052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329",
            "6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d",
            "5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2",
            "3dfacd2805610e0a1a9ff3f10461c97322a3bf62ca1dc348fc6baca13e012ec5"
        ]
        for h in required_hashes:
            self.assertIn(h, self.prd_text, f"Missing frozen hash in PRD: {h}")

if __name__ == "__main__":
    unittest.main()

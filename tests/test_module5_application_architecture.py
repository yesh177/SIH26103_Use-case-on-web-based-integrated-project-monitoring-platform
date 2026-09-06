import os
import unittest

class TestModule5ApplicationArchitecture(unittest.TestCase):
    """
    Unit test suite verifying the Module 5 Phase 9B.1 Application Architecture Specification.
    Validates existence, mandatory sections, 7 API endpoints, 5 frontend screens,
    4 database entities, frozen vs dynamic boundaries, prohibition of live retraining,
    partial coverage semantics, non-causal governance, compound exposure non-joint rules,
    and absence of application implementation code.
    """

    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.arch_path = os.path.join(cls.root_dir, "reports", "MODULE5_APPLICATION_ARCHITECTURE.md")

        if not os.path.exists(cls.arch_path):
            raise FileNotFoundError(f"Architecture specification not found at {cls.arch_path}")

        with open(cls.arch_path, "r", encoding="utf-8") as f:
            cls.arch_text = f.read()

    def test_01_architecture_document_exists_and_substantial(self):
        """1. Verify MODULE5_APPLICATION_ARCHITECTURE.md exists and is substantial (> 10,000 chars)."""
        self.assertTrue(os.path.exists(self.arch_path))
        self.assertGreater(len(self.arch_text), 10000)

    def test_02_all_required_sections_exist(self):
        """2. Verify all 15 required architecture sections exist with exact numbering."""
        expected_sections = [
            "# 1. System Overview",
            "# 2. High-Level System Architecture",
            "# 3. Technology Stack Recommendations",
            "# 4. End-to-End Data Flow",
            "# 5. Component Responsibilities & Architectural Boundaries",
            "# 6. Frozen vs. Dynamic System Boundary",
            "# 7. Database Implementation Architecture",
            "# 8. Backend Architecture & API Specifications",
            "# 9. Frontend Architecture & UI Specifications",
            "# 10. Recommended Repository Structure",
            "# 11. Team Responsibility Matrix",
            "# 12. Implementation Sequence (Build Order)",
            "# 13. MVP Boundaries & Scope",
            "# 14. Governance & Safety Safeguards",
            "# 15. Team Handoff Checklist"
        ]
        for section in expected_sections:
            self.assertIn(section, self.arch_text, f"Missing required section: {section}")

    def test_03_all_seven_authoritative_api_endpoints_present(self):
        """3. Verify all 7 authoritative REST endpoints are documented."""
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
            self.assertIn(ep, self.arch_text, f"Missing API endpoint: {ep}")

    def test_04_all_five_frontend_screens_present(self):
        """4. Verify all 5 authoritative frontend screens/components are documented."""
        required_screens = [
            "Portfolio Overview Dashboard",
            "Risk Ranking Table",
            "Project Detail Profile",
            "Explainable Risk Drivers Panel",
            "Intervention Action Panel"
        ]
        for screen in required_screens:
            self.assertIn(screen, self.arch_text, f"Missing frontend screen: {screen}")

    def test_05_all_four_database_entities_present(self):
        """5. Verify all 4 authoritative database entities are documented."""
        required_entities = [
            "`projects`",
            "`project_risk_scores`",
            "`project_risk_explanations`",
            "`project_intervention_priorities`"
        ]
        for ent in required_entities:
            self.assertIn(ent, self.arch_text, f"Missing database entity: {ent}")

    def test_06_frozen_vs_dynamic_boundary_explicitly_defined(self):
        """6. Verify frozen vs dynamic boundary section exists with explicit designations."""
        self.assertIn("# 6. Frozen vs. Dynamic System Boundary", self.arch_text)
        self.assertIn("FROZEN", self.arch_text)
        self.assertIn("DYNAMIC", self.arch_text)

    def test_07_live_retraining_explicitly_prohibited(self):
        """7. Verify live model retraining is explicitly prohibited in normal dashboard usage."""
        self.assertIn("DOES NOT retrain ML models", self.arch_text)
        self.assertIn("No Live Model Retraining", self.arch_text)

    def test_08_partial_coverage_semantics_preserved(self):
        """8. Verify PARTIAL coverage projects strictly have unobserved schedule outcomes and never zero risk."""
        self.assertIn("PARTIAL", self.arch_text)
        self.assertIn("SCHEDULE_OUTCOME_UNOBSERVED", self.arch_text)
        self.assertIn("Schedule Outcome Unavailable", self.arch_text)
        self.assertIn('NEVER as *"0.0%"*', self.arch_text)
        self.assertIn("unobserved, not zero risk", self.arch_text)

    def test_09_non_causal_governance_preserved(self):
        """9. Verify non-causal language and prohibition of automated sanctions/penalties."""
        self.assertIn("Non-Causal Language", self.arch_text)
        self.assertIn("No Agency or State Blaming", self.arch_text)
        self.assertIn("Automated administrative sanctions", self.arch_text)

    def test_10_compound_exposure_is_explicitly_non_joint(self):
        """10. Verify compound exposure is explicitly documented as NOT a joint probability."""
        self.assertIn("strictly NOT a joint mathematical probability", self.arch_text)

    def test_11_no_application_implementation_code_introduced(self):
        """11. Verify that no application implementation code was introduced in backend/ or frontend/."""
        backend_dir = os.path.join(self.root_dir, "backend")
        frontend_dir = os.path.join(self.root_dir, "frontend")

        # If directories exist, they must not contain actual application code (.py or .tsx/.ts implementation files)
        if os.path.exists(backend_dir):
            py_files = [f for f in os.listdir(backend_dir) if f.endswith(".py")]
            self.assertEqual(len(py_files), 0, "Backend application code must not be implemented in Phase 9B.1")

        if os.path.exists(frontend_dir):
            ts_files = [f for f in os.listdir(frontend_dir) if f.endswith(".tsx") or f.endswith(".ts")]
            self.assertEqual(len(ts_files), 0, "Frontend application code must not be implemented in Phase 9B.1")

if __name__ == "__main__":
    unittest.main()

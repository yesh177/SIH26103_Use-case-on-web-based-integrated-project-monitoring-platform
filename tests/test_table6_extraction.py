"""
Unit and regression tests for Table 6 (July 2026) extraction logic.

Validates:
1. Date and cost cell parsing.
2. Positional state mapping immunity against date-like patterns in project names
   (e.g., PB73/2023-24/NR, PB57/2019-20/NR, EPC/MORT&H/HRK/01/2021-22).
3. Preservation of missing approval dates (NA) without shifting subsequent dates (Serial 557).
4. Table structure invariants (strictly 8 columns, non-numeric state).
"""

import unittest
from src.ingestion.extract_table6 import (
    clean,
    parse_dates_cell,
    parse_costs_cell,
    parse_project,
)


class TestTable6Extraction(unittest.TestCase):
    """Regression test suite for July 2026 Table 6 extraction."""

    def test_parse_dates_cell_standard(self):
        """Verify standard 2-line date strings are parsed correctly."""
        top, paren = parse_dates_cell("03/2023\n(01/2024)")
        self.assertEqual(top, "03/2023")
        self.assertEqual(paren, "01/2024")

    def test_parse_dates_cell_with_dash_and_na(self):
        """Verify dash and NA values in dates are parsed as empty strings."""
        top, paren = parse_dates_cell("03/2027\n(-)")
        self.assertEqual(top, "03/2027")
        self.assertEqual(paren, "")

        top, paren = parse_dates_cell("NA\n(01/2022)")
        self.assertEqual(top, "")
        self.assertEqual(paren, "01/2022")

        top, paren = parse_dates_cell("NA\n(-)")
        self.assertEqual(top, "")
        self.assertEqual(paren, "")

        top, paren = parse_dates_cell("-\n(-)")
        self.assertEqual(top, "")
        self.assertEqual(paren, "")

    def test_parse_costs_cell(self):
        """Verify cost parsing handles parentheses, commas, and NA/dash."""
        orig, rev = parse_costs_cell("265.91\n(265.91)")
        self.assertEqual(orig, "265.91")
        self.assertEqual(rev, "265.91")

        orig, rev = parse_costs_cell("1,234.56\n(1,500.00)")
        self.assertEqual(orig, "1234.56")
        self.assertEqual(rev, "1500.00")

        orig, rev = parse_costs_cell("100.00\n(-)")
        self.assertEqual(orig, "100.00")
        self.assertEqual(rev, "")

    def test_regression_date_like_project_name_pb73(self):
        """
        Regression Test: Project names containing date-like strings like PB73/2023-24/NR
        must NOT corrupt the state column to the serial number (Sl 525).
        """
        mock_project = {
            "source_page": 80,
            "row_index": 5,
            "sl_no": 525,
            "project_code": "705375",
            "cells": [
                "525",
                "Rehab of road km 0 to 25 of PB73/2023-24/NR (PWD) (705375) (-) (-)",
                "Punjab",
                "03/2024\n(10/2024)",
                "04/2026\n(-)",
                "172.93\n(172.93)",
                "25.10",
                "15",
            ],
        }
        res = parse_project(mock_project)
        self.assertEqual(res["sl_no"], 525)
        self.assertEqual(res["project_id"], "705375")
        self.assertEqual(res["state"], "Punjab")
        self.assertNotEqual(res["state"], "525")
        self.assertEqual(res["approval_date"], "03/2024")
        self.assertEqual(res["start_date"], "10/2024")
        self.assertEqual(res["original_completion_date"], "04/2026")
        self.assertEqual(res["revised_completion_date"], "")
        self.assertEqual(res["original_cost_crore"], "172.93")
        self.assertEqual(res["revised_cost_crore"], "172.93")
        self.assertEqual(res["cumulative_expenditure_crore"], "25.10")
        self.assertEqual(res["physical_progress_pct"], "15")

    def test_regression_date_like_project_name_pb57(self):
        """
        Regression Test: Project names containing PB57/2019-20/NR (Sl 528).
        """
        mock_project = {
            "source_page": 80,
            "row_index": 8,
            "sl_no": 528,
            "project_code": "705378",
            "cells": [
                "528",
                "Widening to 4-lane of PB57/2019-20/NR (PWD) (705378) (-) (-)",
                "Punjab",
                "01/2020\n(06/2020)",
                "12/2022\n(03/2025)",
                "98.40\n(115.00)",
                "80.50",
                "70",
            ],
        }
        res = parse_project(mock_project)
        self.assertEqual(res["sl_no"], 528)
        self.assertEqual(res["state"], "Punjab")
        self.assertNotEqual(res["state"], "528")

    def test_regression_date_like_project_name_epc(self):
        """
        Regression Test: Project names containing EPC/MORT&H/HRK/01/2021-22 (Sl 532).
        """
        mock_project = {
            "source_page": 80,
            "row_index": 12,
            "sl_no": 532,
            "project_code": "705382",
            "cells": [
                "532",
                "Upgradation under EPC/MORT&H/HRK/01/2021-22 (NHAI) (705382) (-) (-)",
                "Haryana",
                "05/2021\n(11/2021)",
                "11/2023\n(06/2025)",
                "310.00\n(340.00)",
                "290.00",
                "85",
            ],
        }
        res = parse_project(mock_project)
        self.assertEqual(res["sl_no"], 532)
        self.assertEqual(res["state"], "Haryana")
        self.assertNotEqual(res["state"], "532")

    def test_regression_approval_date_shift_sl_557(self):
        """
        Regression Test: Approval Date = NA in source (Sl 557) must NOT cause
        subsequent dates (03/2031) to be shifted into approval_date.
        """
        mock_project = {
            "source_page": 82,
            "row_index": 15,
            "sl_no": 557,
            "project_code": "706865",
            "cells": [
                "557",
                "Construction of 4 lane bridge across river Zuari (NHAI) (706865) (-) (-)",
                "Goa",
                "NA\n(01/2022)",
                "03/2031\n(-)",
                "2534.50\n(2534.50)",
                "1850.00",
                "75",
            ],
        }
        res = parse_project(mock_project)
        self.assertEqual(res["sl_no"], 557)
        self.assertEqual(res["project_id"], "706865")
        self.assertEqual(res["state"], "Goa")
        self.assertEqual(res["approval_date"], "")
        self.assertEqual(res["start_date"], "01/2022")
        self.assertEqual(res["original_completion_date"], "03/2031")
        self.assertEqual(res["revised_completion_date"], "")

    def test_invariants_column_count_and_numeric_state(self):
        """Verify parse_project fails loudly if column count != 8 or state is numeric."""
        # Bad column count
        with self.assertRaises(ValueError):
            parse_project({
                "source_page": 1,
                "row_index": 1,
                "sl_no": 1,
                "project_code": "1001",
                "cells": ["1", "Name", "State"],
            })

        # Numeric state
        with self.assertRaises(ValueError):
            parse_project({
                "source_page": 1,
                "row_index": 1,
                "sl_no": 1,
                "project_code": "1001",
                "cells": ["1", "Name", "123", "01/2020", "01/2022", "100", "50", "50"],
            })


if __name__ == "__main__":
    unittest.main()

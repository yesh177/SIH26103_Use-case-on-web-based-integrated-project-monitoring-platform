from pathlib import Path
import csv
import re

import pdfplumber


PDF_PATH = Path("data/raw/flash_reports/FlashReport_July_2026.pdf")
OUTPUT_PATH = Path("data/interim/table6_july_2026_projects.csv")

START_PAGE = 55
END_PAGE = 152
EXPECTED_PROJECTS = 1775


def clean(value):
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def is_project_serial(value):
    value = clean(value)

    if not re.fullmatch(r"\d{1,4}", value):
        return False

    number = int(value)

    return 1 <= number <= EXPECTED_PROJECTS


def extract_project_code(text):
    """
    Project code is the first 5-8 digit number
    inside parentheses.
    """

    matches = re.findall(
        r"\((\d{5,8})\)",
        text
    )

    if not matches:
        return ""

    return matches[0]


def extract_tables():

    records = []

    with pdfplumber.open(PDF_PATH) as pdf:

        print(f"PDF: {PDF_PATH.name}")
        print(f"Total PDF pages: {len(pdf.pages)}")
        print(f"Processing pages: {START_PAGE} -> {END_PAGE}")
        print()

        for page_number in range(
            START_PAGE,
            END_PAGE + 1
        ):

            page = pdf.pages[page_number - 1]

            tables = page.extract_tables(
                {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 3,
                    "join_tolerance": 3,
                    "intersection_tolerance": 5,
                }
            )

            if not tables:

                tables = page.extract_tables(
                    {
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                        "intersection_tolerance": 5,
                        "min_words_vertical": 2,
                        "min_words_horizontal": 1,
                    }
                )

            if not tables:
                print(
                    f"WARNING: No table on page {page_number}"
                )
                continue

            table = tables[0]

            for row_index, row in enumerate(table):

                cells = [
                    clean(cell)
                    for cell in row
                ]

                records.append(
                    {
                        "source_page": page_number,
                        "row_index": row_index,
                        "cells": cells,
                    }
                )

    return records


def identify_project_rows(records):

    projects = []

    for record in records:

        cells = record["cells"]

        if not cells:
            continue

        serial = ""

        # Serial is normally in the first cell.
        for cell in cells[:2]:

            if is_project_serial(cell):
                serial = cell
                break

        if not serial:
            continue

        # Combine all non-empty cells.
        combined = " ".join(
            cell
            for cell in cells
            if cell
        )

        project_code = extract_project_code(
            combined
        )

        if not project_code:
            continue

        projects.append(
            {
                "source_page": record["source_page"],
                "row_index": record["row_index"],
                "sl_no": int(serial),
                "project_code": project_code,
                "cells": cells,
            }
        )

    return projects


def parse_dates_cell(cell_text):
    """
    Parse date cell with typically 2 lines:
    e.g. "03/2023\n(01/2024)" or "NA\n(01/2022)" or "03/2027\n(-)"
    Returns (top_date, paren_date).
    """
    s = clean(cell_text)
    paren_match = re.search(r"\(([^)]+)\)", s)
    paren_val = paren_match.group(1).strip() if paren_match else ""
    top_val = re.sub(r"\([^)]+\)", "", s).strip()

    if top_val.upper() in ["NA", "N.A.", "-", ""]:
        top_val = ""
    if paren_val.upper() in ["NA", "N.A.", "-", ""]:
        paren_val = ""

    return top_val, paren_val


def parse_costs_cell(cell_text):
    """
    Parse cost cell with typically 2 lines:
    e.g. "265.91\n(265.91)"
    Returns (orig_cost, rev_cost).
    """
    s = clean(cell_text)
    paren_match = re.search(r"\(([^)]+)\)", s)
    rev_val = paren_match.group(1).replace(",", "").strip() if paren_match else ""
    orig_val = re.sub(r"\([^)]+\)", "", s).replace(",", "").strip()

    if orig_val.upper() in ["NA", "N.A.", "-", ""]:
        orig_val = ""
    if rev_val.upper() in ["NA", "N.A.", "-", ""]:
        rev_val = ""

    return orig_val, rev_val


def clean_num(text):
    s = clean(text).replace(",", "").strip()
    if s.upper() in ["NA", "N.A.", "-", ""]:
        return ""
    return s


def parse_project(project):

    cells = project["cells"]

    # Table 6 confirmed standard layout has strictly 8 columns:
    # cell[0]: Sl.No
    # cell[1]: Project Name + Agency + Codes
    # cell[2]: State
    # cell[3]: Date of Approval (Start Date)
    # cell[4]: Original/Target DoC (Revised DoC)
    # cell[5]: Original Cost (Revised Cost)
    # cell[6]: Cumulative Expenditure
    # cell[7]: Physical Progress
    if len(cells) != 8:
        raise ValueError(
            f"Page {project['source_page']}, Sl {project['sl_no']}: "
            f"Expected 8 table columns, found {len(cells)}"
        )

    project_id = project["project_code"]
    proj_block = clean(cells[1])

    # -------------------------------------------------
    # PROJECT NAME + AGENCY
    # -------------------------------------------------

    code_marker = f"({project_id})"

    before_code = proj_block.split(code_marker, 1)[0].strip()
    before_code = re.sub(rf"^{project['sl_no']}\s*", "", before_code).strip()

    agency = ""
    agency_match = re.search(r"\(([^()]*)\)\s*$", before_code)

    if agency_match:
        agency = agency_match.group(1).strip()
        project_name = before_code[:agency_match.start()].strip()
    else:
        project_name = before_code

    # -------------------------------------------------
    # IDENTIFIERS
    # -------------------------------------------------

    after_code = proj_block.split(code_marker, 1)[1] if code_marker in proj_block else ""
    identifier_codes = re.findall(r"\(([^()]*)\)", after_code)

    legacy_ocms_code = identifier_codes[0].strip() if len(identifier_codes) >= 1 else ""
    pmgid = identifier_codes[1].strip() if len(identifier_codes) >= 2 else ""

    # -------------------------------------------------
    # STATE (DEDICATED COLUMN: cell[2])
    # -------------------------------------------------

    state = clean(cells[2])

    if not state:
        raise ValueError(
            f"Page {project['source_page']}, Sl {project['sl_no']}: "
            f"State column is empty"
        )

    if state.isdigit():
        raise ValueError(
            f"Page {project['source_page']}, Sl {project['sl_no']}: "
            f"State column contains numeric serial number '{state}' instead of valid state"
        )

    # -------------------------------------------------
    # DATES (DEDICATED COLUMNS: cell[3] and cell[4])
    # -------------------------------------------------

    approval_date, start_date = parse_dates_cell(cells[3])
    original_completion_date, revised_completion_date = parse_dates_cell(cells[4])

    # -------------------------------------------------
    # FINANCIAL DATA (DEDICATED COLUMNS: cell[5], [6], [7])
    # -------------------------------------------------

    original_cost, revised_cost = parse_costs_cell(cells[5])
    expenditure = clean_num(cells[6])
    physical_progress = clean_num(cells[7])

    return {
        "snapshot_date": "2026-07",
        "source_page": project["source_page"],
        "sl_no": project["sl_no"],
        "project_id": project_id,
        "project_name": project_name,
        "agency": agency,
        "legacy_ocms_code": legacy_ocms_code,
        "pmgid": pmgid,
        "state": state,
        "approval_date": approval_date,
        "start_date": start_date,
        "original_completion_date": original_completion_date,
        "revised_completion_date": revised_completion_date,
        "original_cost_crore": original_cost,
        "revised_cost_crore": revised_cost,
        "cumulative_expenditure_crore": expenditure,
        "physical_progress_pct": physical_progress,
    }


def save_projects(projects):

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    columns = [
        "snapshot_date",
        "source_page",
        "sl_no",
        "project_id",
        "project_name",
        "agency",
        "legacy_ocms_code",
        "pmgid",
        "state",
        "approval_date",
        "start_date",
        "original_completion_date",
        "revised_completion_date",
        "original_cost_crore",
        "revised_cost_crore",
        "cumulative_expenditure_crore",
        "physical_progress_pct",
    ]

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=columns
        )

        writer.writeheader()

        writer.writerows(projects)

    print(
        f"\nSaved: {OUTPUT_PATH}"
    )


def validate(projects):

    serials = [
        p["sl_no"]
        for p in projects
    ]

    project_ids = [
        p["project_id"]
        for p in projects
    ]

    unique_serials = set(serials)
    unique_ids = set(project_ids)

    expected = set(
        range(
            1,
            EXPECTED_PROJECTS + 1
        )
    )

    missing = sorted(
        expected - unique_serials
    )

    duplicate_serials = (
        len(serials)
        - len(unique_serials)
    )

    duplicate_ids = (
        len(project_ids)
        - len(unique_ids)
    )

    print()
    print("=" * 60)
    print("TABLE 6 EXTRACTION VALIDATION")
    print("=" * 60)

    print(
        f"Detected projects: {len(projects)}"
    )

    print(
        f"Expected projects: {EXPECTED_PROJECTS}"
    )

    print(
        f"Unique project IDs: {len(unique_ids)}"
    )

    print(
        f"Duplicate project IDs: {duplicate_ids}"
    )

    print(
        f"Duplicate serial numbers: {duplicate_serials}"
    )

    if serials:

        print(
            f"Minimum serial: {min(serials)}"
        )

        print(
            f"Maximum serial: {max(serials)}"
        )

    print(
        f"Missing serial numbers: {len(missing)}"
    )

    if missing:

        print(
            "First missing:",
            missing[:30]
        )

    print("=" * 60)

    if (
        len(projects) == EXPECTED_PROJECTS
        and len(unique_ids) == EXPECTED_PROJECTS
        and duplicate_ids == 0
        and duplicate_serials == 0
        and not missing
    ):

        print(
            "SUCCESS: 1,775 projects extracted."
        )

    else:

        print(
            "STATUS: Extraction requires further validation."
        )


def main():

    if not PDF_PATH.exists():

        raise FileNotFoundError(
            f"PDF not found: {PDF_PATH}"
        )

    records = extract_tables()

    print(
        f"\nTotal physical table rows: "
        f"{len(records)}"
    )

    projects = identify_project_rows(
        records
    )

    print(
        f"Detected project table rows: "
        f"{len(projects)}"
    )

    parsed_projects = [
        parse_project(project)
        for project in projects
    ]

    save_projects(
        parsed_projects
    )

    validate(
        parsed_projects
    )


if __name__ == "__main__":
    main()
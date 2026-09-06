"""
PAIMANA Predictive Risk Intelligence
Module 2A: July 2025 Flash Report - Table 4 Extractor

Extracts all ongoing project records (Table 4: "All Ongoing Projects")
from FlashReport_July_2025.pdf using PyMuPDF raw text extraction.

PDF pages: 37-66 (1-indexed)
Expected projects: Serials 1 through 791 exactly once.
Output: data/interim/table4_july_2025_projects.csv
"""

from collections import Counter
from pathlib import Path
import csv
import re
import sys

import pymupdf


PDF_PATH = Path("data/raw/flash_reports/FlashReport_July_2025.pdf")
OUTPUT_PATH = Path("data/interim/table4_july_2025_projects.csv")

START_PAGE = 37  # 1-indexed
END_PAGE = 66    # 1-indexed
EXPECTED_TOTAL = 791

FIELDNAMES = [
    "snapshot_date",
    "source_page",
    "sl_no",
    "project_id",
    "project_name",
    "agency",
    "state",
    "approval_date",
    "original_completion_date",
    "revised_completion_date",
    "original_cost_crore",
    "revised_cost_crore",
    "cumulative_expenditure_crore",
    "physical_progress_pct",
]


def clean_text(text: str) -> str:
    """Normalize internal whitespace and strip leading/trailing spaces."""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def extract_table4_projects(pdf_path: Path):
    """
    Extract Table 4 projects from PDF using sequential serial boundaries
    over PyMuPDF raw text lines.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    print(f"Opened PDF: {pdf_path.name}")
    print(f"Total pages in document: {len(doc)}")
    print(f"Extracting Table 4 from pages {START_PAGE} to {END_PAGE} (inclusive)...")

    all_page_lines = []
    for page_idx in range(START_PAGE - 1, END_PAGE):
        page = doc[page_idx]
        lines = [line.strip() for line in page.get_text().splitlines() if line.strip()]
        all_page_lines.append((page_idx + 1, lines))

    expected_serial = 1
    parsed_blocks = []

    for page_no, lines in all_page_lines:
        serials_on_page = []
        for idx, line in enumerate(lines):
            if line == str(expected_serial):
                # Verify project context: project code in parens within next 25 lines
                context = " ".join(lines[idx : idx + 25])
                if re.search(r"\(\d{4,}\)", context):
                    serials_on_page.append((expected_serial, idx))
                    expected_serial += 1

        for i, (serial_num, start_idx) in enumerate(serials_on_page):
            if i + 1 < len(serials_on_page):
                end_idx = serials_on_page[i + 1][1]
            else:
                end_idx = len(lines)
                for j in range(start_idx, len(lines)):
                    if (
                        lines[j].startswith("Total (")
                        or lines[j].startswith("Total(")
                        or "Project Assessment" in lines[j]
                        or lines[j].startswith("Page ")
                    ):
                        end_idx = j
                        break

            block_lines = lines[start_idx:end_idx]
            parsed_blocks.append((serial_num, page_no, block_lines))

    print(f"Collected raw project blocks: {len(parsed_blocks)}")

    projects = []
    for s, page_no, bl in parsed_blocks:
        # 1. Project ID: matches (digits)
        proj_id_indices = [
            i for i, l in enumerate(bl) if re.fullmatch(r"\((\d{4,})\)", l)
        ]
        if not proj_id_indices:
            raise ValueError(f"Could not locate project ID for serial {s} on page {page_no}: {bl}")

        proj_id_idx = proj_id_indices[0]
        proj_id = re.fullmatch(r"\((\d{4,})\)", bl[proj_id_idx]).group(1)

        # 2. Agency: line preceding project ID
        raw_agency = bl[proj_id_idx - 1]
        if raw_agency.startswith("(") and raw_agency.endswith(")"):
            agency = raw_agency[1:-1].strip()
        else:
            agency = raw_agency.strip()
        agency = clean_text(agency)

        # 3. Project Name: lines between serial number and agency
        project_name = clean_text(" ".join(bl[1 : proj_id_idx - 1]))

        # 4. Remaining tokens after project ID
        rem = bl[proj_id_idx + 1 :]

        # 5. Date tokens in remainder
        date_indices = [
            i for i, l in enumerate(rem) if re.fullmatch(r"\d{2}/\d{4}", l) or l in ("(-)", "-")
        ]
        if not date_indices:
            raise ValueError(f"No dates found for serial {s} on page {page_no}: {bl}")

        first_date_idx = date_indices[0]
        last_date_idx = date_indices[-1]

        # 6. State: text between project ID and first date token
        state = clean_text(" ".join(rem[:first_date_idx]))

        # 7. Approval, Original DoC, Revised DoC
        if len(date_indices) >= 3:
            approval_date = rem[date_indices[0]]
            original_completion_date = rem[date_indices[1]]
            revised_completion_date = rem[date_indices[2]]
        else:
            # Source PDF omits approval date for rows without it (e.g. serials 525, 526, 648)
            approval_date = ""
            original_completion_date = rem[date_indices[0]]
            revised_completion_date = rem[date_indices[1]]

        # 8. Financials and physical progress
        after_dates = rem[last_date_idx + 1 :]
        if len(after_dates) < 4:
            raise ValueError(
                f"Incomplete financial values for serial {s} on page {page_no}: {after_dates}"
            )

        original_cost_crore = after_dates[0]
        revised_cost_crore = re.sub(r"[\(\)]", "", after_dates[1]).strip()
        cumulative_expenditure_crore = after_dates[2]
        physical_progress_pct = after_dates[3]

        projects.append(
            {
                "snapshot_date": "2025-07",
                "source_page": str(page_no),
                "sl_no": str(s),
                "project_id": proj_id,
                "project_name": project_name,
                "agency": agency,
                "state": state,
                "approval_date": approval_date,
                "original_completion_date": original_completion_date,
                "revised_completion_date": revised_completion_date,
                "original_cost_crore": original_cost_crore,
                "revised_cost_crore": revised_cost_crore,
                "cumulative_expenditure_crore": cumulative_expenditure_crore,
                "physical_progress_pct": physical_progress_pct,
            }
        )

    return projects


def save_projects_csv(projects, output_path: Path):
    """Write projects list of dicts to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(projects)
    print(f"Saved {len(projects)} records to: {output_path}")


def validate_extraction(projects):
    """Run validation checks on extracted project records."""
    serials = [int(p["sl_no"]) for p in projects]
    serial_counts = Counter(serials)

    extracted_count = len(projects)
    unique_count = len(set(serials))
    min_serial = min(serials) if serials else 0
    max_serial = max(serials) if serials else 0
    duplicate_serials = sorted([s for s, c in serial_counts.items() if c > 1])
    missing_serials = sorted(
        [s for s in range(1, EXPECTED_TOTAL + 1) if s not in serial_counts]
    )

    print()
    print("=" * 70)
    print("JULY 2025 TABLE 4 EXTRACTION VALIDATION REPORT")
    print("=" * 70)
    print(f"Extracted count   : {extracted_count}")
    print(f"Unique count      : {unique_count}")
    print(f"Min serial        : {min_serial}")
    print(f"Max serial        : {max_serial}")
    print(f"Duplicate serials : {duplicate_serials}")
    print(f"Missing serials   : {missing_serials}")

    proj_ids = [p["project_id"] for p in projects]
    unique_proj_ids = len(set(proj_ids))
    print(f"Unique project IDs: {unique_proj_ids} / {extracted_count}")
    print("=" * 70)

    # Strict assertion
    is_valid = (
        extracted_count == EXPECTED_TOTAL
        and unique_count == EXPECTED_TOTAL
        and min_serial == 1
        and max_serial == EXPECTED_TOTAL
        and len(duplicate_serials) == 0
        and len(missing_serials) == 0
    )

    if is_valid:
        print("SUCCESS: All serials 1-791 extracted exactly once!")
    else:
        print("FAILURE: Validation criteria not satisfied.")
        sys.exit(1)


def main():
    projects = extract_table4_projects(PDF_PATH)
    save_projects_csv(projects, OUTPUT_PATH)
    validate_extraction(projects)


if __name__ == "__main__":
    main()

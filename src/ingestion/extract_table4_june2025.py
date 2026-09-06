"""
PAIMANA Predictive Risk Intelligence
Module 2A: June 2025 Flash Report - Project Table Extractor

Extracts all ongoing project records ("All Ongoing Projects")
from FlashReport_June_2025.pdf using PyMuPDF raw stream text extraction.

Reuses the proven extraction architecture from Module 2A July 2025
(src/ingestion/extract_table4_july2025.py) while dynamically adapting to
June 2025 page ranges and table structure.

Expected output: data/interim/table4_june_2025_projects.csv
"""

from collections import Counter
from pathlib import Path
import csv
import re
import sys

import pymupdf


PDF_PATH = Path("data/raw/flash_reports/FlashReport_June_2025.pdf")
OUTPUT_PATH = Path("data/interim/table4_june_2025_projects.csv")

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


def locate_project_table_pages(doc: pymupdf.Document):
    """
    Locate the page range containing 'All Ongoing Projects'.
    Scans document for headers and project rows.
    """
    start_page = None
    end_page = None

    for idx, page in enumerate(doc):
        text = page.get_text()
        if "all ongoing projects" in text.lower():
            if start_page is None:
                start_page = idx + 1
            end_page = idx + 1
        elif start_page is not None and re.search(r"(?m)^\s*1\s*$", text):
            end_page = idx + 1

    # Fallback to general scan if explicit heading differs
    if start_page is None:
        # Search for Table 4 or project tables
        for idx, page in enumerate(doc):
            text = page.get_text()
            if "table 4" in text.lower() or "table 6" in text.lower():
                if start_page is None:
                    start_page = idx + 1
                end_page = idx + 1

    return start_page, end_page


def extract_table4_june2025(pdf_path: Path):
    """
    Extract June 2025 project records using sequential serial boundaries
    over PyMuPDF raw text streams.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Raw source PDF not found: {pdf_path}\n"
            f"Please ensure '{pdf_path.name}' has been acquired and placed into '{pdf_path.parent}'."
        )

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    print(f"Opened PDF: {pdf_path.name}")
    print(f"Total document pages: {total_pages}")

    start_page, end_page = locate_project_table_pages(doc)
    if start_page is None or end_page is None:
        # Default fallback to scanning pages 30 through total_pages
        start_page = 30
        end_page = total_pages

    print(f"Targeting project table pages: {start_page} to {end_page} (inclusive)...")

    all_page_lines = []
    for page_idx in range(start_page - 1, end_page):
        page = doc[page_idx]
        lines = [l.strip() for l in page.get_text().splitlines() if l.strip()]
        all_page_lines.append((page_idx + 1, lines))

    expected_serial = 1
    parsed_blocks = []

    for page_no, lines in all_page_lines:
        serials_on_page = []
        for idx, line in enumerate(lines):
            if line == str(expected_serial):
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
    if not parsed_blocks:
        raise ValueError("No project records were identified in the specified page range.")

    projects = []
    for s, page_no, bl in parsed_blocks:
        # Project ID
        proj_id_indices = [
            i for i, l in enumerate(bl) if re.fullmatch(r"\(\d{4,}\)", l)
        ]
        if not proj_id_indices:
            raise ValueError(f"Could not locate project ID for serial {s} on page {page_no}: {bl}")

        proj_id_idx = proj_id_indices[0]
        proj_id = re.fullmatch(r"\(\d{4,}\)", bl[proj_id_idx]).group(1)

        # Agency
        raw_agency = bl[proj_id_idx - 1]
        if raw_agency.startswith("(") and raw_agency.endswith(")"):
            agency = raw_agency[1:-1].strip()
        else:
            agency = raw_agency.strip()
        agency = clean_text(agency)

        # Project Name
        project_name = clean_text(" ".join(bl[1 : proj_id_idx - 1]))

        # Remainder after project ID
        rem = bl[proj_id_idx + 1 :]

        # Dates
        date_indices = [
            i for i, l in enumerate(rem) if re.fullmatch(r"\d{2}/\d{4}", l) or l in ("(-)", "-")
        ]
        if not date_indices:
            raise ValueError(f"No dates found for serial {s} on page {page_no}: {bl}")

        first_date_idx = date_indices[0]
        last_date_idx = date_indices[-1]

        # State
        state = clean_text(" ".join(rem[:first_date_idx]))

        # Approval & DoC dates
        if len(date_indices) >= 3:
            approval_date = rem[date_indices[0]]
            original_completion_date = rem[date_indices[1]]
            revised_completion_date = rem[date_indices[2]]
        else:
            approval_date = ""
            original_completion_date = rem[date_indices[0]]
            revised_completion_date = rem[date_indices[1]]

        # Financials & Progress
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
                "snapshot_date": "2025-06",
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
    """Save extracted projects to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(projects)
    print(f"Saved {len(projects)} records to: {output_path}")


def validate_extraction(projects):
    """Validate serial range, uniqueness, and completeness."""
    serials = [int(p["sl_no"]) for p in projects]
    serial_counts = Counter(serials)

    extracted_count = len(projects)
    unique_count = len(set(serials))
    min_serial = min(serials) if serials else 0
    max_serial = max(serials) if serials else 0
    duplicate_serials = sorted([s for s, c in serial_counts.items() if c > 1])
    expected_total = max_serial
    missing_serials = sorted(
        [s for s in range(1, expected_total + 1) if s not in serial_counts]
    )

    print()
    print("=" * 70)
    print("JUNE 2025 TABLE 4 EXTRACTION VALIDATION REPORT")
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

    is_valid = (
        extracted_count > 0
        and extracted_count == expected_total
        and unique_count == expected_total
        and min_serial == 1
        and len(duplicate_serials) == 0
        and len(missing_serials) == 0
    )

    if is_valid:
        print(f"SUCCESS: All serials 1-{expected_total} extracted exactly once!")
    else:
        print("FAILURE: Validation criteria not satisfied. Refusing to claim success.")
        sys.exit(1)


def main():
    try:
        projects = extract_table4_june2025(PDF_PATH)
        save_projects_csv(projects, OUTPUT_PATH)
        validate_extraction(projects)
    except FileNotFoundError as e:
        print()
        print("=" * 70)
        print("EXTRACTION HALTED: RAW SOURCE PDF NOT FOUND")
        print("=" * 70)
        print(e)
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Module 2A: June 2025 Table 7 Deterministic Extractor.

Extracts all 1,595 ongoing central sector projects from Table 7:
"Project List: Ongoing Projects as of 30th June 2025"
in FlashReport_June_2025.pdf (pages 41-229 inclusive) using PyMuPDF.

Preserves source-observed formatting, distinguishes Original/Revised/Anticipated
dates and costs, and propagats hierarchical State and Sector headers.
"""

import csv
import re
import sys
from pathlib import Path
import pymupdf


PDF_PATH = Path("data/raw/flash_reports/FlashReport_June_2025.pdf")
OUTPUT_CSV = Path("data/interim/table7_june_2025_projects.csv")

SNAPSHOT_DATE = "2025-06-30"
START_PAGE = 41
END_PAGE = 229
EXPECTED_ROWS = 1595


def parse_project_block_robust(proj_words):
    """
    Parse project name, agency, and project_id from the project block words.
    In Table 7, the project description block contains:
      - Project Name (multi-line)
      - (Agency Name)
      - (Project Code) e.g. (N04000073) or legacy numeric (220100265)
    """
    lines = []
    curr_line = []
    curr_y = None
    for w in proj_words:
        if curr_y is None or abs(w[1] - curr_y) <= 3:
            curr_line.append(w[4])
            curr_y = w[1]
        else:
            lines.append(" ".join(curr_line))
            curr_line = [w[4]]
            curr_y = w[1]
    if curr_line:
        lines.append(" ".join(curr_line))

    project_id = ""
    agency = ""
    lines = [l.strip() for l in lines if l.strip()]

    code_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i]
        m = re.search(r'\(?\s*([A-Z0-9]{8,10})\s*\)?', line)
        if m:
            val = m.group(1)
            # Must have digits and not be common text abbreviations
            if any(c.isdigit() for c in val) and not any(k in val.lower() for k in ["km", "pkg", "phase", "mva", "mw"]):
                project_id = val
                code_idx = i
                break

    if code_idx != -1:
        if code_idx > 0:
            agency_line = lines[code_idx - 1]
            m_paren = re.search(r'\(\s*([^)]+)\s*\)', agency_line)
            m_ag = re.search(r'\(?\s*([A-Za-z0-9\s&/\.\-_]{2,30})\s*\)?', agency_line)
            if m_paren:
                agency = m_paren.group(1).strip()
                agency_idx = code_idx - 1
            elif m_ag and any(c.isalpha() for c in m_ag.group(1)):
                agency = m_ag.group(1).strip()
                agency_idx = code_idx - 1
            else:
                agency_idx = code_idx
        else:
            agency_idx = code_idx

        name_lines = lines[:agency_idx]
    else:
        name_lines = lines

    project_name = " ".join(name_lines).strip()
    return project_name, agency, project_id


def parse_dates_block(dates_text):
    """
    Parse Original, Revised, and Anticipated commissioning dates.
    Format:
      - Original: M/YYYY or MM/YYYY
      - Revised: in parentheses (Mon-YYYY) or (M/YYYY) or (N.A.)
      - Anticipated: in braces {M/YYYY} or {Mon-YYYY} or {N.A.}
    """
    s = dates_text.strip()
    ant_match = re.search(r'\{([^}]+)\}', s)
    ant_date = ant_match.group(1).strip() if ant_match else ""
    s_no_ant = re.sub(r'\{[^}]+\}', '', s).strip()

    rev_match = re.search(r'\(([^)]+)\)', s_no_ant)
    rev_date = rev_match.group(1).strip() if rev_match else ""
    orig_date = re.sub(r'\([^)]+\)', '', s_no_ant).strip()

    if orig_date.upper() in ["N.A.", "NA", "-", ""]:
        orig_date = ""
    if rev_date.upper() in ["N.A.", "NA", "-", ""]:
        rev_date = ""
    if ant_date.upper() in ["N.A.", "NA", "-", ""]:
        ant_date = ""

    return orig_date, rev_date, ant_date


def parse_costs_block(costs_text):
    """
    Parse Original, Revised, and Anticipated cost in Rs. Crore.
    Format:
      - Original: numeric decimal string
      - Revised: in parentheses (numeric) or (N.A.)
      - Anticipated: in braces {numeric} or {N.A.}
    """
    s = costs_text.strip()
    ant_match = re.search(r'\{([^}]+)\}', s)
    ant_cost = ant_match.group(1).strip() if ant_match else ""
    s_no_ant = re.sub(r'\{[^}]+\}', '', s).strip()

    rev_match = re.search(r'\(([^)]+)\)', s_no_ant)
    rev_cost = rev_match.group(1).strip() if rev_match else ""
    orig_cost = re.sub(r'\([^)]+\)', '', s_no_ant).strip()

    def clean_num(val):
        val = val.replace(',', '').strip()
        if val.upper() in ["N.A.", "NA", "-", ""]:
            return ""
        return val

    return clean_num(orig_cost), clean_num(rev_cost), clean_num(ant_cost)


def clean_decimal(text):
    """Clean numeric decimal string, preserving empty on NA/-."""
    val = text.replace(',', '').strip()
    if val.upper() in ["N.A.", "NA", "-", ""]:
        return ""
    return val


def extract_table7():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found at {PDF_PATH}")

    doc = pymupdf.open(PDF_PATH)
    records = []
    current_state = None
    current_sector = None

    for p_num in range(START_PAGE, END_PAGE + 1):
        page = doc[p_num - 1]
        words = page.get_text("words")
        table_words = [w for w in words if 130 <= w[1] <= 768]

        # Stop before summary Total row if present on page
        total_y = None
        for w in table_words:
            if w[4].lower() == "total":
                total_y = w[1] - 3
                break

        # Detect serial numbers in serial column [125, 158]
        serial_words = [w for w in table_words if 125 <= w[0] <= 158 and w[4].isdigit()]
        serial_words.sort(key=lambda w: w[1])

        for i, sw in enumerate(serial_words):
            sl_no = int(sw[4])
            y_top = sw[1] - 3
            if i + 1 < len(serial_words):
                y_bot = serial_words[i+1][1] - 3
            elif total_y is not None:
                y_bot = total_y
            else:
                y_bot = 768.0

            row_words = [w for w in table_words if y_top <= w[1] < y_bot]

            # Hierarchical State heading [10, 75]
            state_w = sorted([w for w in row_words if 10 <= w[0] < 75], key=lambda w: (w[1], w[0]))
            if state_w:
                st_text = " ".join(w[4] for w in state_w).strip()
                if len(st_text) > 2:
                    current_state = st_text

            # Hierarchical Sector heading [75, 130]
            sector_w = sorted([w for w in row_words if 75 <= w[0] < 130], key=lambda w: (w[1], w[0]))
            if sector_w:
                sec_text = " ".join(w[4] for w in sector_w).strip()
                if len(sec_text) > 2:
                    if sec_text.startswith("TELECOMMUNI"):
                        sec_text = "TELECOMMUNICATIONS"
                    current_sector = sec_text

            # Column slices
            proj_w = sorted([w for w in row_words if 155 <= w[0] < 295], key=lambda w: (w[1], w[0]))
            appr_w = sorted([w for w in row_words if 295 <= w[0] < 335], key=lambda w: (w[1], w[0]))
            dates_w = sorted([w for w in row_words if 335 <= w[0] < 420], key=lambda w: (w[1], w[0]))
            costs_w = sorted([w for w in row_words if 420 <= w[0] < 490], key=lambda w: (w[1], w[0]))
            exp_w = sorted([w for w in row_words if 490 <= w[0] < 555], key=lambda w: (w[1], w[0]))
            prog_w = sorted([w for w in row_words if 555 <= w[0] < 600], key=lambda w: (w[1], w[0]))

            name, agency, pid = parse_project_block_robust(proj_w)
            appr_date = " ".join(w[4] for w in appr_w).strip()
            orig_d, rev_d, ant_d = parse_dates_block(" ".join(w[4] for w in dates_w))
            orig_c, rev_c, ant_c = parse_costs_block(" ".join(w[4] for w in costs_w))
            exp = clean_decimal(" ".join(w[4] for w in exp_w))
            prog = clean_decimal(" ".join(w[4] for w in prog_w))

            records.append({
                "snapshot_date": SNAPSHOT_DATE,
                "source_page": p_num,
                "sl_no": sl_no,
                "project_id": pid,
                "project_name": name,
                "agency": agency,
                "state": current_state,
                "sector": current_sector,
                "approval_date": appr_date,
                "original_completion_date": orig_d,
                "revised_completion_date": rev_d,
                "anticipated_completion_date": ant_d,
                "original_cost_crore": orig_c,
                "revised_cost_crore": rev_c,
                "anticipated_cost_crore": ant_c,
                "cumulative_expenditure_crore": exp,
                "physical_progress_pct": prog,
            })

    # Sanity checks before writing
    if len(records) != EXPECTED_ROWS:
        raise ValueError(f"Extracted {len(records)} rows, expected {EXPECTED_ROWS}")

    serials = [r["sl_no"] for r in records]
    if serials != list(range(1, EXPECTED_ROWS + 1)):
        raise ValueError("Serial numbers are not strictly 1..1595")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "snapshot_date",
        "source_page",
        "sl_no",
        "project_id",
        "project_name",
        "agency",
        "state",
        "sector",
        "approval_date",
        "original_completion_date",
        "revised_completion_date",
        "anticipated_completion_date",
        "original_cost_crore",
        "revised_cost_crore",
        "anticipated_cost_crore",
        "cumulative_expenditure_crore",
        "physical_progress_pct",
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully extracted {len(records)} rows to {OUTPUT_CSV}")
    return records


if __name__ == "__main__":
    extract_table7()

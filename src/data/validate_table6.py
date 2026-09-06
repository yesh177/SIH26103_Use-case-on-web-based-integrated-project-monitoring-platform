from pathlib import Path
import csv
import re
from collections import Counter


INPUT_PATH = Path("data/interim/table6_july_2026_projects.csv")

EXPECTED_ROWS = 1775
MIN_PAGE = 55
MAX_PAGE = 152


REQUIRED_COLUMNS = [
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


def is_month_year(value):
    if not value:
        return True

    return bool(
        re.fullmatch(r"\d{2}/\d{4}", value.strip())
    )


def to_float(value):
    if value is None or value.strip() == "":
        return None

    return float(value)


def main():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_PATH}"
        )

    with INPUT_PATH.open(
        encoding="utf-8",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        rows = list(reader)
        columns = reader.fieldnames or []

    print("=" * 70)
    print("TABLE 6 SEMANTIC / DATA-QUALITY VALIDATION")
    print("=" * 70)

    # --------------------------------------------------
    # 1. Row count
    # --------------------------------------------------

    print(f"Rows: {len(rows)}")
    print(f"Expected: {EXPECTED_ROWS}")

    # --------------------------------------------------
    # 2. Schema
    # --------------------------------------------------

    missing_columns = [
        c for c in REQUIRED_COLUMNS
        if c not in columns
    ]

    print(
        f"Missing required columns: "
        f"{len(missing_columns)}"
    )

    if missing_columns:
        print("Missing:", missing_columns)

    # --------------------------------------------------
    # 3. Project IDs
    # --------------------------------------------------

    project_ids = [
        r["project_id"].strip()
        for r in rows
        if r["project_id"].strip()
    ]

    duplicate_ids = [
        pid
        for pid, count in Counter(project_ids).items()
        if count > 1
    ]

    print(
        f"Unique project IDs: "
        f"{len(set(project_ids))}"
    )

    print(
        f"Duplicate project IDs: "
        f"{len(duplicate_ids)}"
    )

    # --------------------------------------------------
    # 4. Serial numbers
    # --------------------------------------------------

    serials = []

    for r in rows:
        try:
            serials.append(int(r["sl_no"]))
        except ValueError:
            pass

    expected_serials = set(
        range(1, EXPECTED_ROWS + 1)
    )

    actual_serials = set(serials)

    missing_serials = sorted(
        expected_serials - actual_serials
    )

    duplicate_serials = [
        serial
        for serial, count in Counter(serials).items()
        if count > 1
    ]

    print(
        f"Missing serial numbers: "
        f"{len(missing_serials)}"
    )

    print(
        f"Duplicate serial numbers: "
        f"{len(duplicate_serials)}"
    )

    # --------------------------------------------------
    # 5. Missing critical fields
    # --------------------------------------------------

    critical_fields = [
        "project_id",
        "project_name",
        "state",
        "original_cost_crore",
        "revised_cost_crore",
        "cumulative_expenditure_crore",
        "physical_progress_pct",
    ]

    print("\nMISSING VALUES")

    for field in critical_fields:

        missing = sum(
            not r[field].strip()
            for r in rows
        )

        print(
            f"{field}: {missing}"
        )

    # --------------------------------------------------
    # 6. Numeric validation
    # --------------------------------------------------

    invalid_progress = []
    negative_cost = []
    negative_revised_cost = []
    negative_expenditure = []
    expenditure_over_revised = []
    revised_less_original = []

    total_original = 0.0
    total_revised = 0.0
    total_expenditure = 0.0

    progress_values = []

    for r in rows:

        try:

            progress = to_float(
                r["physical_progress_pct"]
            )

            if progress is not None:

                progress_values.append(progress)

                if progress < 0 or progress > 100:

                    invalid_progress.append(
                        r["sl_no"]
                    )

        except ValueError:

            invalid_progress.append(
                r["sl_no"]
            )

        try:

            original = to_float(
                r["original_cost_crore"]
            )

            revised = to_float(
                r["revised_cost_crore"]
            )

            expenditure = to_float(
                r["cumulative_expenditure_crore"]
            )

            if original is not None:
                total_original += original

                if original < 0:
                    negative_cost.append(
                        r["sl_no"]
                    )

            if revised is not None:
                total_revised += revised

                if revised < 0:
                    negative_revised_cost.append(
                        r["sl_no"]
                    )

            if expenditure is not None:
                total_expenditure += expenditure

                if expenditure < 0:
                    negative_expenditure.append(
                        r["sl_no"]
                    )

            if (
                original is not None
                and revised is not None
                and revised < original
            ):
                revised_less_original.append(
                    r["sl_no"]
                )

            if (
                expenditure is not None
                and revised is not None
                and expenditure > revised
            ):
                expenditure_over_revised.append(
                    r["sl_no"]
                )

        except ValueError:
            pass

    print("\nNUMERIC VALIDATION")

    print(
        f"Invalid physical progress: "
        f"{len(invalid_progress)}"
    )

    print(
        f"Negative original cost: "
        f"{len(negative_cost)}"
    )

    print(
        f"Negative revised cost: "
        f"{len(negative_revised_cost)}"
    )

    print(
        f"Negative expenditure: "
        f"{len(negative_expenditure)}"
    )

    print(
        f"Revised cost < original cost: "
        f"{len(revised_less_original)}"
    )

    print(
        f"Expenditure > revised cost: "
        f"{len(expenditure_over_revised)}"
    )

    # --------------------------------------------------
    # 7. Date validation
    # --------------------------------------------------

    date_fields = [
        "approval_date",
        "start_date",
        "original_completion_date",
        "revised_completion_date",
    ]

    print("\nDATE VALIDATION")

    for field in date_fields:

        invalid = sum(
            not is_month_year(r[field])
            for r in rows
        )

        print(
            f"{field}: invalid = {invalid}"
        )

    # --------------------------------------------------
    # 8. Source page validation
    # --------------------------------------------------

    invalid_pages = []

    for r in rows:

        try:

            page = int(r["source_page"])

            if page < MIN_PAGE or page > MAX_PAGE:
                invalid_pages.append(
                    r["sl_no"]
                )

        except ValueError:

            invalid_pages.append(
                r["sl_no"]
            )

    print("\nSOURCE VALIDATION")

    print(
        f"Invalid source pages: "
        f"{len(invalid_pages)}"
    )

    # --------------------------------------------------
    # 9. Summary statistics
    # --------------------------------------------------

    print("\nDATASET TOTALS")

    print(
        f"Original cost total: "
        f"{total_original:,.2f} crore"
    )

    print(
        f"Revised cost total: "
        f"{total_revised:,.2f} crore"
    )

    print(
        f"Cumulative expenditure total: "
        f"{total_expenditure:,.2f} crore"
    )

    if progress_values:

        print(
            f"Physical progress min: "
            f"{min(progress_values):.2f}%"
        )

        print(
            f"Physical progress max: "
            f"{max(progress_values):.2f}%"
        )

        print(
            f"Physical progress average: "
            f"{sum(progress_values) / len(progress_values):.2f}%"
        )

    # --------------------------------------------------
    # 10. Final status
    # --------------------------------------------------

    hard_failures = (
        len(rows) != EXPECTED_ROWS
        or len(set(project_ids)) != EXPECTED_ROWS
        or duplicate_ids
        or missing_serials
        or duplicate_serials
        or missing_columns
        or invalid_progress
        or negative_cost
        or negative_revised_cost
        or negative_expenditure
        or invalid_pages
    )

    print("\n" + "=" * 70)

    if hard_failures:

        print(
            "STATUS: DATASET REQUIRES INVESTIGATION"
        )

    else:

        print(
            "STATUS: STRUCTURAL + BASIC SEMANTIC VALIDATION PASSED"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()
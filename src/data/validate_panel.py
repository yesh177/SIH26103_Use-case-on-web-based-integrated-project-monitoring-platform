"""
PAIMANA Panel Data Validator & Contract Enforcement Module.

Authoritative Specifications:
- docs/pit_feature_specification.md
- docs/target_definition.md
- docs/data_contract.md
- docs/leakage_rules.md
- reports/module1_data_validation.md

Enforces schema invariants, identity constraints, temporal ordering, numeric bounds,
panel density, and point-in-time (PIT) anti-leakage rules.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd


# ==============================================================================
# 1. CANONICAL COLUMN CLASSIFICATIONS
# ==============================================================================

REQUIRED_COLUMNS: Set[str] = {
    "reporting_period",
    "project_code",
    "project_name",
    "sector",
    "line_ministry",
    "original_cost_cr",
    "original_end_date",
    "expenditure_cr",
}

OPTIONAL_COLUMNS: Set[str] = {
    "revised_cost_cr",
    "revised_end_date",
    "start_date",
    "physical_progress_pct",
    "agency",
    "state",
}

DERIVED_COLUMNS: Set[str] = {
    "cost_growth_ratio",
    "expenditure_to_original_cost",
    "expenditure_to_revised_cost",
    "schedule_slippage_days",
    "project_age_days",
    "elapsed_duration_ratio",
    "progress_gap",
    "expenditure_progress_gap",
    "recent_cost_change",
    "recent_expenditure_change",
    "recent_progress_change",
    "recent_schedule_change",
}

FORBIDDEN_FEATURE_COLUMNS: Set[str] = {
    "target",
    "label",
    "future_slip",
    "future_slip_days",
    "future_schedule_deterioration",
    "future_cost_escalation",
    "future_cost_overrun",
    "actual_completion_date",
    "commissioning_date",
    "actual_doc",
    "final_cost",
    "final_cost_overrun",
}

YEAR_MONTH_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


# ==============================================================================
# 2. VALIDATION RESULT DATA STRUCTURES
# ==============================================================================

@dataclass
class ValidationIssue:
    gate: str
    severity: str  # "HARD_FAIL", "WARNING", "INFO"
    rule_id: str
    message: str
    sample_data: Optional[Dict[str, Any]] = None


@dataclass
class PanelDensityStats:
    total_projects: int = 0
    single_period_projects: int = 0
    multi_period_projects: int = 0
    max_periods_observed: int = 0
    min_periods_observed: int = 0
    projects_with_gaps: int = 0
    consecutive_pairs_count: int = 0
    period_distribution: Dict[str, int] = field(default_factory=dict)


@dataclass
class ValidationReport:
    status: str  # "PASS", "FAIL", "SNAPSHOT_ONLY"
    total_rows: int = 0
    total_projects: int = 0
    total_periods: int = 0
    periods_observed: List[str] = field(default_factory=list)
    missing_required_columns: List[str] = field(default_factory=list)
    missing_value_counts: Dict[str, int] = field(default_factory=dict)
    density_stats: PanelDensityStats = field(default_factory=PanelDensityStats)
    issues: List[ValidationIssue] = field(default_factory=list)
    cutoff_date: Optional[str] = None

    @property
    def hard_fails(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "HARD_FAIL"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "WARNING"]


# ==============================================================================
# 3. CORE PANEL VALIDATOR
# ==============================================================================

class PanelDataValidator:
    """Automated validator enforcing the PAIMANA Ingestion Contract and PIT Leakage Rules."""

    def __init__(
        self,
        cutoff_date: Optional[str] = None,
        is_feature_matrix: bool = False,
        allow_snapshot_only: bool = False,
    ):
        self.cutoff_date = cutoff_date
        self.is_feature_matrix = is_feature_matrix
        self.allow_snapshot_only = allow_snapshot_only

    def validate(self, df: pd.DataFrame) -> ValidationReport:
        report = ValidationReport(
            status="PASS",
            total_rows=len(df),
            cutoff_date=self.cutoff_date,
        )

        # Standardize column naming (strip whitespace, lowercase)
        df_clean = df.copy()
        df_clean.columns = [str(c).strip().lower().replace("\n", " ").replace(" ", "_") for c in df_clean.columns]

        # Aliases / normalization mapping
        aliases = {
            "sr._no.": "sr_no",
            "sector_name": "sector",
            "original_cost": "original_cost_cr",
            "original_cost_(in_cr.)": "original_cost_cr",
            "revised_cost": "revised_cost_cr",
            "revised_cost_(in_cr.)": "revised_cost_cr",
            "expenditure": "expenditure_cr",
            "expenditure_(in_cr.)": "expenditure_cr",
            "cumulative_expenditure": "expenditure_cr",
            "original_end_date": "original_end_date",
            "original_doc": "original_end_date",
            "revised_date": "revised_end_date",
            "revised_doc": "revised_end_date",
            "physical_progress": "physical_progress_pct",
        }
        renames = {k: v for k, v in aliases.items() if k in df_clean.columns and v not in df_clean.columns}
        if renames:
            df_clean = df_clean.rename(columns=renames)

        # Gate 1: Schema Validation
        self._gate_1_schema(df_clean, report)

        # Early check: if reporting_period is missing entirely, check if single snapshot
        if "reporting_period" not in df_clean.columns:
            if "project_code" in df_clean.columns and "original_cost_cr" in df_clean.columns:
                report.status = "SNAPSHOT_ONLY"
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 1 (Schema)",
                        severity="HARD_FAIL",
                        rule_id="DC-SCHEMA-01",
                        message="SNAPSHOT_ONLY - INSUFFICIENT FOR LONGITUDINAL PREDICTIVE MODELING: 'reporting_period' column is missing.",
                    )
                )
                self._compute_cross_sectional_metrics(df_clean, report)
                return report

        # Gate 2: Identity & Primary Key
        self._gate_2_identity(df_clean, report)

        # Gate 3: Temporal Integrity
        self._gate_3_temporal(df_clean, report)

        # Gate 4: Numeric Integrity & Non-Negativity
        self._gate_4_numeric(df_clean, report)

        # Gate 5: Panel Density & Longitudinal Structure
        self._gate_5_panel_density(df_clean, report)

        # Gate 6: PIT Anti-Leakage Rules (LR-01 through LR-07)
        self._gate_6_leakage(df_clean, report)

        # Gate 7: Derived Feature Validation (if derived columns present)
        self._gate_7_derived_features(df_clean, report)

        # Gate 8: Target Validation (if target columns present)
        self._gate_8_target(df_clean, report)

        # Final Status Determination
        if any(i.severity == "HARD_FAIL" for i in report.issues):
            if report.status != "SNAPSHOT_ONLY":
                report.status = "FAIL"
        else:
            report.status = "PASS"

        return report

    # --------------------------------------------------------------------------
    # GATE 1: SCHEMA
    # --------------------------------------------------------------------------
    def _gate_1_schema(self, df: pd.DataFrame, report: ValidationReport) -> None:
        missing_req = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        report.missing_required_columns = missing_req
        if missing_req:
            report.issues.append(
                ValidationIssue(
                    gate="Gate 1 (Schema)",
                    severity="HARD_FAIL",
                    rule_id="DC-SCHEMA-01",
                    message=f"Missing required canonical columns: {sorted(missing_req)}",
                )
            )

        # Compute missing values for existing columns
        for c in df.columns:
            report.missing_value_counts[c] = int(df[c].isna().sum())

    # --------------------------------------------------------------------------
    # GATE 2: IDENTITY
    # --------------------------------------------------------------------------
    def _gate_2_identity(self, df: pd.DataFrame, report: ValidationReport) -> None:
        if "project_code" in df.columns:
            null_projects = df["project_code"].isna().sum()
            if null_projects > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 2 (Identity)",
                        severity="HARD_FAIL",
                        rule_id="DC-IDENTITY-01",
                        message=f"Detected {null_projects} rows with NULL project_code.",
                    )
                )

        if "reporting_period" in df.columns:
            null_periods = df["reporting_period"].isna().sum()
            if null_periods > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 2 (Identity)",
                        severity="HARD_FAIL",
                        rule_id="DC-IDENTITY-02",
                        message=f"Detected {null_periods} rows with NULL reporting_period.",
                    )
                )

        if "project_code" in df.columns and "reporting_period" in df.columns:
            dups = df.duplicated(subset=["project_code", "reporting_period"]).sum()
            if dups > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 2 (Identity)",
                        severity="HARD_FAIL",
                        rule_id="DC-IDENTITY-03",
                        message=f"Detected {dups} duplicate (project_code, reporting_period) rows.",
                    )
                )

    # --------------------------------------------------------------------------
    # GATE 3: TEMPORAL INTEGRITY
    # --------------------------------------------------------------------------
    def _gate_3_temporal(self, df: pd.DataFrame, report: ValidationReport) -> None:
        if "reporting_period" not in df.columns:
            return

        # Check format YYYY-MM
        periods = df["reporting_period"].dropna().astype(str).unique()
        invalid_format = [p for p in periods if not YEAR_MONTH_REGEX.match(p)]
        if invalid_format:
            report.issues.append(
                ValidationIssue(
                    gate="Gate 3 (Temporal)",
                    severity="HARD_FAIL",
                    rule_id="DC-TIME-01",
                    message=f"Invalid reporting_period format (must be YYYY-MM): {invalid_format[:5]}",
                )
            )

        report.periods_observed = sorted(list(periods))
        report.total_periods = len(report.periods_observed)

        # Check single-period vs longitudinal
        if report.total_periods <= 1 and not self.allow_snapshot_only:
            report.status = "SNAPSHOT_ONLY"
            report.issues.append(
                ValidationIssue(
                    gate="Gate 3 (Temporal)",
                    severity="HARD_FAIL",
                    rule_id="DC-TIME-02",
                    message=f"SNAPSHOT_ONLY - INSUFFICIENT FOR LONGITUDINAL PREDICTIVE MODELING: Only {report.total_periods} reporting period observed ({report.periods_observed}).",
                )
            )

        # Check date columns parseability
        date_cols = [c for c in ["start_date", "original_end_date", "revised_end_date"] if c in df.columns]
        for dc in date_cols:
            parsed = pd.to_datetime(df[dc], format="mixed", errors="coerce")
            unparseable = (df[dc].notna()) & (parsed.isna())
            if unparseable.sum() > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 3 (Temporal)",
                        severity="HARD_FAIL",
                        rule_id="DC-TIME-03",
                        message=f"Column '{dc}' contains {unparseable.sum()} unparseable dates.",
                    )
                )

    # --------------------------------------------------------------------------
    # GATE 4: NUMERIC INTEGRITY
    # --------------------------------------------------------------------------
    def _gate_4_numeric(self, df: pd.DataFrame, report: ValidationReport) -> None:
        # Original Cost: Must be strictly > 0
        if "original_cost_cr" in df.columns:
            cost = pd.to_numeric(df["original_cost_cr"], errors="coerce")
            neg_or_zero = (cost <= 0).sum()
            if neg_or_zero > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 4 (Numeric)",
                        severity="HARD_FAIL",
                        rule_id="DC-NUM-01",
                        message=f"Column 'original_cost_cr' has {neg_or_zero} values <= 0.",
                    )
                )

        # Expenditure: Must be >= 0
        if "expenditure_cr" in df.columns:
            exp = pd.to_numeric(df["expenditure_cr"], errors="coerce")
            neg_exp = (exp < 0).sum()
            if neg_exp > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 4 (Numeric)",
                        severity="HARD_FAIL",
                        rule_id="DC-NUM-02",
                        message=f"Column 'expenditure_cr' has {neg_exp} negative values.",
                    )
                )

        # Revised Cost: When present and > 0, check logical boundaries
        if "revised_cost_cr" in df.columns and "original_cost_cr" in df.columns:
            rev_cost = pd.to_numeric(df["revised_cost_cr"], errors="coerce")
            orig_cost = pd.to_numeric(df["original_cost_cr"], errors="coerce")
            neg_rev = (rev_cost < 0).sum()
            if neg_rev > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 4 (Numeric)",
                        severity="HARD_FAIL",
                        rule_id="DC-NUM-03",
                        message=f"Column 'revised_cost_cr' has {neg_rev} negative values.",
                    )
                )
            # Warning: De-scoped / lower cost
            descoped = ((rev_cost > 0) & (rev_cost < orig_cost)).sum()
            if descoped > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 4 (Numeric)",
                        severity="WARNING",
                        rule_id="DC-NUM-WARN-01",
                        message=f"{descoped} projects have revised_cost < original_cost (potential de-scoping).",
                    )
                )

        # Physical Progress: Must be in [0, 100] when present
        if "physical_progress_pct" in df.columns:
            prog = pd.to_numeric(df["physical_progress_pct"], errors="coerce")
            out_of_bounds = ((prog < 0) | (prog > 100)).sum()
            if out_of_bounds > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 4 (Numeric)",
                        severity="HARD_FAIL",
                        rule_id="DC-NUM-04",
                        message=f"Column 'physical_progress_pct' has {out_of_bounds} values outside [0.0, 100.0].",
                    )
                )

    # --------------------------------------------------------------------------
    # GATE 5: PANEL DENSITY & LONGITUDINAL STRUCTURE
    # --------------------------------------------------------------------------
    def _gate_5_panel_density(self, df: pd.DataFrame, report: ValidationReport) -> None:
        if "project_code" not in df.columns or "reporting_period" not in df.columns:
            return

        report.total_projects = int(df["project_code"].nunique())
        stats = PanelDensityStats(total_projects=report.total_projects)

        # Count periods per project
        project_counts = df.groupby("project_code")["reporting_period"].agg(
            periods_count="nunique",
            min_period="min",
            max_period="max",
            period_list=lambda x: sorted(list(x.unique())),
        )

        stats.single_period_projects = int((project_counts["periods_count"] == 1).sum())
        stats.multi_period_projects = int((project_counts["periods_count"] > 1).sum())
        stats.max_periods_observed = int(project_counts["periods_count"].max()) if len(project_counts) > 0 else 0
        stats.min_periods_observed = int(project_counts["periods_count"].min()) if len(project_counts) > 0 else 0

        # Distribution of periods
        period_dist = df["reporting_period"].value_counts().to_dict()
        stats.period_distribution = {str(k): int(v) for k, v in sorted(period_dist.items())}

        # Check for temporal gaps (e.g. observed in May and July, missing June)
        gaps_count = 0
        consecutive_pairs = 0
        for _, row in project_counts.iterrows():
            plist = row["period_list"]
            if len(plist) > 1:
                # Calculate month diffs
                parsed_dates = []
                for p in plist:
                    try:
                        parsed_dates.append(datetime.strptime(str(p).strip(), "%Y-%m"))
                    except (ValueError, TypeError):
                        pass
                for i in range(len(parsed_dates) - 1):
                    d1, d2 = parsed_dates[i], parsed_dates[i + 1]
                    month_diff = (d2.year - d1.year) * 12 + (d2.month - d1.month)
                    if month_diff == 1:
                        consecutive_pairs += 1
                    elif month_diff > 1:
                        gaps_count += 1

        stats.projects_with_gaps = gaps_count
        stats.consecutive_pairs_count = consecutive_pairs
        report.density_stats = stats

        if stats.multi_period_projects == 0 and not self.allow_snapshot_only:
            report.status = "SNAPSHOT_ONLY"
            report.issues.append(
                ValidationIssue(
                    gate="Gate 5 (Panel Density)",
                    severity="HARD_FAIL",
                    rule_id="DC-DENSITY-01",
                    message="SNAPSHOT_ONLY - INSUFFICIENT FOR LONGITUDINAL PREDICTIVE MODELING: Zero projects with multi-month longitudinal observations.",
                )
            )

    # --------------------------------------------------------------------------
    # GATE 6: PIT ANTI-LEAKAGE RULES (LR-01 THROUGH LR-07)
    # --------------------------------------------------------------------------
    def _gate_6_leakage(self, df: pd.DataFrame, report: ValidationReport) -> None:
        # LR-05 & LR-06: Target variables & post-outcome variables in feature matrix
        if self.is_feature_matrix:
            post_outcome_cols = {
                "actual_completion_date",
                "commissioning_date",
                "actual_doc",
                "final_cost",
                "final_cost_overrun",
            }

            target_leakage = []
            post_outcome_leakage = []

            for c in df.columns:
                c_lower = c.lower().strip()
                if c_lower in post_outcome_cols:
                    post_outcome_leakage.append(c)
                elif (
                    c_lower in FORBIDDEN_FEATURE_COLUMNS
                    or c_lower.startswith("future_")
                    or c_lower.endswith("_target")
                    or c_lower in {"target", "label"}
                ):
                    target_leakage.append(c)

            if target_leakage:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 6 (PIT Leakage)",
                        severity="HARD_FAIL",
                        rule_id="LR-05",
                        message=f"Target-derived or future-outcome columns found in feature matrix: {sorted(target_leakage)}",
                    )
                )

            if post_outcome_leakage:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 6 (PIT Leakage)",
                        severity="HARD_FAIL",
                        rule_id="LR-06",
                        message=f"Post-outcome realization columns found in feature matrix: {sorted(post_outcome_leakage)}",
                    )
                )

            # Check if project_code or project_name are fed as features
            if "project_code" in df.columns:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 6 (PIT Leakage)",
                        severity="WARNING",
                        rule_id="LR-ENTITY",
                        message="'project_code' is present; must be excluded from predictive feature matrix before model training.",
                    )
                )

        # LR-01 through LR-04: Enforce snapshot cutoff date t
        if self.cutoff_date and "reporting_period" in df.columns:
            future_obs = (df["reporting_period"] > self.cutoff_date).sum()
            if future_obs > 0:
                report.issues.append(
                    ValidationIssue(
                        gate="Gate 6 (PIT Leakage)",
                        severity="HARD_FAIL",
                        rule_id="LR-01-04",
                        message=f"Cutoff violation: {future_obs} observations have reporting_period > declared cutoff '{self.cutoff_date}'.",
                    )
                )

    # --------------------------------------------------------------------------
    # GATE 7: DERIVED FEATURE VALIDATION (VELOCITY CONTINUITY)
    # --------------------------------------------------------------------------
    def _gate_7_derived_features(self, df: pd.DataFrame, report: ValidationReport) -> None:
        derived_present = [c for c in DERIVED_COLUMNS if c in df.columns]
        if not derived_present:
            return  # Raw data is not expected to contain derived features

        # For velocity features, check that preceding observation exists and is exactly 1 calendar month prior
        velocity_cols = [
            c for c in ["recent_cost_change", "recent_expenditure_change", "recent_progress_change", "recent_schedule_change"]
            if c in df.columns
        ]
        if velocity_cols and "project_code" in df.columns and "reporting_period" in df.columns:
            df_sorted = df.sort_values(by=["project_code", "reporting_period"]).copy()

            prev_project = df_sorted["project_code"].shift(1)
            same_project = df_sorted["project_code"] == prev_project

            # Parse YYYY-MM dates to calculate calendar month diff
            curr_dates = pd.to_datetime(df_sorted["reporting_period"].astype(str).str.strip(), format="%Y-%m", errors="coerce")
            prev_dates = curr_dates.shift(1)

            year_diff = curr_dates.dt.year - prev_dates.dt.year
            month_diff = curr_dates.dt.month - prev_dates.dt.month
            cal_month_diff = year_diff * 12 + month_diff

            # A velocity value is strictly valid ONLY when preceded by the same project exactly 1 calendar month earlier
            is_valid_consecutive = same_project & (cal_month_diff == 1)

            for vc in velocity_cols:
                # Any non-consecutive or first observation MUST be NaN
                invalid_non_nan = (~is_valid_consecutive & df_sorted[vc].notna()).sum()
                if invalid_non_nan > 0:
                    report.issues.append(
                        ValidationIssue(
                            gate="Gate 7 (Derived Features)",
                            severity="HARD_FAIL",
                            rule_id="DC-DERIVED-01",
                            message=(
                                f"Velocity feature '{vc}' has {invalid_non_nan} non-NaN values where the preceding "
                                "calendar month is missing or not exactly 1 month prior (requires genuinely observed consecutive month)."
                            ),
                        )
                    )

    # --------------------------------------------------------------------------
    # GATE 8: TARGET VALIDATION (GENERALIZED LEAKAGE CHECK)
    # --------------------------------------------------------------------------
    def _gate_8_target(self, df: pd.DataFrame, report: ValidationReport) -> None:
        candidate_target_cols = [
            c for c in df.columns
            if c.lower().strip() in {"target", "label", "future_slip", "future_cost_escalation"}
            or c.lower().strip().startswith("future_")
            or c.lower().strip().endswith("_target")
        ]

        if not candidate_target_cols:
            return

        for tc in candidate_target_cols:
            target_series = pd.to_numeric(df[tc], errors="coerce")
            valid_idx = target_series.dropna().index
            if len(valid_idx) == 0:
                continue

            # Check 1: Schedule Current Status Leakage (revised_doc > original_doc)
            if "revised_end_date" in df.columns and "original_end_date" in df.columns:
                rev_d = pd.to_datetime(df["revised_end_date"], errors="coerce")
                orig_d = pd.to_datetime(df["original_end_date"], errors="coerce")
                date_mask = rev_d.notna() & orig_d.notna()
                common_idx = valid_idx.intersection(df[date_mask].index)

                if len(common_idx) > 0:
                    current_delay = (rev_d.loc[common_idx] > orig_d.loc[common_idx]).astype(int)
                    if (target_series.loc[common_idx] == current_delay).all():
                        report.issues.append(
                            ValidationIssue(
                                gate="Gate 8 (Target Construction)",
                                severity="HARD_FAIL",
                                rule_id="DC-TARGET-01",
                                message=(
                                    f"Target column '{tc}' is identical to current schedule delay status "
                                    "(revised_doc > original_doc). Instantaneous delay leakage detected."
                                ),
                            )
                        )

            # Check 2: Cost Current Status Leakage (revised_cost > original_cost)
            if "revised_cost_cr" in df.columns and "original_cost_cr" in df.columns:
                rev_c = pd.to_numeric(df["revised_cost_cr"], errors="coerce")
                orig_c = pd.to_numeric(df["original_cost_cr"], errors="coerce")
                cost_mask = rev_c.notna() & orig_c.notna()
                common_idx = valid_idx.intersection(df[cost_mask].index)

                if len(common_idx) > 0:
                    current_cost_overrun = (rev_c.loc[common_idx] > orig_c.loc[common_idx]).astype(int)
                    if (target_series.loc[common_idx] == current_cost_overrun).all():
                        report.issues.append(
                            ValidationIssue(
                                gate="Gate 8 (Target Construction)",
                                severity="HARD_FAIL",
                                rule_id="DC-TARGET-02",
                                message=(
                                    f"Target column '{tc}' is identical to current cost overrun status "
                                    "(revised_cost > original_cost). Instantaneous cost leakage detected."
                                ),
                            )
                        )

    # --------------------------------------------------------------------------
    # HELPER: CROSS-SECTIONAL INSPECTION
    # --------------------------------------------------------------------------
    def _compute_cross_sectional_metrics(self, df: pd.DataFrame, report: ValidationReport) -> None:
        if "project_code" in df.columns:
            report.total_projects = int(df["project_code"].nunique())
            report.density_stats.total_projects = report.total_projects
            report.density_stats.single_period_projects = report.total_projects
            report.density_stats.multi_period_projects = 0


# ==============================================================================
# 4. CLI INTERFACE & FORMATTING
# ==============================================================================

def format_validation_summary(report: ValidationReport, filepath: str) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("PAIMANA DATA CONTRACT & PANEL VALIDATION REPORT")
    lines.append("=" * 78)
    lines.append(f"Target File:       {filepath}")
    lines.append(f"Execution Date:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Declared Cutoff:   {report.cutoff_date if report.cutoff_date else 'None (Full History)'}")
    lines.append(f"Overall Status:    {report.status}")
    lines.append("-" * 78)
    lines.append("DIMENSIONALITY & IDENTITY:")
    lines.append(f"  Total Rows:             {report.total_rows:,}")
    lines.append(f"  Unique Projects:        {report.total_projects:,}")
    lines.append(f"  Reporting Periods:      {report.total_periods} {report.periods_observed}")
    lines.append("-" * 78)
    lines.append("PANEL DENSITY & LONGITUDINAL PROFILE:")
    d = report.density_stats
    lines.append(f"  Single-Period Projects: {d.single_period_projects:,}")
    lines.append(f"  Multi-Period Projects:  {d.multi_period_projects:,}")
    lines.append(f"  Max Observed Periods:   {d.max_periods_observed}")
    lines.append(f"  Consecutive Pairs:      {d.consecutive_pairs_count:,}")
    lines.append(f"  Projects with Gaps:     {d.projects_with_gaps:,}")
    if d.period_distribution:
        lines.append("  Distribution per Period:")
        for p, count in d.period_distribution.items():
            lines.append(f"    - {p}: {count:,} projects")
    lines.append("-" * 78)

    hard_fails = report.hard_fails
    warnings = report.warnings

    lines.append(f"VALIDATION GATES:  {len(hard_fails)} Hard Fails, {len(warnings)} Warnings")
    if hard_fails:
        lines.append("\nHARD FAILS (Blocking Pipeline Execution):")
        for i, hf in enumerate(hard_fails, 1):
            lines.append(f"  [{i}] {hf.gate} - {hf.rule_id}: {hf.message}")

    if warnings:
        lines.append("\nWARNINGS (Audit Log):")
        for i, w in enumerate(warnings, 1):
            lines.append(f"  [{i}] {w.gate} - {w.rule_id}: {w.message}")

    lines.append("=" * 78)
    if report.status == "PASS":
        lines.append("RESULT: [PASS] Dataset conforms to PAIMANA Data Contract & PIT Invariants.")
    elif report.status == "SNAPSHOT_ONLY":
        lines.append("RESULT: [SNAPSHOT_ONLY] Cross-sectional snapshot detected.")
        lines.append("        INSUFFICIENT FOR LONGITUDINAL PREDICTIVE MODELING.")
    else:
        lines.append("RESULT: [FAIL] Dataset REJECTED by Validation Gates.")
    lines.append("=" * 78)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a longitudinal PAIMANA dataset against the authoritative Data Contract & PIT rules."
    )
    parser.add_argument("input_csv", help="Path to input CSV dataset to validate.")
    parser.add_argument("--cutoff", dest="cutoff", default=None, help="Declared snapshot cutoff period (YYYY-MM).")
    parser.add_argument("--feature-matrix", dest="is_feature_matrix", action="store_true", help="Validate as feature matrix (LR-05 check).")
    parser.add_argument("--allow-snapshot", dest="allow_snapshot", action="store_true", help="Do not exit with failure on single snapshot.")

    args = parser.parse_args()
    input_path = Path(args.input_csv)

    if not input_path.exists():
        print(f"[ERROR] Input file does not exist: {input_path}", file=sys.stderr)
        return 1

    try:
        # Check if first line is title
        with open(input_path, "r", encoding="utf-8", errors="replace") as f:
            first_line = f.readline()
        skiprows = 2 if "Projects Details" in first_line else 0

        df = pd.read_csv(input_path, skiprows=skiprows)
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}", file=sys.stderr)
        return 1

    validator = PanelDataValidator(
        cutoff_date=args.cutoff,
        is_feature_matrix=args.is_feature_matrix,
        allow_snapshot_only=args.allow_snapshot,
    )
    report = validator.validate(df)
    summary_text = format_validation_summary(report, str(input_path))
    print(summary_text)

    if report.status == "PASS":
        return 0
    elif report.status == "SNAPSHOT_ONLY":
        return 2 if not args.allow_snapshot else 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

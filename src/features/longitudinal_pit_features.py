"""
PAIMANA Generic Longitudinal Point-in-Time (PIT) Feature Builder.

Authoritative Specifications:
- docs/pit_feature_specification.md (Sections 1-4: PIT Model, Inventory, Derived Features, Model A vs B)
- docs/leakage_rules.md (Rules LR-01 through LR-07: Anti-Leakage Invariants)
- docs/data_contract.md (Ingestion schema and validation constraints)

Guarantees:
1. Operates at (project_code, reporting_period) canonical longitudinal grain.
2. Strict PIT cutoff enforcement: features at time t use ONLY data available at or before t.
3. Zero future leakage: never accesses t+1 or later data.
4. Supports irregular / missing monthly observations; preserves authentic gaps.
5. Preserves NaN for unavailable velocity/lag features; never backfills or interpolates.
6. Sets is_first_observation=1 when prior authentic observation (t-1) is unavailable.
7. Computes all 12 authoritative derived/velocity features:
   - 1. cost_growth_ratio
   - 2. expenditure_to_original_cost (Raw CUF)
   - 3. expenditure_to_revised_cost (Adjusted CUF)
   - 4. schedule_slippage_days
   - 5. project_age_days
   - 6. elapsed_duration_ratio
   - 7. progress_gap
   - 8. expenditure_progress_gap
   - 9. recent_cost_change
   - 10. recent_expenditure_change
   - 11. recent_progress_change
   - 12. recent_schedule_change
8. Explicitly separates Model A (official CUF baseline) vs Model B (enhanced PIT + velocity) feature sets.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, date
import calendar
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd


# ==============================================================================
# 1. CUSTOM EXCEPTIONS
# ==============================================================================

class PITFeatureError(ValueError):
    """Base exception for errors during PIT feature engineering."""
    pass


class PITLeakageError(PITFeatureError):
    """Raised when future data leaks into PIT feature construction."""
    pass


# ==============================================================================
# 2. COLUMN MAPPING CONFIGURATION
# ==============================================================================

@dataclass
class PITColumnConfig:
    """Configurable column mapping for longitudinal PIT feature engineering."""
    entity_col: str = "project_code"
    period_col: str = "reporting_period"
    sector_col: str = "sector"
    ministry_col: str = "line_ministry"
    state_col: str = "state"
    agency_col: str = "agency"
    start_date_col: str = "start_date"
    original_cost_col: str = "original_cost_cr"
    revised_cost_col: str = "revised_cost_cr"
    original_end_date_col: str = "original_end_date"
    revised_end_date_col: str = "revised_end_date"
    expenditure_col: str = "expenditure_cr"
    physical_progress_col: str = "physical_progress_pct"

    # Common aliases for automatic column discovery
    ENTITY_CANDIDATES: Tuple[str, ...] = (
        "project_code", "canonical_project_key", "project_id", "source_project_id", "id"
    )
    PERIOD_CANDIDATES: Tuple[str, ...] = (
        "reporting_period", "snapshot_date", "prediction_cutoff_date", "period", "date"
    )
    ORIG_COST_CANDIDATES: Tuple[str, ...] = (
        "original_cost_cr", "original_cost", "feat_original_cost_crore", "cost_original", "orig_cost"
    )
    REV_COST_CANDIDATES: Tuple[str, ...] = (
        "revised_cost_cr", "revised_cost", "revised_cost_crore", "cost_revised", "rev_cost"
    )
    ORIG_END_DATE_CANDIDATES: Tuple[str, ...] = (
        "original_end_date", "original_completion_date", "original_doc", "doc_original", "orig_doc"
    )
    REV_END_DATE_CANDIDATES: Tuple[str, ...] = (
        "revised_end_date", "revised_completion_date", "revised_doc", "doc_revised", "rev_doc"
    )
    EXP_CANDIDATES: Tuple[str, ...] = (
        "expenditure_cr", "expenditure", "feat_cumulative_expenditure_crore", "cumulative_expenditure", "expenditure_crore"
    )
    PROGRESS_CANDIDATES: Tuple[str, ...] = (
        "physical_progress_pct", "physical_progress", "feat_physical_progress_pct", "progress_pct"
    )
    START_DATE_CANDIDATES: Tuple[str, ...] = (
        "start_date", "approval_date", "date_of_approval", "commencement_date"
    )
    SECTOR_CANDIDATES: Tuple[str, ...] = ("sector", "sector_name", "feat_sector")
    MINISTRY_CANDIDATES: Tuple[str, ...] = ("line_ministry", "ministry", "feat_line_ministry")
    STATE_CANDIDATES: Tuple[str, ...] = ("state", "feat_state", "location")
    AGENCY_CANDIDATES: Tuple[str, ...] = ("agency", "feat_agency", "executing_agency")

    @classmethod
    def auto_detect(cls, df: pd.DataFrame, **overrides: str) -> PITColumnConfig:
        """Create column config with automatic detection, respecting explicit overrides."""
        cols = set(df.columns)

        def pick(candidate_name: str, candidates: Sequence[str], default_name: str) -> str:
            if candidate_name in overrides and overrides[candidate_name]:
                return overrides[candidate_name]
            for cand in candidates:
                if cand in cols:
                    return cand
            return default_name

        return cls(
            entity_col=pick("entity_col", cls.ENTITY_CANDIDATES, "project_code"),
            period_col=pick("period_col", cls.PERIOD_CANDIDATES, "reporting_period"),
            sector_col=pick("sector_col", cls.SECTOR_CANDIDATES, "sector"),
            ministry_col=pick("ministry_col", cls.MINISTRY_CANDIDATES, "line_ministry"),
            state_col=pick("state_col", cls.STATE_CANDIDATES, "state"),
            agency_col=pick("agency_col", cls.AGENCY_CANDIDATES, "agency"),
            start_date_col=pick("start_date_col", cls.START_DATE_CANDIDATES, "start_date"),
            original_cost_col=pick("original_cost_col", cls.ORIG_COST_CANDIDATES, "original_cost_cr"),
            revised_cost_col=pick("revised_cost_col", cls.REV_COST_CANDIDATES, "revised_cost_cr"),
            original_end_date_col=pick("original_end_date_col", cls.ORIG_END_DATE_CANDIDATES, "original_end_date"),
            revised_end_date_col=pick("revised_end_date_col", cls.REV_END_DATE_CANDIDATES, "revised_end_date"),
            expenditure_col=pick("expenditure_col", cls.EXP_CANDIDATES, "expenditure_cr"),
            physical_progress_col=pick("physical_progress_col", cls.PROGRESS_CANDIDATES, "physical_progress_pct"),
        )


# ==============================================================================
# 3. DATE AND PERIOD UTILITIES
# ==============================================================================

def normalize_period(val: Any) -> Optional[str]:
    """Standardize reporting period string to 'YYYY-MM' format."""
    if pd.isna(val):
        return None
    if isinstance(val, (datetime, date, pd.Timestamp)):
        return f"{val.year:04d}-{val.month:02d}"

    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("nan", "none", "na", "n.a.", "-", ""):
        return None

    if "-" in val_str:
        parts = val_str.split("-")
        if len(parts) >= 2:
            try:
                if len(parts[0]) == 4:
                    return f"{int(parts[0]):04d}-{int(parts[1]):02d}"
                elif len(parts[1]) == 4:
                    return f"{int(parts[1]):04d}-{int(parts[0]):02d}"
            except (ValueError, TypeError):
                pass

    if "/" in val_str:
        parts = val_str.split("/")
        if len(parts) >= 2:
            try:
                if len(parts[1]) == 4:
                    return f"{int(parts[1]):04d}-{int(parts[0]):02d}"
                elif len(parts[0]) == 4:
                    return f"{int(parts[0]):04d}-{int(parts[1]):02d}"
            except (ValueError, TypeError):
                pass

    try:
        dt = pd.to_datetime(val_str)
        return f"{dt.year:04d}-{dt.month:02d}"
    except Exception:
        return None


def subtract_one_month(period_str: str) -> str:
    """Return the immediately preceding calendar month 'YYYY-MM'."""
    parts = period_str.strip().split("-")
    year = int(parts[0])
    month = int(parts[1])
    if month == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month - 1:02d}"


def get_period_end_timestamp(period_str: str) -> pd.Timestamp:
    """Return pd.Timestamp corresponding to the last day of the reporting period."""
    parts = period_str.strip().split("-")
    year = int(parts[0])
    month = int(parts[1])
    last_day = calendar.monthrange(year, month)[1]
    return pd.Timestamp(year, month, last_day, 23, 59, 59)


def parse_date_value(val: Any) -> Optional[pd.Timestamp]:
    """Parse date values robustly to pd.Timestamp."""
    if pd.isna(val):
        return None
    if isinstance(val, (pd.Timestamp, datetime)):
        return pd.Timestamp(val)
    if isinstance(val, date):
        return pd.Timestamp(datetime.combine(val, datetime.min.time()))

    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("nan", "none", "na", "n.a.", "-", "(-)"):
        return None

    try:
        if "-" in val_str and len(val_str.split("-")) == 2:
            parts = val_str.split("-")
            if len(parts[0]) == 4:
                return pd.Timestamp(int(parts[0]), int(parts[1]), 1)
        if "/" in val_str and len(val_str.split("/")) == 2:
            parts = val_str.split("/")
            if len(parts[1]) == 4:
                return pd.Timestamp(int(parts[1]), int(parts[0]), 1)
            elif len(parts[0]) == 4:
                return pd.Timestamp(int(parts[0]), int(parts[1]), 1)
        return pd.to_datetime(val_str)
    except Exception:
        return None


# ==============================================================================
# 4. LONGITUDINAL PIT FEATURE BUILDER CLASS
# ==============================================================================

class LongitudinalPITFeatureBuilder:
    """
    Constructs Point-in-Time features for longitudinal project monitoring panels.

    Adheres strictly to docs/pit_feature_specification.md:
    - Zero future leakage (Rule LR-01 through LR-07).
    - Features at cutoff t depend only on data observed at or before t.
    - Preserves unobservable lags/velocities as NaN with is_first_observation flag.
    - Computes all 12 authoritative derived and velocity features.
    - Supports Model A (CUF baseline) vs Model B (Enhanced PIT + velocity) partitioning.
    """

    # Feature definitions according to docs/pit_feature_specification.md Section 4
    MODEL_A_COLUMNS = [
        "sector",
        "line_ministry",
        "original_cost_cr",
        "original_end_date",
        "revised_cost_cr",
        "expenditure_cr",
        "expenditure_to_original_cost",
        "physical_progress_pct",
    ]

    MODEL_B_DERIVED_COLUMNS = [
        "cost_growth_ratio",
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
        "is_first_observation",
    ]

    def __init__(self, config: Optional[PITColumnConfig] = None):
        """Initialize builder with column configuration."""
        self.config = config

    def build_pit_features(
        self,
        df: pd.DataFrame,
        config: Optional[PITColumnConfig] = None,
    ) -> pd.DataFrame:
        """
        Build longitudinal PIT features across all project-reporting period observations.

        Args:
            df: Input panel DataFrame containing longitudinal observations.
            config: Optional column mapping; if omitted, self.config or auto-detected is used.

        Returns:
            pd.DataFrame: Augmented DataFrame containing all base, derived, and velocity features.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(df)}.")
        if df.empty:
            raise PITFeatureError("Input DataFrame is empty.")

        cfg = config or self.config or PITColumnConfig.auto_detect(df)

        if cfg.entity_col not in df.columns:
            raise PITFeatureError(f"Entity column '{cfg.entity_col}' not found.")
        if cfg.period_col not in df.columns:
            raise PITFeatureError(f"Period column '{cfg.period_col}' not found.")

        df_out = df.copy()

        # Standardize reporting periods
        norm_periods = df_out[cfg.period_col].apply(normalize_period)
        if norm_periods.isna().any():
            n_inv = int(norm_periods.isna().sum())
            raise PITFeatureError(f"Found {n_inv} unparseable reporting periods in '{cfg.period_col}'.")
        df_out["_norm_period"] = norm_periods

        # Check composite primary key uniqueness
        duplicates = df_out.duplicated(subset=[cfg.entity_col, "_norm_period"])
        if duplicates.any():
            n_dup = int(duplicates.sum())
            raise PITFeatureError(
                f"Found {n_dup} duplicate (project, period) rows on ['{cfg.entity_col}', '{cfg.period_col}']."
            )

        # Build fast lookup dictionary: (entity, period) -> row parsed values
        # Used strictly for looking up t-1 (never t+1)
        records_lookup: Dict[Tuple[Any, str], Dict[str, Any]] = {}
        for idx, row in df_out.iterrows():
            entity_val = row[cfg.entity_col]
            period_val = row["_norm_period"]

            orig_cost = pd.to_numeric(row.get(cfg.original_cost_col), errors="coerce")
            rev_cost = pd.to_numeric(row.get(cfg.revised_cost_col), errors="coerce")
            exp = pd.to_numeric(row.get(cfg.expenditure_col), errors="coerce")
            phys_prog = pd.to_numeric(row.get(cfg.physical_progress_col), errors="coerce")

            start_dt = parse_date_value(row.get(cfg.start_date_col))
            orig_end_dt = parse_date_value(row.get(cfg.original_end_date_col))
            rev_end_dt = parse_date_value(row.get(cfg.revised_end_date_col))

            records_lookup[(entity_val, period_val)] = {
                "orig_cost": orig_cost,
                "rev_cost": rev_cost,
                "exp": exp,
                "phys_prog": phys_prog,
                "start_dt": start_dt,
                "orig_end_dt": orig_end_dt,
                "rev_end_dt": rev_end_dt,
            }

        # Containers for derived features
        cost_growth_ratio_vals = []
        exp_to_orig_vals = []
        exp_to_rev_vals = []
        sched_slip_vals = []
        project_age_vals = []
        elapsed_dur_vals = []
        progress_gap_vals = []
        exp_prog_gap_vals = []

        recent_cost_vals = []
        recent_exp_vals = []
        recent_prog_vals = []
        recent_sched_vals = []
        is_first_obs_vals = []

        for idx, row in df_out.iterrows():
            entity_val = row[cfg.entity_col]
            period_t = row["_norm_period"]
            period_dt = get_period_end_timestamp(period_t)

            rec_t = records_lookup[(entity_val, period_t)]

            # Static & dynamic attributes at t
            orig_cost_t = rec_t["orig_cost"]
            rev_cost_t = rec_t["rev_cost"]
            exp_t = rec_t["exp"]
            phys_prog_t = rec_t["phys_prog"]
            start_dt_t = rec_t["start_dt"]
            orig_end_dt_t = rec_t["orig_end_dt"]
            rev_end_dt_t = rec_t["rev_end_dt"]

            # Effective revised values at t (default to baseline if unrevised)
            eff_rev_cost_t = rev_cost_t if (pd.notna(rev_cost_t) and rev_cost_t > 0) else orig_cost_t
            eff_rev_end_t = rev_end_dt_t if rev_end_dt_t is not None else orig_end_dt_t

            # -------------------------------------------------------------
            # Feature 1: cost_growth_ratio (Section 3.1)
            # max(revised_cost(t), original_cost) / original_cost
            # -------------------------------------------------------------
            if pd.notna(orig_cost_t) and orig_cost_t > 0:
                base_c = max(eff_rev_cost_t, orig_cost_t) if pd.notna(eff_rev_cost_t) else orig_cost_t
                c_growth = float(base_c / orig_cost_t)
            else:
                c_growth = np.nan
            cost_growth_ratio_vals.append(c_growth)

            # -------------------------------------------------------------
            # Feature 2: expenditure_to_original_cost (Raw CUF)
            # expenditure(t) / original_cost
            # -------------------------------------------------------------
            if pd.notna(exp_t) and pd.notna(orig_cost_t) and orig_cost_t > 0:
                raw_cuf = float(exp_t / orig_cost_t)
            else:
                raw_cuf = np.nan
            exp_to_orig_vals.append(raw_cuf)

            # -------------------------------------------------------------
            # Feature 3: expenditure_to_revised_cost (Adjusted CUF)
            # expenditure(t) / max(revised_cost(t), original_cost)
            # -------------------------------------------------------------
            active_budget = max(eff_rev_cost_t, orig_cost_t) if (pd.notna(eff_rev_cost_t) and pd.notna(orig_cost_t)) else (orig_cost_t if pd.notna(orig_cost_t) else np.nan)
            if pd.notna(exp_t) and pd.notna(active_budget) and active_budget > 0:
                adj_cuf = float(exp_t / active_budget)
            else:
                adj_cuf = np.nan
            exp_to_rev_vals.append(adj_cuf)

            # -------------------------------------------------------------
            # Feature 4: schedule_slippage_days (Section 3.2)
            # max(0, (revised_end_date(t) - original_end_date).days)
            # -------------------------------------------------------------
            if eff_rev_end_t is not None and orig_end_dt_t is not None:
                slip_days = max(0.0, float((eff_rev_end_t - orig_end_dt_t).days))
            else:
                slip_days = np.nan
            sched_slip_vals.append(slip_days)

            # -------------------------------------------------------------
            # Feature 5: project_age_days
            # (t - start_date).days
            # -------------------------------------------------------------
            if start_dt_t is not None:
                age_days = float((period_dt - start_dt_t).days)
            else:
                age_days = np.nan
            project_age_vals.append(age_days)

            # -------------------------------------------------------------
            # Feature 6: elapsed_duration_ratio
            # (t - start_date).days / max(1, (original_end_date - start_date).days)
            # -------------------------------------------------------------
            if start_dt_t is not None and orig_end_dt_t is not None:
                total_duration_days = max(1.0, float((orig_end_dt_t - start_dt_t).days))
                elapsed_days = float((period_dt - start_dt_t).days)
                dur_ratio = float(elapsed_days / total_duration_days)
            else:
                dur_ratio = np.nan
            elapsed_dur_vals.append(dur_ratio)

            # -------------------------------------------------------------
            # Feature 7: progress_gap (Section 3.3)
            # min(100, elapsed_duration_ratio * 100) - physical_progress_pct(t)
            # -------------------------------------------------------------
            if pd.notna(dur_ratio) and pd.notna(phys_prog_t):
                expected_prog = min(100.0, max(0.0, dur_ratio * 100.0))
                p_gap = float(expected_prog - phys_prog_t)
            else:
                p_gap = np.nan
            progress_gap_vals.append(p_gap)

            # -------------------------------------------------------------
            # Feature 8: expenditure_progress_gap (Burn Discrepancy)
            # (expenditure_to_revised_cost * 100) - physical_progress_pct(t)
            # -------------------------------------------------------------
            if pd.notna(adj_cuf) and pd.notna(phys_prog_t):
                e_p_gap = float((adj_cuf * 100.0) - phys_prog_t)
            else:
                e_p_gap = np.nan
            exp_prog_gap_vals.append(e_p_gap)

            # -------------------------------------------------------------
            # Velocity Features 9-12 (Section 3.4 - Requires authentic t-1)
            # -------------------------------------------------------------
            period_prev = subtract_one_month(period_t)
            rec_prev = records_lookup.get((entity_val, period_prev))

            if rec_prev is not None:
                is_first_obs = 0

                # Feature 9: recent_cost_change = revised_cost(t) - revised_cost(t-1)
                rev_c_prev = rec_prev["rev_cost"] if pd.notna(rec_prev["rev_cost"]) else rec_prev["orig_cost"]
                if pd.notna(eff_rev_cost_t) and pd.notna(rev_c_prev):
                    d_cost = float(eff_rev_cost_t - rev_c_prev)
                else:
                    d_cost = np.nan

                # Feature 10: recent_expenditure_change = expenditure(t) - expenditure(t-1)
                exp_prev = rec_prev["exp"]
                if pd.notna(exp_t) and pd.notna(exp_prev):
                    d_exp = float(exp_t - exp_prev)
                else:
                    d_exp = np.nan

                # Feature 11: recent_progress_change = progress(t) - progress(t-1)
                prog_prev = rec_prev["phys_prog"]
                if pd.notna(phys_prog_t) and pd.notna(prog_prev):
                    d_prog = float(phys_prog_t - prog_prev)
                else:
                    d_prog = np.nan

                # Feature 12: recent_schedule_change = (revised_end(t) - revised_end(t-1)).days
                rev_end_prev = rec_prev["rev_end_dt"] if rec_prev["rev_end_dt"] is not None else rec_prev["orig_end_dt"]
                if eff_rev_end_t is not None and rev_end_prev is not None:
                    d_sched = float((eff_rev_end_t - rev_end_prev).days)
                else:
                    d_sched = np.nan
            else:
                # No authentic t-1 observation exists -> strictly preserve NaN
                is_first_obs = 1
                d_cost = np.nan
                d_exp = np.nan
                d_prog = np.nan
                d_sched = np.nan

            is_first_obs_vals.append(is_first_obs)
            recent_cost_vals.append(d_cost)
            recent_exp_vals.append(d_exp)
            recent_prog_vals.append(d_prog)
            recent_sched_vals.append(d_sched)

        # Assign derived features to DataFrame
        df_out["cost_growth_ratio"] = cost_growth_ratio_vals
        df_out["expenditure_to_original_cost"] = exp_to_orig_vals
        df_out["expenditure_to_revised_cost"] = exp_to_rev_vals
        df_out["schedule_slippage_days"] = sched_slip_vals
        df_out["project_age_days"] = project_age_vals
        df_out["elapsed_duration_ratio"] = elapsed_dur_vals
        df_out["progress_gap"] = progress_gap_vals
        df_out["expenditure_progress_gap"] = exp_prog_gap_vals

        df_out["recent_cost_change"] = recent_cost_vals
        df_out["recent_expenditure_change"] = recent_exp_vals
        df_out["recent_progress_change"] = recent_prog_vals
        df_out["recent_schedule_change"] = recent_sched_vals
        df_out["is_first_observation"] = is_first_obs_vals

        df_out = df_out.drop(columns=["_norm_period"])
        return df_out

    def extract_model_a_features(
        self,
        df: pd.DataFrame,
        config: Optional[PITColumnConfig] = None,
    ) -> pd.DataFrame:
        """
        Extract Model A (Official CUF Baseline) feature matrix.

        Returns DataFrame containing:
        - sector
        - line_ministry
        - original_cost_cr
        - original_end_date
        - revised_cost_cr
        - expenditure_cr
        - expenditure_to_original_cost (Raw CUF)
        - physical_progress_pct
        """
        cfg = config or self.config or PITColumnConfig.auto_detect(df)

        # Ensure expenditure_to_original_cost is computed if missing
        if "expenditure_to_original_cost" not in df.columns:
            df = self.build_pit_features(df, config=cfg)

        model_a_cols = [
            cfg.sector_col,
            cfg.ministry_col,
            cfg.original_cost_col,
            cfg.original_end_date_col,
            cfg.revised_cost_col,
            cfg.expenditure_col,
            "expenditure_to_original_cost",
            cfg.physical_progress_col,
        ]
        available_cols = [c for c in model_a_cols if c in df.columns]
        return df[available_cols].copy()

    def extract_model_b_features(
        self,
        df: pd.DataFrame,
        config: Optional[PITColumnConfig] = None,
    ) -> pd.DataFrame:
        """
        Extract Model B (Enhanced PIT + Velocity) feature matrix.

        Includes all Model A features PLUS:
        - cost_growth_ratio
        - expenditure_to_revised_cost
        - schedule_slippage_days
        - project_age_days
        - elapsed_duration_ratio
        - progress_gap
        - expenditure_progress_gap
        - recent_cost_change
        - recent_expenditure_change
        - recent_progress_change
        - recent_schedule_change
        - is_first_observation
        """
        cfg = config or self.config or PITColumnConfig.auto_detect(df)

        # If derived columns are not yet present, compute them
        if "cost_growth_ratio" not in df.columns:
            df = self.build_pit_features(df, config=cfg)

        model_a_df = self.extract_model_a_features(df, config=cfg)
        model_b_cols = list(model_a_df.columns) + [
            c for c in self.MODEL_B_DERIVED_COLUMNS if c in df.columns
        ]
        return df[model_b_cols].copy()


# ==============================================================================
# 5. CONVENIENCE FUNCTION
# ==============================================================================

def build_longitudinal_pit_features(
    df: pd.DataFrame,
    config: Optional[PITColumnConfig] = None,
) -> pd.DataFrame:
    """Convenience functional interface to build longitudinal PIT features."""
    builder = LongitudinalPITFeatureBuilder(config=config)
    return builder.build_pit_features(df, config=config)


# ==============================================================================
# 6. CLI COMMAND-LINE INTERFACE
# ==============================================================================

def main() -> None:
    """CLI runner for calculating longitudinal PIT features on an input panel CSV."""
    parser = argparse.ArgumentParser(
        description="PAIMANA Longitudinal Point-in-Time (PIT) Feature Builder"
    )
    parser.add_argument("input_csv", type=str, help="Path to input panel CSV file")
    parser.add_argument("--output-csv", type=str, default=None, help="Path to save augmented CSV file")
    args = parser.parse_args()

    import os
    if not os.path.exists(args.input_csv):
        print(f"[ERROR] Input file not found: {args.input_csv}")
        sys.exit(1)

    df = pd.read_csv(args.input_csv)
    print(f"[INFO] Loaded {len(df)} rows from {args.input_csv}")

    builder = LongitudinalPITFeatureBuilder()
    df_out = builder.build_pit_features(df)

    print("=" * 65)
    print("PAIMANA LONGITUDINAL PIT FEATURE AUDIT")
    print("=" * 65)
    print(f"Total Rows:               {len(df_out)}")
    print(f"First Observations:       {int(df_out['is_first_observation'].sum())}")
    print(f"Velocity Observations:    {len(df_out) - int(df_out['is_first_observation'].sum())}")
    print(f"Non-null cost_growth:     {int(df_out['cost_growth_ratio'].notna().sum())}")
    print(f"Non-null slippage_days:   {int(df_out['schedule_slippage_days'].notna().sum())}")
    print(f"Non-null progress_gap:    {int(df_out['progress_gap'].notna().sum())}")
    print("=" * 65)

    if args.output_csv:
        out_p = Path(args.output_csv)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_p, index=False)
        print(f"[SUCCESS] Saved PIT features to: {out_p}")


if __name__ == "__main__":
    main()

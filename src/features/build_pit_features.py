"""
build_pit_features.py
---------------------
Constructs the Point-in-Time (PIT) feature and target dataset for the
prospective prediction horizon:
    Prediction Cutoff: July 31, 2025 (t)
    Forecast Horizon : July 31, 2026 (t + 12m)
    Learning Cohort  : 437 longitudinal projects tracked across both snapshots.

Input : data/processed/project_snapshot_panel.csv (FROZEN)
Output: data/interim/pit_features_july2025_to_july2026.csv

Strict Governance Invariants:
- All features X_t derived strictly from July 2025 data (<= 2025-07-31).
- July 2026 data used solely for target variables Y and eligibility flags.
- Zero temporal leakage, zero artificial imputation across cutoff.
- Missing target values are preserved as NaN and never coerced to zero.
"""

import sys
import hashlib
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np

EXPECTED_PANEL_SHA256 = "9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47"
DEFAULT_INPUT_PANEL = Path("data/processed/project_snapshot_panel.csv")
DEFAULT_OUTPUT_CSV = Path("data/interim/pit_features_july2025_to_july2026.csv")
SPEC_VERSION = "MODULE_2C_V1"
FIXED_GENERATED_AT = "2026-09-05T08:00:00Z"


def parse_ym(val: any) -> Optional[Tuple[int, int]]:
    """
    Parses year-month representation from string formats ('YYYY-MM', 'MM/YYYY', 'YYYY/MM', 'MM-YYYY').
    Returns (year, month) or None if unparseable/missing.
    """
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str or val_str in ("-", "NA", "N.A.", "(-)", "None", "nan"):
        return None

    # Hyphen separator
    if "-" in val_str:
        parts = val_str.split("-")
        if len(parts) == 2:
            try:
                if len(parts[0]) == 4:
                    return int(parts[0]), int(parts[1])
                elif len(parts[1]) == 4:
                    return int(parts[1]), int(parts[0])
            except (ValueError, TypeError):
                return None

    # Slash separator
    if "/" in val_str:
        parts = val_str.split("/")
        if len(parts) == 2:
            try:
                if len(parts[1]) == 4:
                    return int(parts[1]), int(parts[0])
                elif len(parts[0]) == 4:
                    return int(parts[0]), int(parts[1])
            except (ValueError, TypeError):
                return None

    return None


def verify_source_integrity(panel_path: Path) -> None:
    """Verifies that the frozen project snapshot panel exists and matches its immutable SHA-256 hash."""
    if not panel_path.exists():
        raise FileNotFoundError(f"Frozen input not found: {panel_path}")
    data = panel_path.read_bytes()
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != EXPECTED_PANEL_SHA256:
        raise ValueError(
            f"SOURCE INTEGRITY ERROR: Hash mismatch for {panel_path}.\n"
            f"Expected: {EXPECTED_PANEL_SHA256}\n"
            f"Actual  : {actual_hash}"
        )
    print(f"  [OK] Source panel verified: {panel_path.name} (SHA-256: {actual_hash})")


def build_pit_feature_dataset(
    panel_path: Path = DEFAULT_INPUT_PANEL,
    output_path: Path = DEFAULT_OUTPUT_CSV,
    generated_at: str = FIXED_GENERATED_AT,
) -> pd.DataFrame:
    """
    Builds the prospective PIT feature + target dataset from the frozen longitudinal panel.
    """
    print("\n===========================================================================")
    print("MODULE 2C: PHASE 2 — BUILD PIT FEATURE + TARGET DATASET")
    print("===========================================================================")

    # 1. Source verification
    verify_source_integrity(panel_path)

    # 2. Load panel
    panel = pd.read_csv(panel_path, dtype=str)
    print(f"  [OK] Loaded longitudinal panel: {len(panel):,} total observations")

    # 3. Partition snapshots
    df_2025 = panel[panel["source_snapshot"] == "2025-07"].copy()
    df_2026 = panel[panel["source_snapshot"] == "2026-07"].copy()
    df_2025_06 = panel[panel["source_snapshot"] == "2025-06"].copy()

    keys_2025 = set(df_2025["canonical_project_key"].dropna())
    keys_2026 = set(df_2026["canonical_project_key"].dropna())
    common_keys = sorted(list(keys_2025.intersection(keys_2026)))

    expected_cohort_size = 437
    if len(common_keys) != expected_cohort_size:
        raise ValueError(
            f"COHORT SIZE MISMATCH: Expected exactly {expected_cohort_size} projects, got {len(common_keys)}"
        )
    print(f"  [OK] Identified primary longitudinal cohort: exactly {len(common_keys)} physical projects")

    # Identify 3-snapshot vs 2-snapshot projects
    june_keys = set(df_2025_06["canonical_project_key"].dropna())

    # Set index for fast deterministic lookup
    sub_25 = df_2025[df_2025["canonical_project_key"].isin(common_keys)].set_index("canonical_project_key").loc[common_keys]
    sub_26 = df_2026[df_2026["canonical_project_key"].isin(common_keys)].set_index("canonical_project_key").loc[common_keys]

    rows = []

    for k in common_keys:
        r25 = sub_25.loc[k]
        r26 = sub_26.loc[k]

        # -------------------------------------------------------------
        # Keys & Cutoff Metadata
        # -------------------------------------------------------------
        source_proj_id = r25["source_project_id"]
        proj_name = r25["project_name"]
        snap_date = "2025-07"
        cutoff_date = "2025-07-31"

        # -------------------------------------------------------------
        # Baseline Features (X_t) from July 2025
        # -------------------------------------------------------------
        orig_cost_crore = float(r25["original_cost_crore"])
        cum_exp_crore = float(r25["cumulative_expenditure_crore"])
        phys_prog_pct = float(r25["physical_progress_pct"])

        log_orig_cost = float(np.log1p(orig_cost_crore))
        exp_ratio = float(cum_exp_crore / orig_cost_crore) if orig_cost_crore > 0 else np.nan
        divergence = float((exp_ratio * 100.0) - phys_prog_pct) if pd.notna(exp_ratio) else np.nan

        appr_ym = parse_ym(r25["approval_date"])
        if appr_ym is not None:
            age_months = float((2025 - appr_ym[0]) * 12 + (7 - appr_ym[1]))
            is_missing_appr = 0
        else:
            age_months = np.nan
            is_missing_appr = 1

        orig_end_ym = parse_ym(r25["original_completion_date"])
        if orig_end_ym is not None:
            rem_months = float((orig_end_ym[0] - 2025) * 12 + (orig_end_ym[1] - 7))
            is_past_orig = 1 if rem_months < 0 else 0
        else:
            rem_months = np.nan
            is_past_orig = np.nan

        state_val = str(r25["state"]).strip() if pd.notna(r25["state"]) else "MISSING"
        agency_val = str(r25["agency"]).strip() if pd.notna(r25["agency"]) else "UNKNOWN"

        # -------------------------------------------------------------
        # Cost Target (Y) from July 2026 Outcome
        # -------------------------------------------------------------
        raw_rev_cost_26 = r26["revised_cost_crore"]
        if pd.notna(raw_rev_cost_26) and str(raw_rev_cost_26).strip() != "" and orig_cost_crore > 0:
            try:
                rev_cost_26_val = float(raw_rev_cost_26)
                cost_esc = float((rev_cost_26_val - orig_cost_crore) / orig_cost_crore)
                cost_overrun_5 = 1 if cost_esc > 0.05 else 0
                is_elig_cost = 1
            except (ValueError, TypeError):
                cost_esc = np.nan
                cost_overrun_5 = np.nan
                is_elig_cost = 0
        else:
            cost_esc = np.nan
            cost_overrun_5 = np.nan
            is_elig_cost = 0

        # -------------------------------------------------------------
        # Schedule Target (Y) from July 2026 Outcome
        # -------------------------------------------------------------
        rev_end_26_ym = parse_ym(r26["revised_completion_date"])
        if rev_end_26_ym is not None and orig_end_ym is not None:
            slippage = float((rev_end_26_ym[0] - orig_end_ym[0]) * 12 + (rev_end_26_ym[1] - orig_end_ym[1]))
            time_overrun_3 = 1 if slippage >= 3.0 else 0
            is_elig_sched = 1
        else:
            slippage = np.nan
            time_overrun_3 = np.nan
            is_elig_sched = 0

        # -------------------------------------------------------------
        # Provenance Metadata
        # -------------------------------------------------------------
        traj_type = "3_SNAPSHOT" if k in june_keys else "2_SNAPSHOT_JULY"

        rows.append({
            "canonical_project_key": k,
            "source_project_id": source_proj_id,
            "project_name": proj_name,
            "snapshot_date": snap_date,
            "prediction_cutoff_date": cutoff_date,
            "feat_log_original_cost": log_orig_cost,
            "feat_original_cost_crore": orig_cost_crore,
            "feat_cumulative_expenditure_crore": cum_exp_crore,
            "feat_expenditure_to_original_cost_ratio": exp_ratio,
            "feat_physical_progress_pct": phys_prog_pct,
            "feat_physical_vs_financial_divergence": divergence,
            "feat_project_age_months": age_months,
            "feat_is_missing_approval_date": is_missing_appr,
            "feat_remaining_original_duration_months": rem_months,
            "feat_is_past_original_completion": is_past_orig,
            "feat_state": state_val,
            "feat_agency": agency_val,
            "future_total_cost_escalation_2026": cost_esc,
            "cost_overrun_5pct_2026": cost_overrun_5,
            "future_schedule_slippage_months_2026": slippage,
            "time_overrun_3m_2026": time_overrun_3,
            "is_eligible_cost_target": is_elig_cost,
            "is_eligible_schedule_target": is_elig_sched,
            "trajectory_type": traj_type,
            "spec_version": SPEC_VERSION,
            "generated_at": generated_at,
        })

    df_out = pd.DataFrame(rows)

    # 4. Schema verification
    expected_cols = [
        "canonical_project_key",
        "source_project_id",
        "project_name",
        "snapshot_date",
        "prediction_cutoff_date",
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
        "feat_agency",
        "future_total_cost_escalation_2026",
        "cost_overrun_5pct_2026",
        "future_schedule_slippage_months_2026",
        "time_overrun_3m_2026",
        "is_eligible_cost_target",
        "is_eligible_schedule_target",
        "trajectory_type",
        "spec_version",
        "generated_at",
    ]
    assert list(df_out.columns) == expected_cols, f"Schema mismatch: {df_out.columns.tolist()}"
    assert len(df_out) == 437, f"Row count mismatch: expected 437, got {len(df_out)}"
    assert df_out["canonical_project_key"].nunique() == 437, "Duplicate canonical_project_key found"

    # 5. Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(output_path, index=False, encoding="utf-8")

    data_out = output_path.read_bytes()
    out_hash = hashlib.sha256(data_out).hexdigest()

    print(f"\n[SUCCESS] PIT Feature Dataset successfully constructed:")
    print(f"  Output Path: {output_path}")
    print(f"  Total Rows : {len(df_out)}")
    print(f"  Columns    : {len(df_out.columns)}")
    print(f"  File Size  : {len(data_out):,} bytes")
    print(f"  SHA-256    : {out_hash}")

    # 6. Print summary metrics
    print("\n--- TARGET ACCOUNTING & ELIGIBILITY ---")
    n_total = len(df_out)

    # Cost
    n_elig_cost = int(df_out["is_eligible_cost_target"].sum())
    n_miss_cost = n_total - n_elig_cost
    n_pos_cost = int((df_out["cost_overrun_5pct_2026"] == 1).sum())
    n_neg_cost = int((df_out["cost_overrun_5pct_2026"] == 0).sum())
    rate_cost = (n_pos_cost / n_elig_cost * 100) if n_elig_cost > 0 else 0.0
    print(f"  Cost Overrun (>5%): Total={n_total}, Eligible={n_elig_cost}, Missing={n_miss_cost}, Positive={n_pos_cost}, Negative={n_neg_cost}, Event Rate={rate_cost:.2f}%")

    # Schedule
    n_elig_sched = int(df_out["is_eligible_schedule_target"].sum())
    n_miss_sched = n_total - n_elig_sched
    n_pos_sched = int((df_out["time_overrun_3m_2026"] == 1).sum())
    n_neg_sched = int((df_out["time_overrun_3m_2026"] == 0).sum())
    rate_sched = (n_pos_sched / n_elig_sched * 100) if n_elig_sched > 0 else 0.0
    print(f"  Schedule Slippage (>=3M): Total={n_total}, Eligible={n_elig_sched}, Missing={n_miss_sched}, Positive={n_pos_sched}, Negative={n_neg_sched}, Event Rate={rate_sched:.2f}%")

    print("\n--- TRAJECTORY BREAKDOWN ---")
    traj_counts = df_out["trajectory_type"].value_counts().to_dict()
    for t_type, cnt in traj_counts.items():
        print(f"  {t_type}: {cnt} projects")

    return df_out


if __name__ == "__main__":
    build_pit_feature_dataset()

"""
Module 4 — Project Risk Scoring Engine
SIH26103 PAIMANA Predictive Risk Intelligence

Generates dual-dimension risk probabilities (Cost & Schedule), compound exposure indicators,
portfolio attention scores, empirical attention tiers, and portfolio priority ranks across
the reference portfolio (N=437) using frozen Module 3 prototype Random Forest models.

Governing Rules:
- Upstream datasets and PIT dataset are immutable.
- Missing schedule predictions are never imputed as zero.
- Compound exposure is computed strictly when both dimensions are available.
- Attention tiers (Tier 1 to Tier 4) are derived from empirical reference quantiles (Q50, Q75, Q90).
- Identical attention scores receive identical tiers and consistent ranks.
"""

import os
import sys
import hashlib
import warnings
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

EXPECTED_PIT_SHA256 = "052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329"

EXPECTED_UPSTREAM_HASHES = {
    "data/interim/pit_features_july2025_to_july2026.csv": "052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329",
    "data/processed/table7_june_2025_projects.csv": "9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43",
    "data/processed/table4_july_2025_projects.csv": "ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3",
    "data/processed/table6_july_2026_projects.csv": "6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9",
    "data/processed/project_identity_map.csv": "16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb",
    "data/processed/project_snapshot_panel.csv": "9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47",
}

ENHANCED_NUMERIC_PREDICTORS = [
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
]

ENHANCED_CATEGORICAL_PREDICTORS = [
    "feat_state",
    "feat_agency",
]

PROHIBITED_FIELDS = [
    "future_total_cost_escalation_2026",
    "cost_overrun_5pct_2026",
    "future_schedule_slippage_months_2026",
    "time_overrun_3m_2026",
    "revised_cost_cr_2026",
    "revised_date_of_commissioning_2026",
    "future_cost",
    "future_completion",
    "future_expenditure",
    "future_progress",
    "sector",
    "feat_sector",
    "revised_cost_cr_2025",
    "delay_months_2025",
]


def verify_file_sha256(filepath: str, expected_sha256: str) -> bool:
    """Verifies that the target file matches the expected SHA-256 hash."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, "rb") as f:
        computed = hashlib.sha256(f.read()).hexdigest()
    if computed != expected_sha256:
        raise ValueError(
            f"SHA-256 mismatch for {filepath}:\n"
            f"  Computed: {computed}\n"
            f"  Expected: {expected_sha256}"
        )
    return True


def audit_predictor_leakage(predictors: list):
    """Asserts that no prohibited target, future-outcome, or unauthorized fields enter X."""
    for col in predictors:
        if col in PROHIBITED_FIELDS:
            raise ValueError(f"CRITICAL LEAKAGE DETECTED: Prohibited column '{col}' is in predictor set!")
        if "2026" in col:
            raise ValueError(f"CRITICAL LEAKAGE DETECTED: Future 2026 column '{col}' is in predictor set!")
        if "future" in col.lower():
            raise ValueError(f"CRITICAL LEAKAGE DETECTED: Future outcome column '{col}' is in predictor set!")


def build_preprocessor() -> ColumnTransformer:
    """Constructs the standard leakage-safe ColumnTransformer."""
    numeric_transformer = SimpleImputer(strategy="median")
    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, ENHANCED_NUMERIC_PREDICTORS),
            ("cat", categorical_transformer, ENHANCED_CATEGORICAL_PREDICTORS),
        ]
    )


def build_random_forest_classifier() -> RandomForestClassifier:
    """Returns the exact Random Forest classifier selected in Module 3."""
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        bootstrap=True,
        class_weight=None,
        random_state=42,
        n_jobs=1,
    )


def assign_attention_tier(score: float, q50: float, q75: float, q90: float) -> str:
    """Assigns portfolio attention priority tier based on empirical reference quantiles."""
    if score >= q90:
        return "Tier 1"
    elif score >= q75:
        return "Tier 2"
    elif score >= q50:
        return "Tier 3"
    else:
        return "Tier 4"


def generate_risk_scores(pit_path: str, output_path: str, partition_output_path: str = None) -> pd.DataFrame:
    """
    Executes the full risk scoring generation pipeline.
    """
    # 1. Verify PIT file integrity
    verify_file_sha256(pit_path, EXPECTED_PIT_SHA256)

    # 2. Verify upstream files integrity
    repo_root = os.path.abspath(os.path.join(os.path.dirname(pit_path), "..", ".."))
    for rel_path, expected_hash in EXPECTED_UPSTREAM_HASHES.items():
        full_p = os.path.join(repo_root, rel_path)
        verify_file_sha256(full_p, expected_hash)

    # 3. Load PIT data
    df = pd.read_csv(pit_path)
    if len(df) != 437:
        raise ValueError(f"Expected exactly 437 projects in PIT cohort, got {len(df)}")

    all_predictors = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
    audit_predictor_leakage(all_predictors)

    # 4. Train Cost Random Forest model deterministically (matching Module 3 Phase 7)
    y_cost = df["cost_overrun_5pct_2026"].to_numpy()
    train_idx_c, test_idx_c = train_test_split(
        df.index, test_size=0.20, random_state=42, stratify=y_cost
    )
    modelfit_idx_c, calib_idx_c = train_test_split(
        train_idx_c, test_size=0.25, random_state=42, stratify=y_cost[train_idx_c]
    )

    cost_part = pd.Series(index=df.index, dtype=str)
    cost_part.loc[modelfit_idx_c] = "MODELFIT"
    cost_part.loc[calib_idx_c] = "CALIBRATION_HOLDOUT"
    cost_part.loc[test_idx_c] = "TEST_HOLDOUT"

    X_fit_c = df.loc[modelfit_idx_c, all_predictors]
    y_fit_c = y_cost[modelfit_idx_c]

    pipe_cost = Pipeline([
        ("prep", build_preprocessor()),
        ("clf", build_random_forest_classifier())
    ])
    pipe_cost.fit(X_fit_c, y_fit_c)

    # Predict cost probabilities for the complete cost population (N=437)
    cost_probs = pipe_cost.predict_proba(df[all_predictors])[:, 1]

    # 5. Train Schedule Random Forest model deterministically (matching Module 3 Phase 7)
    eligible_mask = df["is_eligible_schedule_target"] == 1
    sched_df = df[eligible_mask].copy().reset_index(drop=True)
    y_sched = sched_df["time_overrun_3m_2026"].astype(int).to_numpy()

    train_idx_s, test_idx_s = train_test_split(
        sched_df.index, test_size=0.20, random_state=42, stratify=y_sched
    )
    modelfit_idx_s, calib_idx_s = train_test_split(
        train_idx_s, test_size=0.25, random_state=42, stratify=y_sched[train_idx_s]
    )

    sched_part_eligible = pd.Series(index=sched_df.index, dtype=str)
    sched_part_eligible.loc[modelfit_idx_s] = "MODELFIT"
    sched_part_eligible.loc[calib_idx_s] = "CALIBRATION_HOLDOUT"
    sched_part_eligible.loc[test_idx_s] = "TEST_HOLDOUT"

    sched_part = pd.Series("NOT_ELIGIBLE", index=df.index, dtype=str)
    sched_part.loc[eligible_mask] = sched_part_eligible.values

    X_fit_s = sched_df.loc[modelfit_idx_s, all_predictors]
    y_fit_s = y_sched[modelfit_idx_s]

    pipe_sched = Pipeline([
        ("prep", build_preprocessor()),
        ("clf", build_random_forest_classifier())
    ])
    pipe_sched.fit(X_fit_s, y_fit_s)

    # Predict schedule probabilities ONLY for schedule-eligible projects (N=305)
    sched_probs_eligible = pipe_sched.predict_proba(sched_df[all_predictors])[:, 1]

    # Map back to full dataset (N=437), ensuring 132 ineligible projects remain NaN
    sched_probs = np.full(len(df), np.nan, dtype=float)
    sched_probs[eligible_mask] = sched_probs_eligible

    # 6. Calculate risk scores and coverage
    risk_coverage = np.where(np.isnan(sched_probs), "PARTIAL", "FULL")
    attention_score = np.where(np.isnan(sched_probs), cost_probs, np.maximum(cost_probs, sched_probs))
    compound_exposure = np.where(np.isnan(sched_probs), np.nan, np.minimum(cost_probs, sched_probs))

    # 7. Derive empirical quantiles from the reference scoring portfolio (N=437)
    q50 = float(np.quantile(attention_score, 0.50))
    q75 = float(np.quantile(attention_score, 0.75))
    q90 = float(np.quantile(attention_score, 0.90))

    # 8. Assign attention tiers deterministically
    attention_tiers = [assign_attention_tier(score, q50, q75, q90) for score in attention_score]

    # 9. Build output DataFrame
    out_df = pd.DataFrame({
        "canonical_project_key": df["canonical_project_key"],
        "source_project_id": df["source_project_id"],
        "project_name": df["project_name"],
        "state": df["feat_state"],
        "agency": df["feat_agency"],
        "snapshot_date": df["snapshot_date"],
        "prediction_cutoff_date": df["prediction_cutoff_date"],
        "is_eligible_cost_target": df["is_eligible_cost_target"],
        "is_eligible_schedule_target": df["is_eligible_schedule_target"],
        "cost_risk_probability": cost_probs,
        "schedule_risk_probability": sched_probs,
        "risk_coverage": risk_coverage,
        "attention_score": attention_score,
        "compound_exposure": compound_exposure,
        "attention_tier": attention_tiers,
    })

    # 10. Assign portfolio rank based on descending attention_score
    # Using method='min' to consistently give tied scores identical ranks
    out_df["portfolio_rank"] = out_df["attention_score"].rank(ascending=False, method="min").astype(int)

    # Sort descending by attention_score, then canonical_project_key for deterministic presentation
    out_df = out_df.sort_values(by=["attention_score", "canonical_project_key"], ascending=[False, True]).reset_index(drop=True)

    # 11. Add provenance fields
    out_df["cost_model_name"] = "RandomForestClassifier(n_estimators=300, random_state=42)"
    out_df["schedule_model_name"] = "RandomForestClassifier(n_estimators=300, random_state=42)"
    out_df["cost_probability_variant"] = "Raw / Uncalibrated"
    out_df["schedule_probability_variant"] = "Raw / Uncalibrated"
    out_df["scoring_method_version"] = "1.0.0"

    # 12. Save to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_df.to_csv(output_path, index=False)
    print(f"Saved project risk scores to: {output_path} ({len(out_df)} projects)")

    # 13. Save partition sidecar to CSV
    raw_partition_df = pd.DataFrame({
        "canonical_project_key": df["canonical_project_key"],
        "cost_prediction_partition": cost_part,
        "schedule_prediction_partition": sched_part,
    })
    partition_df = out_df[["canonical_project_key"]].merge(raw_partition_df, on="canonical_project_key", how="left")

    if partition_output_path is None:
        if os.path.basename(output_path) == "project_risk_scores.csv":
            partition_output_path = os.path.join(os.path.dirname(output_path), "project_risk_score_partitions.csv")
        else:
            base, ext = os.path.splitext(output_path)
            partition_output_path = f"{base}_partitions{ext}"
    os.makedirs(os.path.dirname(partition_output_path), exist_ok=True)
    partition_df.to_csv(partition_output_path, index=False)
    print(f"Saved project risk score partitions to: {partition_output_path} ({len(partition_df)} projects)")

    return out_df


if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    pit_path = os.path.join(repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
    out_path = os.path.join(repo_root, "data", "processed", "project_risk_scores.csv")
    generate_risk_scores(pit_path, out_path)

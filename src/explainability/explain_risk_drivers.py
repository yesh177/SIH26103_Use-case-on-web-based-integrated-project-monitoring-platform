"""
Module 4 — Phase 6: Explainable Risk Drivers Engine
SIH26103 PAIMANA Predictive Risk Intelligence

Extracts global feature importances and local project-level risk drivers
for both Cost Overrun (>5%) and Schedule Slippage (>=3M) tasks using
frozen Random Forest candidate models and leakage-safe preprocessing.

Governing Principles:
- Models: Random Forest (Raw probabilities, n_estimators=300, random_state=42, n_jobs=1).
- Predictors: Authorized 12 PIT predictors only; SECTOR IS STRICTLY PROHIBITED.
- Local Explanation Method: Local Marginal Reference Perturbation (dependency-free, directional, bounded).
- Non-Causality: Statistical associations within historical evaluated data; NOT causal drivers.
- Source-Evidence Separation: Explicitly separates model signals from observable PIT project facts.
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
EXPECTED_SCORES_SHA256 = "6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d"

EXPECTED_UPSTREAM_HASHES = {
    "data/interim/pit_features_july2025_to_july2026.csv": "052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329",
    "data/processed/table7_june_2025_projects.csv": "9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43",
    "data/processed/table4_july_2025_projects.csv": "ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3",
    "data/processed/table6_july_2026_projects.csv": "6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9",
    "data/processed/project_identity_map.csv": "16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb",
    "data/processed/project_snapshot_panel.csv": "9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47",
    "data/processed/project_risk_scores.csv": "6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d",
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

AUTHORIZED_PREDICTORS = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS

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
    "cat_sector",
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
        if "sector" in col.lower():
            raise ValueError(f"CRITICAL PROHIBITION: Sector feature '{col}' is prohibited!")


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


def extract_aggregated_global_importance(pipe: Pipeline) -> dict:
    """Extracts raw MDI importances and aggregates OHE dummies back to parent features."""
    prep = pipe.named_steps["prep"]
    clf = pipe.named_steps["clf"]
    names = list(prep.get_feature_names_out())
    imps = list(clf.feature_importances_)

    parent_imps = {feat: 0.0 for feat in AUTHORIZED_PREDICTORS}
    for n, imp in zip(names, imps):
        if n.startswith("num__"):
            p = n.replace("num__", "")
        elif n.startswith("cat__feat_state_"):
            p = "feat_state"
        elif n.startswith("cat__feat_agency_"):
            p = "feat_agency"
        else:
            p = n
        if p in parent_imps:
            parent_imps[p] += float(imp)
        else:
            raise ValueError(f"Encountered unexpected feature during aggregation: {p}")

    # Return sorted dictionary
    return dict(sorted(parent_imps.items(), key=lambda x: x[1], reverse=True))


def format_source_fact(feature_name: str, val) -> str:
    """Generates an objective, non-fabricated text description of the observed PIT fact."""
    if pd.isna(val):
        return f"{feature_name} value is unobserved or missing in PIT record."
    if feature_name == "feat_is_past_original_completion":
        return "Original completion date had passed as of July 2025 cutoff." if val == 1 else "Project was within original completion schedule as of July 2025 cutoff."
    elif feature_name == "feat_is_missing_approval_date":
        return "Official government approval date is missing in MoSPI report." if val == 1 else "Official government approval date is recorded in MoSPI report."
    elif feature_name == "feat_physical_vs_financial_divergence":
        return f"Financial expenditure ratio diverges from physical progress by {float(val):+.1f}% points."
    elif feature_name == "feat_physical_progress_pct":
        return f"Reported cumulative physical progress was {float(val):.1f}% as of July 2025."
    elif feature_name == "feat_expenditure_to_original_cost_ratio":
        return f"Cumulative expenditure reached {float(val)*100:.1f}% of original sanctioned budget."
    elif feature_name == "feat_project_age_months":
        return f"Project age was {float(val):.0f} months since approval as of July 2025."
    elif feature_name == "feat_remaining_original_duration_months":
        return f"Remaining original duration was {float(val):.0f} months as of July 2025."
    elif feature_name == "feat_cumulative_expenditure_crore":
        return f"Cumulative financial expenditure was ₹{float(val):.2f} crore as of July 2025."
    elif feature_name == "feat_original_cost_crore":
        return f"Original sanctioned project cost was ₹{float(val):.2f} crore."
    elif feature_name == "feat_log_original_cost":
        return f"Log-transformed original cost scale index was {float(val):.2f}."
    elif feature_name == "feat_state":
        return f"Primary executing state/UT is {str(val)}."
    elif feature_name == "feat_agency":
        return f"Executing agency/enterprise is {str(val)}."
    return f"{feature_name} = {val}"


def generate_explanations(pit_path: str, scores_path: str, output_path: str):
    """
    Computes global feature importances and local marginal perturbation explanations
    for all projects across Cost and Schedule tasks.
    """
    # 1. Verify inputs
    verify_file_sha256(pit_path, EXPECTED_PIT_SHA256)
    verify_file_sha256(scores_path, EXPECTED_SCORES_SHA256)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(pit_path), "..", ".."))
    for rel_path, exp_hash in EXPECTED_UPSTREAM_HASHES.items():
        verify_file_sha256(os.path.join(repo_root, rel_path), exp_hash)

    pit_df = pd.read_csv(pit_path)
    scores_df = pd.read_csv(scores_path)

    audit_predictor_leakage(AUTHORIZED_PREDICTORS)

    # 2. Re-fit models deterministically on exact training splits
    # Cost model
    y_cost = pit_df["cost_overrun_5pct_2026"].to_numpy()
    tr_c, _ = train_test_split(pit_df.index, test_size=0.20, random_state=42, stratify=y_cost)
    fit_c, _ = train_test_split(tr_c, test_size=0.25, random_state=42, stratify=y_cost[tr_c])

    pipe_cost = Pipeline([("prep", build_preprocessor()), ("clf", build_random_forest_classifier())])
    pipe_cost.fit(pit_df.loc[fit_c, AUTHORIZED_PREDICTORS], y_cost[fit_c])

    # Schedule model
    eligible_mask = pit_df["is_eligible_schedule_target"] == 1
    sched_df = pit_df[eligible_mask].copy().reset_index(drop=True)
    y_sched = sched_df["time_overrun_3m_2026"].astype(int).to_numpy()

    tr_s, _ = train_test_split(sched_df.index, test_size=0.20, random_state=42, stratify=y_sched)
    fit_s, _ = train_test_split(tr_s, test_size=0.25, random_state=42, stratify=y_sched[tr_s])

    pipe_sched = Pipeline([("prep", build_preprocessor()), ("clf", build_random_forest_classifier())])
    pipe_sched.fit(sched_df.loc[fit_s, AUTHORIZED_PREDICTORS], y_sched[fit_s])

    # 3. Global feature importances
    global_cost_imp = extract_aggregated_global_importance(pipe_cost)
    global_sched_imp = extract_aggregated_global_importance(pipe_sched)

    # 4. Compute reference portfolio baselines (median for numeric, mode for categorical)
    baselines = {}
    for col in ENHANCED_NUMERIC_PREDICTORS:
        baselines[col] = float(pit_df[col].median())
    for col in ENHANCED_CATEGORICAL_PREDICTORS:
        baselines[col] = str(pit_df[col].mode()[0])

    # 5. Local explanations via vectorized marginal perturbation
    # A. Cost Task (all 437 projects)
    base_cost_probs = pipe_cost.predict_proba(pit_df[AUTHORIZED_PREDICTORS])[:, 1]
    # Verify probability match with scores_df
    scores_dict = scores_df.set_index("canonical_project_key").to_dict(orient="index")
    for idx, key in enumerate(pit_df["canonical_project_key"]):
        expected_p = scores_dict[key]["cost_risk_probability"]
        if abs(base_cost_probs[idx] - expected_p) > 1e-6:
            raise ValueError(f"Cost probability mismatch for {key}: {base_cost_probs[idx]} vs {expected_p}")

    cost_pert_deltas = {}
    for col in AUTHORIZED_PREDICTORS:
        pert_df = pit_df[AUTHORIZED_PREDICTORS].copy()
        pert_df[col] = baselines[col]
        pert_probs = pipe_cost.predict_proba(pert_df)[:, 1]
        cost_pert_deltas[col] = base_cost_probs - pert_probs

    # B. Schedule Task (305 eligible projects)
    base_sched_probs_eligible = pipe_sched.predict_proba(sched_df[AUTHORIZED_PREDICTORS])[:, 1]
    sched_pert_deltas = {}
    for col in AUTHORIZED_PREDICTORS:
        pert_df = sched_df[AUTHORIZED_PREDICTORS].copy()
        pert_df[col] = baselines[col]
        pert_probs = pipe_sched.predict_proba(pert_df)[:, 1]
        sched_pert_deltas[col] = base_sched_probs_eligible - pert_probs

    # Map schedule deltas back to full 437 cohort (NaN for ineligible)
    sched_pert_deltas_full = {}
    for col in AUTHORIZED_PREDICTORS:
        arr = np.full(len(pit_df), np.nan, dtype=float)
        arr[eligible_mask] = sched_pert_deltas[col]
        sched_pert_deltas_full[col] = arr

    # 6. Build explanations DataFrame (tidy format: project x task)
    records = []

    # First pass: Cost Task records (437 rows)
    for i in range(len(pit_df)):
        key = pit_df.loc[i, "canonical_project_key"]
        p_info = scores_dict[key]

        # Extract feature deltas for this project
        deltas = [(col, cost_pert_deltas[col][i]) for col in AUTHORIZED_PREDICTORS]
        # Sort by absolute impact descending
        deltas_sorted = sorted(deltas, key=lambda x: abs(x[1]), reverse=True)

        top1_f, top1_imp = deltas_sorted[0]
        top2_f, top2_imp = deltas_sorted[1]
        top3_f, top3_imp = deltas_sorted[2]

        top1_val = pit_df.loc[i, top1_f]
        top2_val = pit_df.loc[i, top2_f]
        top3_val = pit_df.loc[i, top3_f]

        def get_dir(imp):
            if imp > 1e-4:
                return "ELEVATES_RISK"
            elif imp < -1e-4:
                return "ATTENUATES_RISK"
            return "NEUTRAL"

        records.append({
            "canonical_project_key": key,
            "source_project_id": pit_df.loc[i, "source_project_id"],
            "project_name": pit_df.loc[i, "project_name"],
            "state": pit_df.loc[i, "feat_state"],
            "agency": pit_df.loc[i, "feat_agency"],
            "task": "cost_overrun",
            "is_eligible_task_target": 1,
            "predicted_risk_probability": base_cost_probs[i],
            "attention_score": p_info["attention_score"],
            "attention_tier": p_info["attention_tier"],
            "portfolio_rank": p_info["portfolio_rank"],
            "risk_coverage": p_info["risk_coverage"],
            "top_1_feature": top1_f,
            "top_1_feature_value": str(top1_val),
            "top_1_impact": float(top1_imp),
            "top_1_direction": get_dir(top1_imp),
            "top_1_source_fact": format_source_fact(top1_f, top1_val),
            "top_2_feature": top2_f,
            "top_2_feature_value": str(top2_val),
            "top_2_impact": float(top2_imp),
            "top_2_direction": get_dir(top2_imp),
            "top_2_source_fact": format_source_fact(top2_f, top2_val),
            "top_3_feature": top3_f,
            "top_3_feature_value": str(top3_val),
            "top_3_impact": float(top3_imp),
            "top_3_direction": get_dir(top3_imp),
            "top_3_source_fact": format_source_fact(top3_f, top3_val),
            "explanation_method": "Local Marginal Reference Perturbation",
            "explanation_disclaimer": "Statistical association in evaluated data; not a causal driver.",
        })

    # Second pass: Schedule Task records (437 rows: 305 eligible + 132 ineligible)
    for i in range(len(pit_df)):
        key = pit_df.loc[i, "canonical_project_key"]
        p_info = scores_dict[key]
        is_eligible = int(pit_df.loc[i, "is_eligible_schedule_target"])

        if is_eligible == 1:
            # Extract feature deltas for schedule
            deltas = [(col, sched_pert_deltas_full[col][i]) for col in AUTHORIZED_PREDICTORS]
            deltas_sorted = sorted(deltas, key=lambda x: abs(x[1]), reverse=True)

            top1_f, top1_imp = deltas_sorted[0]
            top2_f, top2_imp = deltas_sorted[1]
            top3_f, top3_imp = deltas_sorted[2]

            top1_val = pit_df.loc[i, top1_f]
            top2_val = pit_df.loc[i, top2_f]
            top3_val = pit_df.loc[i, top3_f]

            pred_p = p_info["schedule_risk_probability"]

            records.append({
                "canonical_project_key": key,
                "source_project_id": pit_df.loc[i, "source_project_id"],
                "project_name": pit_df.loc[i, "project_name"],
                "state": pit_df.loc[i, "feat_state"],
                "agency": pit_df.loc[i, "feat_agency"],
                "task": "schedule_slippage",
                "is_eligible_task_target": 1,
                "predicted_risk_probability": pred_p,
                "attention_score": p_info["attention_score"],
                "attention_tier": p_info["attention_tier"],
                "portfolio_rank": p_info["portfolio_rank"],
                "risk_coverage": p_info["risk_coverage"],
                "top_1_feature": top1_f,
                "top_1_feature_value": str(top1_val),
                "top_1_impact": float(top1_imp),
                "top_1_direction": get_dir(top1_imp),
                "top_1_source_fact": format_source_fact(top1_f, top1_val),
                "top_2_feature": top2_f,
                "top_2_feature_value": str(top2_val),
                "top_2_impact": float(top2_imp),
                "top_2_direction": get_dir(top2_imp),
                "top_2_source_fact": format_source_fact(top2_f, top2_val),
                "top_3_feature": top3_f,
                "top_3_feature_value": str(top3_val),
                "top_3_impact": float(top3_imp),
                "top_3_direction": get_dir(top3_imp),
                "top_3_source_fact": format_source_fact(top3_f, top3_val),
                "explanation_method": "Local Marginal Reference Perturbation",
                "explanation_disclaimer": "Statistical association in evaluated data; not a causal driver.",
            })
        else:
            # Ineligible schedule outcome (missing in source)
            records.append({
                "canonical_project_key": key,
                "source_project_id": pit_df.loc[i, "source_project_id"],
                "project_name": pit_df.loc[i, "project_name"],
                "state": pit_df.loc[i, "feat_state"],
                "agency": pit_df.loc[i, "feat_agency"],
                "task": "schedule_slippage",
                "is_eligible_task_target": 0,
                "predicted_risk_probability": np.nan,
                "attention_score": p_info["attention_score"],
                "attention_tier": p_info["attention_tier"],
                "portfolio_rank": p_info["portfolio_rank"],
                "risk_coverage": p_info["risk_coverage"],
                "top_1_feature": np.nan,
                "top_1_feature_value": np.nan,
                "top_1_impact": np.nan,
                "top_1_direction": np.nan,
                "top_1_source_fact": "Schedule outcome unobserved / unrevised in source MoSPI reports; schedule monitoring inactive.",
                "top_2_feature": np.nan,
                "top_2_feature_value": np.nan,
                "top_2_impact": np.nan,
                "top_2_direction": np.nan,
                "top_2_source_fact": np.nan,
                "top_3_feature": np.nan,
                "top_3_feature_value": np.nan,
                "top_3_impact": np.nan,
                "top_3_direction": np.nan,
                "top_3_source_fact": np.nan,
                "explanation_method": "Local Marginal Reference Perturbation",
                "explanation_disclaimer": "Statistical association in evaluated data; not a causal driver.",
            })

    out_df = pd.DataFrame(records)

    # Sort deterministically
    out_df = out_df.sort_values(by=["task", "portfolio_rank", "canonical_project_key"], ascending=[True, True, True]).reset_index(drop=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_df.to_csv(output_path, index=False)
    print(f"Saved explanations to {output_path} ({len(out_df)} records)")

    return out_df, global_cost_imp, global_sched_imp


if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    pit_p = os.path.join(repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
    scores_p = os.path.join(repo_root, "data", "processed", "project_risk_scores.csv")
    out_p = os.path.join(repo_root, "data", "interim", "project_risk_explanations.csv")

    generate_explanations(pit_p, scores_p, out_p)

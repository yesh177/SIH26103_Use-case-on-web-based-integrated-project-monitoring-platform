"""
Module 4 — Phase 7: Intervention Prioritisation Engine
SIH26103 PAIMANA Predictive Risk Intelligence

Generates deterministic, evidence-grounded monitoring and intervention priorities
from frozen risk scores, explainable drivers, and point-in-time facts.

Governing Principles:
- Conservative Decision Support: Produces operational review recommendations, NOT administrative penalties or sanctions.
- Evidence-Grounded: Every recommendation is explicitly traceable to model probabilities, explainable drivers, and observable PIT features.
- Non-Causal Formulation: Strictly avoids blaming agencies or states; frames signals as statistical model associations.
- Missing Schedule Integrity: The 132 PARTIAL projects preserve unobserved schedule status; never imputed or scored for schedule intervention.
- Separation of Concerns: Intervention priority categorizes operational focus without altering the frozen portfolio rank.
"""

import os
import sys
import hashlib
import numpy as np
import pandas as pd

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


def generate_interventions(pit_path: str, scores_path: str, explanations_path: str, output_path: str) -> pd.DataFrame:
    """
    Executes the deterministic intervention prioritisation engine.
    """
    # 1. Verify inputs
    verify_file_sha256(pit_path, EXPECTED_PIT_SHA256)
    verify_file_sha256(scores_path, EXPECTED_SCORES_SHA256)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(pit_path), "..", ".."))
    for rel_path, exp_hash in EXPECTED_UPSTREAM_HASHES.items():
        verify_file_sha256(os.path.join(repo_root, rel_path), exp_hash)

    pit_df = pd.read_csv(pit_path)
    scores_df = pd.read_csv(scores_path)
    exp_df = pd.read_csv(explanations_path)

    if len(scores_df) != 437:
        raise ValueError(f"Expected 437 projects in scores_df, got {len(scores_df)}")

    # Index lookups
    cost_exp_map = exp_df[exp_df["task"] == "cost_overrun"].set_index("canonical_project_key").to_dict(orient="index")
    sched_exp_map = exp_df[exp_df["task"] == "schedule_slippage"].set_index("canonical_project_key").to_dict(orient="index")
    pit_map = pit_df.set_index("canonical_project_key").to_dict(orient="index")

    priority_tier_map = {
        "Tier 1": "PRIORITY_1",
        "Tier 2": "PRIORITY_2",
        "Tier 3": "PRIORITY_3",
        "Tier 4": "PRIORITY_4",
    }

    records = []
    for _, r in scores_df.iterrows():
        key = r["canonical_project_key"]
        pc = float(r["cost_risk_probability"])
        ps = float(r["schedule_risk_probability"]) if pd.notna(r["schedule_risk_probability"]) else np.nan
        att = float(r["attention_score"])
        cov = str(r["risk_coverage"])
        tier = str(r["attention_tier"])
        rank = int(r["portfolio_rank"])

        pit_row = pit_map[key]
        past_comp = int(pit_row["feat_is_past_original_completion"])
        divergence = float(pit_row["feat_physical_vs_financial_divergence"])
        exp_ratio = float(pit_row["feat_expenditure_to_original_cost_ratio"])
        missing_appr = int(pit_row["feat_is_missing_approval_date"])

        c_exp = cost_exp_map.get(key, {})
        c_top_f = c_exp.get("top_1_feature", "feat_expenditure_to_original_cost_ratio")
        c_top_val = c_exp.get("top_1_feature_value", str(exp_ratio))
        c_top_dir = c_exp.get("top_1_direction", "NEUTRAL")

        s_exp = sched_exp_map.get(key, {}) if cov == "FULL" else {}
        s_top_f = s_exp.get("top_1_feature", "feat_is_past_original_completion")
        s_top_val = s_exp.get("top_1_feature_value", str(past_comp))
        s_top_dir = s_exp.get("top_1_direction", "NEUTRAL")

        # Data quality flag
        if cov == "PARTIAL" and missing_appr == 1:
            dq_flag = "SCHEDULE_OUTCOME_UNOBSERVED_AND_MISSING_APPROVAL_DATE"
        elif cov == "PARTIAL":
            dq_flag = "SCHEDULE_OUTCOME_UNOBSERVED"
        elif missing_appr == 1:
            dq_flag = "MISSING_APPROVAL_DATE"
        else:
            dq_flag = "COMPLETE_BASELINE_DATA"

        # Deterministic Intervention Action Routing
        if cov == "FULL" and pc >= 0.50 and ps >= 0.75:
            risk_focus = "JOINT_COST_SCHEDULE"
            primary_act = "JOINT_COST_SCHEDULE_REVIEW"
            if past_comp == 1:
                secondary_act = "COMPLETION_STATUS_REVIEW"
            elif abs(divergence) >= 20.0:
                secondary_act = "EXPENDITURE_PROGRESS_REVIEW"
            else:
                secondary_act = "PROGRESS_VERIFICATION"
            reason = "Both evaluated cost and schedule risk are elevated; coordinated cost and schedule review is recommended."
            ev_f = c_top_f
            ev_v = str(c_top_val)
            ev_d = c_top_dir
        elif pc >= 0.50:
            risk_focus = "COST_RISK"
            primary_act = "COST_REVIEW"
            if abs(divergence) >= 20.0 or exp_ratio >= 1.0:
                secondary_act = "EXPENDITURE_PROGRESS_REVIEW"
            elif cov == "PARTIAL":
                secondary_act = "DATA_QUALITY_REVIEW"
            else:
                secondary_act = "PROGRESS_VERIFICATION"
            if cov == "PARTIAL":
                reason = "Elevated cost risk is supported by budget expenditure signals; schedule outcome is unobserved, cost review is recommended."
            else:
                clean_name = c_top_f.replace("feat_", "").replace("_", " ")
                reason = f"Elevated cost risk is supported by {clean_name}; cost review is recommended."
            ev_f = c_top_f
            ev_v = str(c_top_val)
            ev_d = c_top_dir
        elif cov == "FULL" and ps >= 0.75:
            risk_focus = "SCHEDULE_RISK"
            if past_comp == 1:
                primary_act = "COMPLETION_STATUS_REVIEW"
                secondary_act = "SCHEDULE_REVIEW"
                reason = "Elevated schedule risk is supported by a past-original-completion signal; completion status review is recommended."
                ev_f = "feat_is_past_original_completion"
                ev_v = "1"
                ev_d = "ELEVATES_RISK"
            else:
                primary_act = "SCHEDULE_REVIEW"
                secondary_act = "PROGRESS_VERIFICATION"
                reason = "Elevated schedule risk is supported by remaining duration and agency timeline patterns; schedule review is recommended."
                ev_f = s_top_f
                ev_v = str(s_top_val)
                ev_d = s_top_dir
        else:
            # Lower risk / baseline / partial
            if cov == "PARTIAL":
                risk_focus = "UNOBSERVED_SCHEDULE"
                primary_act = "DATA_QUALITY_REVIEW"
                secondary_act = "PROGRESS_VERIFICATION"
                reason = "Schedule outcome is unobserved in the available PIT cohort; prioritisation is based on cost risk only."
                ev_f = "schedule_outcome"
                ev_v = "UNOBSERVED"
                ev_d = "NEUTRAL"
            elif abs(divergence) >= 25.0:
                risk_focus = "PROGRESS_FINANCIAL_DIVERGENCE"
                primary_act = "EXPENDITURE_PROGRESS_REVIEW"
                secondary_act = "PROGRESS_VERIFICATION"
                reason = f"Physical-financial divergence of {divergence:+.1f}% points indicates expenditure pace mismatch; expenditure progress review is recommended."
                ev_f = "feat_physical_vs_financial_divergence"
                ev_v = f"{divergence:+.1f}"
                ev_d = "ELEVATES_RISK" if divergence > 0 else "ATTENUATES_RISK"
            elif past_comp == 1:
                risk_focus = "COMPLETION_STATUS"
                primary_act = "COMPLETION_STATUS_REVIEW"
                secondary_act = "PROGRESS_VERIFICATION"
                reason = "Project had passed original completion date as of July 2025 cutoff; completion status verification is recommended."
                ev_f = "feat_is_past_original_completion"
                ev_v = "1"
                ev_d = "ELEVATES_RISK"
            else:
                risk_focus = "BASELINE_MONITORING"
                primary_act = "PROGRESS_VERIFICATION"
                secondary_act = "DATA_QUALITY_REVIEW"
                reason = "Evaluated risk probabilities remain within baseline parameters; standard periodic progress verification is recommended."
                ev_f = c_top_f
                ev_v = str(c_top_val)
                ev_d = c_top_dir

        int_prio = priority_tier_map[tier]
        gov_note = "Monitoring recommendation derived from historical statistical associations in MoSPI reports; not an autonomous administrative decision or causal estimate."

        records.append({
            "canonical_project_key": key,
            "cost_risk_probability": pc,
            "schedule_risk_probability": ps,
            "attention_score": att,
            "risk_coverage": cov,
            "portfolio_rank": rank,
            "intervention_priority": int_prio,
            "primary_action": primary_act,
            "secondary_action": secondary_act,
            "risk_focus": risk_focus,
            "priority_reason": reason,
            "evidence_feature": ev_f,
            "evidence_value": ev_v,
            "evidence_direction": ev_d,
            "data_quality_flag": dq_flag,
            "governance_note": gov_note,
        })

    out_df = pd.DataFrame(records)

    # Sort deterministically by portfolio_rank ascending, then canonical_project_key ascending
    out_df = out_df.sort_values(by=["portfolio_rank", "canonical_project_key"], ascending=[True, True]).reset_index(drop=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_df.to_csv(output_path, index=False)
    print(f"Saved intervention priorities to: {output_path} ({len(out_df)} records)")

    return out_df


if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    pit_p = os.path.join(repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
    scores_p = os.path.join(repo_root, "data", "processed", "project_risk_scores.csv")
    exp_p = os.path.join(repo_root, "data", "interim", "project_risk_explanations.csv")
    out_p = os.path.join(repo_root, "data", "processed", "project_intervention_priorities.csv")

    generate_interventions(pit_p, scores_p, exp_p, out_p)

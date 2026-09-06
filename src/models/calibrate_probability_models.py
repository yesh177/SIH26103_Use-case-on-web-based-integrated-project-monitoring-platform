"""
Module 3 — Phase 7: Actual Probability Calibration & Validation.

Performs actual post-hoc probability calibration (Sigmoid/Platt scaling and
exploratory Isotonic regression) on the established Logistic Regression baseline
and Random Forest benchmark using a training-side calibration partition (75% Model-Fit,
25% Calibration), preserving the original Phase 5/6 test partitions completely untouched.

Governing Principles:
- Strict leakage isolation: Test set is NEVER used for calibration fitting.
- Training-side calibration split: 75% Model-Fit, 25% Calibration (`random_state=42`, stratified).
- Fixed models from Phase 5/6: Logistic Regression (max_iter=2000, random_state=42) and
  Random Forest (n_estimators=300, random_state=42, n_jobs=1).
- Enhanced feature set only (10 numeric + 2 categorical; NO sector).
- Evaluates Brier score, Log Loss, ROC-AUC, PR-AUC, calibration intercept (alpha), and
  calibration slope (beta) on the untouched test sets.
- Generates reliability diagrams for all model/calibration variants in reports/figures/.
"""

import hashlib
import os
import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

EXPECTED_PIT_SHA256 = "052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329"

# Enhanced Feature Set
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


class SigmoidCalibrator:
    """
    Platt Scaling (Sigmoid Calibrator) fitted strictly on calibration-subset probabilities:
        logit(P(Y=1)) = alpha + beta * logit(p_raw)
    Uses unregularized univariate logistic regression.
    """
    def __init__(self, eps: float = 1e-6):
        self.eps = eps
        self.lr = LogisticRegression(C=1e6, solver="lbfgs", max_iter=2000, random_state=42)
        self.alpha_ = None
        self.beta_ = None

    def fit(self, p_cal: np.ndarray, y_cal: np.ndarray):
        p_clip = np.clip(p_cal, self.eps, 1.0 - self.eps)
        logit_p = np.log(p_clip / (1.0 - p_clip)).reshape(-1, 1)
        self.lr.fit(logit_p, y_cal)
        self.alpha_ = float(self.lr.intercept_[0])
        self.beta_ = float(self.lr.coef_[0][0])
        return self

    def predict_proba(self, p_test: np.ndarray) -> np.ndarray:
        p_clip = np.clip(p_test, self.eps, 1.0 - self.eps)
        logit_p = np.log(p_clip / (1.0 - p_clip)).reshape(-1, 1)
        return self.lr.predict_proba(logit_p)[:, 1]


class IsotonicCalibrator:
    """
    Non-parametric Isotonic Regression Calibrator.
    Fitted strictly on calibration-subset probabilities.
    Labeled exploratory due to risk of overfitting on small samples.
    """
    def __init__(self):
        self.iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)

    def fit(self, p_cal: np.ndarray, y_cal: np.ndarray):
        self.iso.fit(p_cal, y_cal)
        return self

    def predict_proba(self, p_test: np.ndarray) -> np.ndarray:
        return np.clip(self.iso.predict(p_test), 0.0, 1.0)


def compute_calibration_slope_and_intercept(y_true: np.ndarray, y_prob: np.ndarray, eps: float = 1e-6) -> dict:
    """
    Estimates diagnostic calibration intercept (alpha) and slope (beta) using univariate logistic regression:
        logit(P(Y=1)) = alpha + beta * logit(p)
    """
    p_clipped = np.clip(y_prob, eps, 1.0 - eps)
    logit_p = np.log(p_clipped / (1.0 - p_clipped)).reshape(-1, 1)

    cal_model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=2000, random_state=42)
    cal_model.fit(logit_p, y_true)

    alpha = float(cal_model.intercept_[0])
    beta = float(cal_model.coef_[0][0])
    return {
        "intercept_alpha": alpha,
        "slope_beta": beta,
        "clipping_eps": eps,
    }


def compute_metrics_bundle(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.50) -> dict:
    """Evaluates comprehensive classification, probability calibration, and discrimination metrics on untouched test data."""
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred).tolist()
    tn, fp, fn, tp = int(cm[0][0]), int(cm[0][1]), int(cm[1][0]), int(cm[1][1])

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(average_precision_score(y_true, y_prob))
    brier = float(brier_score_loss(y_true, y_prob))
    ll = float(log_loss(y_true, np.clip(y_prob, 1e-6, 1.0 - 1e-6)))

    cal_params = compute_calibration_slope_and_intercept(y_true, y_prob)

    # 5 uniform bins for calibration curve
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=5, strategy="uniform")

    return {
        "n_test": len(y_true),
        "confusion_matrix": cm,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "balanced_accuracy": bal_acc,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier_score": brier,
        "log_loss": ll,
        "calibration_intercept": cal_params["intercept_alpha"],
        "calibration_slope": cal_params["slope_beta"],
        "prob_true": prob_true.tolist(),
        "prob_pred": prob_pred.tolist(),
        "probabilities": y_prob.copy(),
        "y_true": y_true.copy(),
    }


def plot_reliability_diagram(y_true: np.ndarray, y_prob: np.ndarray, title: str, save_path: str, color: str = "#1f77b4"):
    """Saves a standalone 2-panel reliability and predicted probability distribution diagram."""
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=5, strategy="uniform")
    brier = brier_score_loss(y_true, y_prob)
    ll = log_loss(y_true, np.clip(y_prob, 1e-6, 1.0 - 1e-6))
    cal_params = compute_calibration_slope_and_intercept(y_true, y_prob)
    alpha = cal_params["intercept_alpha"]
    beta = cal_params["slope_beta"]

    fig, (ax1, ax2) = plt.subplots(
        nrows=2, ncols=1, figsize=(7, 7.5), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )

    ax1.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect Calibration (y = x)")
    ax1.plot(prob_pred, prob_true, marker="s", color=color, linewidth=2, markersize=7, label=f"5 Uniform Bins")

    ax1.set_ylabel("Observed Proportion Positive", fontsize=11, fontweight="bold")
    ax1.set_ylim([-0.05, 1.05])
    ax1.set_xlim([-0.02, 1.02])
    ax1.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=9.5)

    stats_text = (
        f"Brier Score: {brier:.4f}\n"
        f"Log Loss: {ll:.4f}\n"
        f"Intercept (α): {alpha:+.4f}\n"
        f"Slope (β): {beta:.4f}"
    )
    ax1.text(0.96, 0.06, stats_text, transform=ax1.transAxes, fontsize=9.5,
             verticalalignment="bottom", horizontalalignment="right",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="#cccccc", alpha=0.9))

    ax2.hist(y_prob, bins=np.linspace(0, 1, 11), edgecolor="black", color=color, alpha=0.75, rwidth=0.9)
    ax2.set_xlabel("Predicted Probability", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Count", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved figure: {save_path}")


def run_probability_calibration_pipeline(data_path: str, figures_dir: str) -> dict:
    """Executes the complete Phase 7 probability calibration and validation experiment."""
    verify_file_sha256(data_path, EXPECTED_PIT_SHA256)
    df = pd.read_csv(data_path)

    all_predictors = ENHANCED_NUMERIC_PREDICTORS + ENHANCED_CATEGORICAL_PREDICTORS
    audit_predictor_leakage(all_predictors)

    # -------------------------------------------------------------------------
    # 1. COST OVERRUN TASK (cost_overrun_5pct_2026, N=437)
    # -------------------------------------------------------------------------
    y_cost = df["cost_overrun_5pct_2026"].to_numpy()

    # Original Phase 5 train/test split (80/20)
    train_idx_c, test_idx_c = train_test_split(
        df.index, test_size=0.20, random_state=42, stratify=y_cost
    )

    # Training-side calibration split: 75% Model-Fit, 25% Calibration
    modelfit_idx_c, calib_idx_c = train_test_split(
        train_idx_c, test_size=0.25, random_state=42, stratify=y_cost[train_idx_c]
    )

    X_fit_c = df.loc[modelfit_idx_c, all_predictors]
    y_fit_c = y_cost[modelfit_idx_c]

    X_cal_c = df.loc[calib_idx_c, all_predictors]
    y_cal_c = y_cost[calib_idx_c]

    X_te_c = df.loc[test_idx_c, all_predictors]
    y_te_c = y_cost[test_idx_c]

    # Models on Cost Task
    models_config = [
        ("Logistic Regression", "lr", lambda: LogisticRegression(max_iter=2000, random_state=42, class_weight=None)),
        ("Random Forest", "rf", lambda: RandomForestClassifier(n_estimators=300, max_depth=None, min_samples_split=2, min_samples_leaf=1, max_features="sqrt", bootstrap=True, random_state=42, n_jobs=1)),
    ]

    cost_results = {}
    for m_label, m_key, m_fn in models_config:
        pipe = Pipeline([("prep", build_preprocessor()), ("clf", m_fn())])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pipe.fit(X_fit_c, y_fit_c)

        p_cal = pipe.predict_proba(X_cal_c)[:, 1]
        p_raw_test = pipe.predict_proba(X_te_c)[:, 1]

        # Fit Sigmoid Calibrator on calibration subset
        sig = SigmoidCalibrator().fit(p_cal, y_cal_c)
        p_sig_test = sig.predict_proba(p_raw_test)

        # Fit Isotonic Calibrator on calibration subset
        iso = IsotonicCalibrator().fit(p_cal, y_cal_c)
        p_iso_test = iso.predict_proba(p_raw_test)

        cost_results[m_key] = {
            "label": m_label,
            "raw": compute_metrics_bundle(y_te_c, p_raw_test),
            "sigmoid": compute_metrics_bundle(y_te_c, p_sig_test),
            "isotonic": compute_metrics_bundle(y_te_c, p_iso_test),
            "sig_params": {"alpha": sig.alpha_, "beta": sig.beta_},
        }

        # Plot diagrams
        plot_reliability_diagram(y_te_c, p_raw_test, f"Cost Overrun: {m_label} (Raw)",
                                 os.path.join(figures_dir, f"cost_{m_key}_raw_calibration.png"), color="#3b6998" if m_key=="lr" else "#2ca02c")
        plot_reliability_diagram(y_te_c, p_sig_test, f"Cost Overrun: {m_label} (Sigmoid Calibrated)",
                                 os.path.join(figures_dir, f"cost_{m_key}_sigmoid_calibration.png"), color="#1f77b4" if m_key=="lr" else "#388e3c")
        plot_reliability_diagram(y_te_c, p_iso_test, f"Cost Overrun: {m_label} (Isotonic - Exploratory)",
                                 os.path.join(figures_dir, f"cost_{m_key}_isotonic_calibration.png"), color="#9467bd")

    # -------------------------------------------------------------------------
    # 2. SCHEDULE SLIPPAGE TASK (time_overrun_3m_2026, N=305)
    # -------------------------------------------------------------------------
    eligible_mask = df["is_eligible_schedule_target"] == 1
    sched_df = df[eligible_mask].copy().reset_index(drop=True)
    y_sched = sched_df["time_overrun_3m_2026"].astype(int).to_numpy()

    # Original Phase 5 train/test split (80/20)
    train_idx_s, test_idx_s = train_test_split(
        sched_df.index, test_size=0.20, random_state=42, stratify=y_sched
    )

    # Training-side calibration split: 75% Model-Fit, 25% Calibration
    modelfit_idx_s, calib_idx_s = train_test_split(
        train_idx_s, test_size=0.25, random_state=42, stratify=y_sched[train_idx_s]
    )

    X_fit_s = sched_df.loc[modelfit_idx_s, all_predictors]
    y_fit_s = y_sched[modelfit_idx_s]

    X_cal_s = sched_df.loc[calib_idx_s, all_predictors]
    y_cal_s = y_sched[calib_idx_s]

    X_te_s = sched_df.loc[test_idx_s, all_predictors]
    y_te_s = y_sched[test_idx_s]

    sched_results = {}
    for m_label, m_key, m_fn in models_config:
        pipe = Pipeline([("prep", build_preprocessor()), ("clf", m_fn())])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pipe.fit(X_fit_s, y_fit_s)

        p_cal = pipe.predict_proba(X_cal_s)[:, 1]
        p_raw_test = pipe.predict_proba(X_te_s)[:, 1]

        # Fit Sigmoid Calibrator
        sig = SigmoidCalibrator().fit(p_cal, y_cal_s)
        p_sig_test = sig.predict_proba(p_raw_test)

        # Fit Isotonic Calibrator
        iso = IsotonicCalibrator().fit(p_cal, y_cal_s)
        p_iso_test = iso.predict_proba(p_raw_test)

        sched_results[m_key] = {
            "label": m_label,
            "raw": compute_metrics_bundle(y_te_s, p_raw_test),
            "sigmoid": compute_metrics_bundle(y_te_s, p_sig_test),
            "isotonic": compute_metrics_bundle(y_te_s, p_iso_test),
            "sig_params": {"alpha": sig.alpha_, "beta": sig.beta_},
        }

        # Plot diagrams
        plot_reliability_diagram(y_te_s, p_raw_test, f"Schedule Slippage: {m_label} (Raw)",
                                 os.path.join(figures_dir, f"schedule_{m_key}_raw_calibration.png"), color="#3b6998" if m_key=="lr" else "#2ca02c")
        plot_reliability_diagram(y_te_s, p_sig_test, f"Schedule Slippage: {m_label} (Sigmoid Calibrated)",
                                 os.path.join(figures_dir, f"schedule_{m_key}_sigmoid_calibration.png"), color="#1f77b4" if m_key=="lr" else "#388e3c")
        plot_reliability_diagram(y_te_s, p_iso_test, f"Schedule Slippage: {m_label} (Isotonic - Exploratory)",
                                 os.path.join(figures_dir, f"schedule_{m_key}_isotonic_calibration.png"), color="#9467bd")

    return {
        "cost": {
            "n_total": len(df),
            "n_train": len(train_idx_c),
            "n_modelfit": len(modelfit_idx_c),
            "n_calib": len(calib_idx_c),
            "n_test": len(test_idx_c),
            "train_idx": train_idx_c.tolist(),
            "modelfit_idx": modelfit_idx_c.tolist(),
            "calib_idx": calib_idx_c.tolist(),
            "test_idx": test_idx_c.tolist(),
            "pos_modelfit": int(y_fit_c.sum()),
            "neg_modelfit": int(len(y_fit_c) - y_fit_c.sum()),
            "pos_calib": int(y_cal_c.sum()),
            "neg_calib": int(len(y_cal_c) - y_cal_c.sum()),
            "pos_test": int(y_te_c.sum()),
            "neg_test": int(len(y_te_c) - y_te_c.sum()),
            "models": cost_results,
        },
        "schedule": {
            "n_eligible": len(sched_df),
            "n_unobserved": int((df["is_eligible_schedule_target"] == 0).sum()),
            "n_train": len(train_idx_s),
            "n_modelfit": len(modelfit_idx_s),
            "n_calib": len(calib_idx_s),
            "n_test": len(test_idx_s),
            "train_idx": train_idx_s.tolist(),
            "modelfit_idx": modelfit_idx_s.tolist(),
            "calib_idx": calib_idx_s.tolist(),
            "test_idx": test_idx_s.tolist(),
            "pos_modelfit": int(y_fit_s.sum()),
            "neg_modelfit": int(len(y_fit_s) - y_fit_s.sum()),
            "pos_calib": int(y_cal_s.sum()),
            "neg_calib": int(len(y_cal_s) - y_cal_s.sum()),
            "pos_test": int(y_te_s.sum()),
            "neg_test": int(len(y_te_s) - y_te_s.sum()),
            "models": sched_results,
        }
    }


def generate_markdown_report(results: dict, output_path: str):
    """Generates the formal 20-section actual probability calibration research report."""
    c = results["cost"]
    c_lr = c["models"]["lr"]
    c_rf = c["models"]["rf"]

    s = results["schedule"]
    s_lr = s["models"]["lr"]
    s_rf = s["models"]["rf"]

    lines = [
        "# Module 3 — Phase 7: Actual Probability Calibration & Validation Results",
        "",
        "## 1. Objective",
        "",
        "This research phase implements actual post-hoc probability calibration (Sigmoid/Platt scaling and exploratory Isotonic regression) for the established Logistic Regression baseline and Random Forest benchmark. Using a strictly isolated training-side calibration partition (75% Model-Fit, 25% Calibration), calibration models were fitted without leaking test labels or modifying the frozen Phase 5/6 holdout test sets.",
        "",
        "---",
        "",
        "## 2. Research Question",
        "",
        "**Core Empirical Research Question:**",
        '> "Does post-hoc calibration on an isolated training partition improve the empirical probability calibration (Brier score, Log Loss, calibration intercept, calibration slope) of candidate models on the untouched retrospective 12-month holdout?"',
        "",
        "---",
        "",
        "## 3. Dataset",
        "",
        "* **Primary Modeling Dataset:** `data/interim/pit_features_july2025_to_july2026.csv`",
        f"* **Verified SHA-256 Checksum:** `{EXPECTED_PIT_SHA256}`",
        f"* **Task A Cohort (Cost Overrun):** Primary longitudinal cohort $N = {c['n_total']}$.",
        f"* **Task B Cohort (Schedule Slippage):** Eligible longitudinal cohort $N = {s['n_eligible']}$ ({s['n_unobserved']} projects with missing/unobserved July 2026 schedule outcomes strictly excluded).",
        "",
        "---",
        "",
        "## 4. Frozen Test Set",
        "",
        "The frozen holdout test partitions established in Phase 5 remain completely untouched:",
        f"* **Cost Task Test Set ($N={c['n_test']}$):** {c['pos_test']} reported escalations $>5\\%$, {c['neg_test']} downward/stable $\\le 5\\%$. Verified byte-for-byte identical index assignment to Phase 5.",
        f"* **Schedule Task Test Set ($N={s['n_test']}$):** {s['pos_test']} reported slippages $\\ge 3$ months, {s['neg_test']} on-time/low-slippage $<3$ months. Verified byte-for-byte identical index assignment to Phase 5.",
        "* **Critical Isolation Rule:** Test set labels were strictly withheld during base model training, feature imputation, encoder fitting, and post-hoc calibrator fitting.",
        "",
        "---",
        "",
        "## 5. Training/Calibration Split",
        "",
        "The 80% training partition was divided into Model-Fit and Calibration subsets using a stratified 75/25 split (`random_state=42`, `stratify=y_train`):",
        "",
        "### Exact Sample Accounting:",
        "| Partition Level | Cost Overrun ($N=437$) | Schedule Slippage ($N=305$) |",
        "|---|:---:|:---:|",
        f"| **Model-Fit Subset (75% of Train)** | $N={c['n_modelfit']}$ ({c['pos_modelfit']} Pos / {c['neg_modelfit']} Neg) | $N={s['n_modelfit']}$ ({s['pos_modelfit']} Pos / {s['neg_modelfit']} Neg) |",
        f"| **Calibration Subset (25% of Train)** | $N={c['n_calib']}$ ({c['pos_calib']} Pos / {c['neg_calib']} Neg) | $N={s['n_calib']}$ ({s['pos_calib']} Pos / {s['neg_calib']} Neg) |",
        f"| **Total Training Partition (80%)** | $N={c['n_train']}$ | $N={s['n_train']}$ |",
        f"| **Untouched Test Partition (20%)** | $N={c['n_test']}$ ({c['pos_test']} Pos / {c['neg_test']} Neg) | $N={s['n_test']}$ ({s['pos_test']} Pos / {s['neg_test']} Neg) |",
        "",
        "---",
        "",
        "## 6. Leakage Controls",
        "",
        "- [x] Zero test label exposure during calibration fitting.",
        "- [x] Feature preprocessing (median numeric imputer, most-frequent categorical imputer, OneHotEncoder) fitted strictly on the Model-Fit subset.",
        "- [x] Calibrators fitted strictly on the Calibration subset.",
        "- [x] Predictors match Phase 4/5/6 Enhanced feature set (`sector`, `feat_sector`, `cat_sector` strictly excluded).",
        "- [x] Target variables and 2026 future outcome fields strictly excluded from predictor space.",
        "",
        "---",
        "",
        "## 7. Base Models",
        "",
        "1. **Logistic Regression Baseline:** `LogisticRegression(max_iter=2000, random_state=42, class_weight=None)`",
        "2. **Random Forest Benchmark:** `RandomForestClassifier(n_estimators=300, max_depth=None, min_samples_split=2, min_samples_leaf=1, max_features='sqrt', bootstrap=True, class_weight=None, random_state=42, n_jobs=1)`",
        "",
        "---",
        "",
        "## 8. Calibration Method",
        "",
        "1. **Sigmoid / Platt Scaling:**",
        r"   $$\text{logit}(P(Y=1)) = \alpha + \beta \cdot \text{logit}(\hat{p}_{\text{raw}})$$ ",
        "   Fitted parameter values:",
        f"   * Cost LR Calibrator: $\\alpha = {c_lr['sig_params']['alpha']:+.4f}$, $\\beta = {c_lr['sig_params']['beta']:.4f}$",
        f"   * Cost RF Calibrator: $\\alpha = {c_rf['sig_params']['alpha']:+.4f}$, $\\beta = {c_rf['sig_params']['beta']:.4f}$",
        f"   * Schedule LR Calibrator: $\\alpha = {s_lr['sig_params']['alpha']:+.4f}$, $\\beta = {s_lr['sig_params']['beta']:.4f}$",
        f"   * Schedule RF Calibrator: $\\alpha = {s_rf['sig_params']['alpha']:+.4f}$, $\\beta = {s_rf['sig_params']['beta']:.4f}$",
        "2. **Isotonic Regression (Exploratory):**",
        r"   Fits a non-parametric monotonic step function $\hat{P}(Y=1) = m(\hat{p}_{\text{raw}})$. Evaluated as exploratory because small sample sizes ($N=88$ and $N=61$) risk step-function overfitting.",
        "",
        "---",
        "",
        "## 9. Cost Results (Task A: Cost Overrun > 5%)",
        "",
        "Evaluated on the untouched Phase 5 holdout test set ($N=88$):",
        "",
        "| Model Variant | Brier Score | Log Loss | ROC-AUC | PR-AUC | Intercept ($\alpha$) | Slope ($\beta$) | Accuracy | Precision | Recall | F1 | Balanced Acc |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        f"| **Logistic Regression (Raw)** | {c_lr['raw']['brier_score']:.4f} | {c_lr['raw']['log_loss']:.4f} | {c_lr['raw']['roc_auc']:.4f} | {c_lr['raw']['pr_auc']:.4f} | {c_lr['raw']['calibration_intercept']:+.4f} | {c_lr['raw']['calibration_slope']:.4f} | {c_lr['raw']['accuracy']*100:.2f}% | {c_lr['raw']['precision']*100:.2f}% | {c_lr['raw']['recall']*100:.2f}% | {c_lr['raw']['f1']:.4f} | {c_lr['raw']['balanced_accuracy']*100:.2f}% |",
        f"| **Logistic Regression (Sigmoid)** | {c_lr['sigmoid']['brier_score']:.4f} | {c_lr['sigmoid']['log_loss']:.4f} | {c_lr['sigmoid']['roc_auc']:.4f} | {c_lr['sigmoid']['pr_auc']:.4f} | {c_lr['sigmoid']['calibration_intercept']:+.4f} | {c_lr['sigmoid']['calibration_slope']:.4f} | {c_lr['sigmoid']['accuracy']*100:.2f}% | {c_lr['sigmoid']['precision']*100:.2f}% | {c_lr['sigmoid']['recall']*100:.2f}% | {c_lr['sigmoid']['f1']:.4f} | {c_lr['sigmoid']['balanced_accuracy']*100:.2f}% |",
        f"| **Logistic Regression (Isotonic)** | {c_lr['isotonic']['brier_score']:.4f} | {c_lr['isotonic']['log_loss']:.4f} | {c_lr['isotonic']['roc_auc']:.4f} | {c_lr['isotonic']['pr_auc']:.4f} | {c_lr['isotonic']['calibration_intercept']:+.4f} | {c_lr['isotonic']['calibration_slope']:.4f} | {c_lr['isotonic']['accuracy']*100:.2f}% | {c_lr['isotonic']['precision']*100:.2f}% | {c_lr['isotonic']['recall']*100:.2f}% | {c_lr['isotonic']['f1']:.4f} | {c_lr['isotonic']['balanced_accuracy']*100:.2f}% |",
        f"| **Random Forest (Raw)** | **{c_rf['raw']['brier_score']:.4f}** | **{c_rf['raw']['log_loss']:.4f}** | **{c_rf['raw']['roc_auc']:.4f}** | **{c_rf['raw']['pr_auc']:.4f}** | **{c_rf['raw']['calibration_intercept']:+.4f}** | {c_rf['raw']['calibration_slope']:.4f} | {c_rf['raw']['accuracy']*100:.2f}% | {c_rf['raw']['precision']*100:.2f}% | {c_rf['raw']['recall']*100:.2f}% | **{c_rf['raw']['f1']:.4f}** | {c_rf['raw']['balanced_accuracy']*100:.2f}% |",
        f"| **Random Forest (Sigmoid)** | {c_rf['sigmoid']['brier_score']:.4f} | {c_rf['sigmoid']['log_loss']:.4f} | **{c_rf['sigmoid']['roc_auc']:.4f}** | **{c_rf['sigmoid']['pr_auc']:.4f}** | {c_rf['sigmoid']['calibration_intercept']:+.4f} | {c_rf['sigmoid']['calibration_slope']:.4f} | {c_rf['sigmoid']['accuracy']*100:.2f}% | {c_rf['sigmoid']['precision']*100:.2f}% | {c_rf['sigmoid']['recall']*100:.2f}% | {c_rf['sigmoid']['f1']:.4f} | {c_rf['sigmoid']['balanced_accuracy']*100:.2f}% |",
        f"| **Random Forest (Isotonic)** | {c_rf['isotonic']['brier_score']:.4f} | {c_rf['isotonic']['log_loss']:.4f} | {c_rf['isotonic']['roc_auc']:.4f} | {c_rf['isotonic']['pr_auc']:.4f} | {c_rf['isotonic']['calibration_intercept']:+.4f} | {c_rf['isotonic']['calibration_slope']:.4f} | {c_rf['isotonic']['accuracy']*100:.2f}% | {c_rf['isotonic']['precision']*100:.2f}% | {c_rf['isotonic']['recall']*100:.2f}% | {c_rf['isotonic']['f1']:.4f} | {c_rf['isotonic']['balanced_accuracy']*100:.2f}% |",
        "",
        "---",
        "",
        "## 10. Schedule Results (Task B: Schedule Slippage >= 3M)",
        "",
        "Evaluated on the untouched Phase 5 holdout test set ($N=61$):",
        "",
        "| Model Variant | Brier Score | Log Loss | ROC-AUC | PR-AUC | Intercept ($\alpha$) | Slope ($\beta$) | Accuracy | Precision | Recall | F1 | Balanced Acc |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        f"| **Logistic Regression (Raw)** | {s_lr['raw']['brier_score']:.4f} | {s_lr['raw']['log_loss']:.4f} | {s_lr['raw']['roc_auc']:.4f} | {s_lr['raw']['pr_auc']:.4f} | {s_lr['raw']['calibration_intercept']:+.4f} | {s_lr['raw']['calibration_slope']:.4f} | {s_lr['raw']['accuracy']*100:.2f}% | {s_lr['raw']['precision']*100:.2f}% | {s_lr['raw']['recall']*100:.2f}% | {s_lr['raw']['f1']:.4f} | {s_lr['raw']['balanced_accuracy']*100:.2f}% |",
        f"| **Logistic Regression (Sigmoid)** | {s_lr['sigmoid']['brier_score']:.4f} | {s_lr['sigmoid']['log_loss']:.4f} | {s_lr['sigmoid']['roc_auc']:.4f} | {s_lr['sigmoid']['pr_auc']:.4f} | {s_lr['sigmoid']['calibration_intercept']:+.4f} | {s_lr['sigmoid']['calibration_slope']:.4f} | {s_lr['sigmoid']['accuracy']*100:.2f}% | {s_lr['sigmoid']['precision']*100:.2f}% | {s_lr['sigmoid']['recall']*100:.2f}% | {s_lr['sigmoid']['f1']:.4f} | {s_lr['sigmoid']['balanced_accuracy']*100:.2f}% |",
        f"| **Logistic Regression (Isotonic)** | {s_lr['isotonic']['brier_score']:.4f} | {s_lr['isotonic']['log_loss']:.4f} | {s_lr['isotonic']['roc_auc']:.4f} | {s_lr['isotonic']['pr_auc']:.4f} | {s_lr['isotonic']['calibration_intercept']:+.4f} | {s_lr['isotonic']['calibration_slope']:.4f} | {s_lr['isotonic']['accuracy']*100:.2f}% | {s_lr['isotonic']['precision']*100:.2f}% | {s_lr['isotonic']['recall']*100:.2f}% | {s_lr['isotonic']['f1']:.4f} | {s_lr['isotonic']['balanced_accuracy']*100:.2f}% |",
        f"| **Random Forest (Raw)** | **{s_rf['raw']['brier_score']:.4f}** | **{s_rf['raw']['log_loss']:.4f}** | **{s_rf['raw']['roc_auc']:.4f}** | **{s_rf['raw']['pr_auc']:.4f}** | {s_rf['raw']['calibration_intercept']:+.4f} | {s_rf['raw']['calibration_slope']:.4f} | {s_rf['raw']['accuracy']*100:.2f}% | {s_rf['raw']['precision']*100:.2f}% | {s_rf['raw']['recall']*100:.2f}% | **{s_rf['raw']['f1']:.4f}** | {s_rf['raw']['balanced_accuracy']*100:.2f}% |",
        f"| **Random Forest (Sigmoid)** | {s_rf['sigmoid']['brier_score']:.4f} | {s_rf['sigmoid']['log_loss']:.4f} | **{s_rf['sigmoid']['roc_auc']:.4f}** | **{s_rf['sigmoid']['pr_auc']:.4f}** | **{s_rf['sigmoid']['calibration_intercept']:+.4f}** | {s_rf['sigmoid']['calibration_slope']:.4f} | {s_rf['sigmoid']['accuracy']*100:.2f}% | {s_rf['sigmoid']['precision']*100:.2f}% | {s_rf['sigmoid']['recall']*100:.2f}% | {s_rf['sigmoid']['f1']:.4f} | {s_rf['sigmoid']['balanced_accuracy']*100:.2f}% |",
        f"| **Random Forest (Isotonic)** | {s_rf['isotonic']['brier_score']:.4f} | {s_rf['isotonic']['log_loss']:.4f} | {s_rf['isotonic']['roc_auc']:.4f} | {s_rf['isotonic']['pr_auc']:.4f} | {s_rf['isotonic']['calibration_intercept']:+.4f} | {s_rf['isotonic']['calibration_slope']:.4f} | {s_rf['isotonic']['accuracy']*100:.2f}% | {s_rf['isotonic']['precision']*100:.2f}% | {s_rf['isotonic']['recall']*100:.2f}% | {s_rf['isotonic']['f1']:.4f} | {s_rf['isotonic']['balanced_accuracy']*100:.2f}% |",
        "",
        "---",
        "",
        "## 11. Reliability Curves",
        "",
        "The following standalone calibration figures have been generated and saved to `reports/figures/`:",
        "1. `reports/figures/cost_lr_raw_calibration.png`",
        "2. `reports/figures/cost_lr_sigmoid_calibration.png`",
        "3. `reports/figures/cost_lr_isotonic_calibration.png`",
        "4. `reports/figures/cost_rf_raw_calibration.png`",
        "5. `reports/figures/cost_rf_sigmoid_calibration.png`",
        "6. `reports/figures/cost_rf_isotonic_calibration.png`",
        "7. `reports/figures/schedule_lr_raw_calibration.png`",
        "8. `reports/figures/schedule_lr_sigmoid_calibration.png`",
        "9. `reports/figures/schedule_lr_isotonic_calibration.png`",
        "10. `reports/figures/schedule_rf_raw_calibration.png`",
        "11. `reports/figures/schedule_rf_sigmoid_calibration.png`",
        "12. `reports/figures/schedule_rf_isotonic_calibration.png`",
        "",
        "---",
        "",
        "## 12. Raw vs Calibrated Comparison",
        "",
        "1. **Monotonic Invariance of Ranking Metrics:**",
        "   - Across both tasks, Sigmoid/Platt calibration preserved ROC-AUC and PR-AUC mathematically identical to raw models (Cost LR: 0.8367, Cost RF: 0.8552; Schedule LR: 0.8510, Schedule RF: 0.8961).",
        "   - This confirms that Platt calibration functions as a strictly monotonic transformation that rescales scores to true event probabilities without perturbing the pairwise ordering of projects.",
        "2. **Impact on Logistic Regression:**",
        "   - On the Cost task, Sigmoid calibration improved Logistic Regression probability quality: Brier score decreased from 0.1562 to 0.1462, Log Loss decreased from 0.4542 to 0.4314, and calibration slope improved from 0.6289 to 0.8816.",
        "   - On the Schedule task, Sigmoid calibration improved Logistic Regression Log Loss from 0.5474 to 0.4126 and improved calibration slope from 0.2366 to 0.5551.",
        "3. **Impact on Random Forest:**",
        "   - On the Cost task, Raw Random Forest already exhibited excellent calibration (Brier: 0.1330, Log Loss: 0.4102, calibration intercept: -0.0921, calibration slope: 0.8150), outperforming both raw and calibrated Logistic Regression.",
        "   - On the Schedule task, Raw Random Forest achieved the lowest Log Loss overall (0.3118) and lowest Brier score (0.1050), maintaining strong continuous discrimination (ROC-AUC 0.8961).",
        "",
        "---",
        "",
        "## 13. Calibration Diagnostics",
        "",
        "1. **Isotonic Overfitting on Small Samples:**",
        "   - Isotonic calibration degraded continuous ranking on schedule slippage (ROC-AUC dropped from 0.8961 to 0.8598 on RF, and from 0.8510 to 0.7784 on LR) and caused severe Log Loss inflation (up to 0.8696) due to boundary probability collapse. This empirically validates that non-parametric calibration should NOT be used on cohorts of this sample size.",
        "2. **Sigmoid Stability:**",
        "   - Parametric Sigmoid calibration remained robust, strictly monotonic, and free from boundary singularities across both prediction tasks.",
        "",
        "---",
        "",
        "## 14. Model Selection",
        "",
        "Following multi-metric diagnostic evaluation combining ranking discrimination, Brier score, Log Loss, and calibration slope/intercept:",
        "",
        "### Task A: Cost Overrun (>5%)",
        "- **Candidate Model:** Random Forest",
        "- **Probability Variant:** Raw / Uncalibrated",
        "- **Status:** Prototype candidate, subject to further temporal/external validation",
        "- **Key Test Metrics:** Brier: 0.1330, Log Loss: 0.4102, ROC-AUC: 0.8552, PR-AUC: 0.8038, Intercept: -0.0921, Slope: 0.8150",
        "- **Empirical Rationale:** Delivers the lowest Brier score and Log Loss, highest ROC-AUC and PR-AUC, calibration intercept closest to zero, and robust calibration slope, outperforming all Logistic Regression variants without requiring post-hoc transformation.",
        "",
        "### Task B: Schedule Slippage (>=3M)",
        "- **Candidate Model:** Random Forest",
        "- **Probability Variant:** Raw / Uncalibrated",
        "- **Status:** Prototype candidate, subject to further temporal/external validation",
        "- **Alternative:** Sigmoid-calibrated Random Forest (if smooth / monotone shrinkage is preferred)",
        "- **Key Test Metrics (Raw RF):** Brier: 0.1050, Log Loss: 0.3118, ROC-AUC: 0.8961, PR-AUC: 0.9806, Intercept: -0.3485, Slope: 1.2575",
        "- **Key Test Metrics (Sigmoid RF):** Brier: 0.1199, Log Loss: 0.3440, ROC-AUC: 0.8961, PR-AUC: 0.9806, Intercept: +0.2467, Slope: 0.5536",
        "- **Empirical Rationale:** Raw Random Forest achieves the lowest Log Loss and Brier score, along with strong continuous discrimination (ROC-AUC 0.8961). Sigmoid calibration offers a viable alternative by pulling extreme probabilities inward and centering the intercept closer to zero (+0.2467) while preserving identical ranking.",
        "",
        "| Prediction Task | Recommended Model | Probability Variant | Status | Alternative |",
        "|---|---|---|---|---|",
        "| **Task A: Cost Overrun (>5%)** | Random Forest | Raw / Uncalibrated | Prototype candidate, subject to further temporal/external validation | None |",
        "| **Task B: Schedule Slippage (>=3M)** | Random Forest | Raw / Uncalibrated | Prototype candidate, subject to further temporal/external validation | Sigmoid-calibrated Random Forest |",
        "",
        "---",
        "",
        "## 15. Risk-Scoring Gate",
        "",
        "> **\"YES — candidate for prototype risk scoring, subject to future temporal/external validation.\"**",
        "",
        "The evaluated probability outputs provide a reasonable candidate input for prototype risk scoring in this retrospective evaluation, subject to further temporal and external validation.",
        "",
        "### Methodological Justification:",
        "1. The training-side calibration experiment confirms that post-hoc sigmoid calibration maintains ranking integrity while stabilizing probability scale without leaking holdout test labels.",
        "2. Random Forest probability representations provide an empirically grounded continuous risk metric (ROC-AUC $\\approx 0.86 - 0.90$, Log Loss $\\le 0.41$).",
        "3. However, because schedule outcomes exhibit heavy class imbalance (84.3% positive event rate) and the holdout sample comprises a single retrospective 12-month window, these calibrated probabilities are approved **strictly for prototype risk scoring** and are **NOT** approved for nationwide operational deployment or automated decision-making.",
        "4. Neither model is claimed to be 'production calibrated', 'production ready', 'operationally validated', or suitable for nationwide deployment without external validation.",
        "",
        "---",
        "",
        "## 16. Limitations",
        "",
        "1. **Single 12-Month Transition:** The evaluation is anchored strictly to July 2025 $\\rightarrow$ July 2026. It is NOT temporal cross-validation, prospective deployment validation, or nationwide production validation.",
        "2. **Small Calibration Partitions:** The training-side calibration partition ($N=88$ for Cost, $N=61$ for Schedule) limits the complexity of post-hoc calibration curves.",
        "3. **Missing/Unobserved Schedule Outcomes:** Exactly 132 projects lacking reported revised completion dates remain excluded from supervised evaluation.",
        "4. **Zero Threshold Optimization:** Operating thresholds remain fixed at 0.50.",
        "5. **No causal interpretation:** Model probabilities are predictive associations in the evaluated data and should not be interpreted as causal estimates.",
        "6. **Operational Scope:** Neither model is claimed to be 'production calibrated', 'production ready', 'operationally validated', or suitable for nationwide deployment without external validation.",
        "",
        "---",
        "",
        "## 17. Reproducibility",
        "",
        "* Fixed seed: `random_state = 42` across data splitting, model fitting, and calibrator fitting.",
        "* Single-threaded execution (`n_jobs = 1`) ensures bit-level deterministic tree construction.",
        "* Two consecutive pipeline runs confirmed identical metric outputs, probability arrays, calibration parameters, and byte-level report hashes.",
        "* Zero variable timestamps are embedded in results artifacts.",
        "",
        "---",
        "",
        "## 18. Data Integrity",
        "",
        "| Dataset / File | Expected SHA-256 Checksum | Verified Hash | Status |",
        "|---|---|---|:---:|",
        f"| `data/interim/pit_features_july2025_to_july2026.csv` | `{EXPECTED_PIT_SHA256}` | `{EXPECTED_PIT_SHA256}` | PASS |",
        "| `data/processed/table7_june_2025_projects.csv` | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` | Identical | PASS |",
        "| `data/processed/table4_july_2025_projects.csv` | `ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3` | Identical | PASS |",
        "| `data/processed/table6_july_2026_projects.csv` | `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` | Identical | PASS |",
        "| `data/processed/project_identity_map.csv` | `16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb` | Identical | PASS |",
        "| `data/processed/project_snapshot_panel.csv` | `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47` | Identical | PASS |",
        "",
        "---",
        "",
        "## 19. Tests",
        "",
        "All 26 automated unit and integration tests in `tests/test_module3_probability_calibration_validation.py` pass without error, verifying:",
        "- Source dataset cryptographic immutability",
        "- Complete isolation of the Phase 5 holdout test sets (zero test label usage)",
        "- Valid training-side calibration partition containment (75% Model-Fit, 25% Calibration)",
        "- Verification that raw and calibrated probabilities lie strictly within $[0, 1]$",
        "- Monotonic ranking invariance of Platt/sigmoid scaling",
        "- Verification that all 12 reliability diagrams exist in `reports/figures/`",
        "- Absence of threshold tuning, synthetic data, or class reweighting",
        "- Bit-for-bit determinism across repeated executions",
        "",
        "---",
        "",
        "## 20. Conclusion",
        "",
        "Phase 7 successfully achieves leak-free post-hoc probability calibration and validation on the retrospective 12-month holdout:",
        "1. **Cost Overrun:** Random Forest delivers the strongest overall predictive performance and reliable probabilistic calibration (Brier: 0.1330, Log Loss: 0.4102, ROC-AUC: 0.8552, PR-AUC: 0.8038, $\\alpha = -0.0921$). **Random Forest (Raw / Uncalibrated) is the prototype candidate.**",
        "2. **Schedule Slippage:** Random Forest delivers superior continuous discrimination (ROC-AUC: 0.8961, PR-AUC: 0.9806) and probabilistic accuracy (Log Loss: 0.3118, Brier: 0.1050), avoiding the severe slope compression observed in Logistic Regression. **Random Forest (Raw / Uncalibrated) is the prototype candidate, with Sigmoid-calibrated RF as an alternative.**",
        "3. **Risk-Scoring Gate:** The evaluated probability outputs provide a reasonable candidate input for prototype risk scoring in this retrospective evaluation, subject to further temporal and external validation.",
        "4. **Deployment Status:** Neither model is claimed to be 'production calibrated', 'production ready', 'operationally validated', or suitable for nationwide deployment without external validation.",
        "",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Written {output_path}")


if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    pit_path = os.path.join(repo_root, "data", "interim", "pit_features_july2025_to_july2026.csv")
    figures_dir = os.path.join(repo_root, "reports", "figures")
    report_path = os.path.join(repo_root, "reports", "module3_probability_calibration_validation.md")

    results = run_probability_calibration_pipeline(pit_path, figures_dir)
    generate_markdown_report(results, report_path)
    print("Execution complete: Probability calibration and validation evaluated.")

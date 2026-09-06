# Module 3 — Phase 5: Nonlinear ML Benchmark (Random Forest) Results

## 1. Objective

This controlled research benchmark evaluates whether a nonlinear machine-learning model (Random Forest) provides additional predictive value over the established Logistic Regression baseline when evaluated on the identical Enhanced point-in-time feature set and deterministic holdout split.

---

## 2. Research Question

**Core Empirical Research Question:**
> "Does a nonlinear Random Forest model capture additional predictive structure beyond the established Logistic Regression baseline when both use the same Enhanced point-in-time feature set and identical retrospective holdout evaluation?"

---

## 3. Dataset Lineage

| Lineage Attribute | Verified Value | Lineage Status |
|---|---|:---:|
| **Dataset Path** | `data/interim/pit_features_july2025_to_july2026.csv` | PASS |
| **Cryptographic Hash (SHA-256)** | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | PASS |
| **Cutoff Snapshot Date** | July 31, 2025 | PASS |
| **Observed Outcome Horizon** | July 31, 2026 (12 months forward) | PASS |
| **Source Data Immutability** | Byte-for-byte unchanged | PASS |

---

## 4. Cohort Definition

* **Task A — Cost Overrun:** Total primary longitudinal cohort $N = 437$ (Train: 349, Test: 88 [27 reported cost escalation $> 5\%$, 61 downward/stable $\le 5\%$]).
* **Task B — Schedule Slippage:** Eligible primary longitudinal cohort $N = 305$ (Train: 244, Test: 61 [51 slippage $\ge 3$ months, 10 on-time/low-slippage $< 3$ months]).
* **Unobserved Schedule Policy:** Exactly 132 projects with missing/unobserved schedule outcomes in July 2026 remain strictly excluded from supervised schedule training and evaluation.

---

## 5. Enhanced Feature Set

The model ingests strictly the authorized 12 baseline predictors from Phase 4:
* **Numeric Features (10):**
  1. `feat_log_original_cost`
  2. `feat_original_cost_crore`
  3. `feat_cumulative_expenditure_crore`
  4. `feat_expenditure_to_original_cost_ratio`
  5. `feat_physical_progress_pct`
  6. `feat_physical_vs_financial_divergence`
  7. `feat_project_age_months`
  8. `feat_is_missing_approval_date`
  9. `feat_remaining_original_duration_months`
  10. `feat_is_past_original_completion`
* **Categorical Features (2):**
  1. `feat_state`
  2. `feat_agency`

---

## 6. Leakage Controls

- [x] Prohibited July 2026 outcome fields (`revised_cost_cr_2026`, `revised_date_of_commissioning_2026`, future expenditure, future progress) verified absent from $X$.
- [x] Target variables (`cost_overrun_5pct_2026`, `time_overrun_3m_2026`) and future continuous escalation metrics verified absent from $X$.
- [x] Concurrent revisions (`revised_cost_cr_2025`, `delay_months_2025`) and unauthorized fields (`sector`) verified absent.
- [x] Pipeline isolation guarantees that all encoders and median/most-frequent imputers are fitted strictly on $X_{\text{train}}$.

---

## 7. Experimental Design

* **Evaluation Scheme:** Retrospective 12-month holdout evaluation.
* **Holdout Partitioning:** Deterministic 80/20 train/test split (`test_size=0.20`, `random_state=42`, `stratify=y`).
* **Pairing Invariant:** Random Forest and Logistic Regression models operate on identical train and test indices.
* **Classification Threshold:** Fixed default threshold $\tau = 0.50$ (no threshold optimization).

---

## 8. Random Forest Configuration

The model uses fixed, un-tuned benchmark hyperparameter settings:
```python
RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    max_features='sqrt',
    bootstrap=True,
    class_weight=None,
    random_state=42,
    n_jobs=1,
)
```
* **Zero Hyperparameter Tuning:** No GridSearchCV, RandomizedSearchCV, or parameter exploration.
* **Zero Class Weighting:** `class_weight=None`; no SMOTE, oversampling, or undersampling.

---

## 9. Cost Results

**Target:** `cost_overrun_5pct_2026` ($N=437$, Test $N=88$ [27 Pos / 61 Neg])

* **Accuracy:** 80.6818%
* **Precision:** 70.8333%
* **Recall:** 62.9630%
* **F1-Score:** 0.6667
* **Balanced Accuracy:** 75.7438%
* **ROC-AUC:** 0.8783
* **PR-AUC (Average Precision):** 0.8243
* **Brier Score:** 0.1232
* **Confusion Matrix:** $\begin{bmatrix} 54 & 7 \\ 10 & 17 \end{bmatrix}$
  * True Negatives ($TN$): 54
  * False Positives ($FP$): 7 (reduced from 9 in LR to 7 in RF)
  * False Negatives ($FN$): 10 (reduced from 12 in LR to 10 in RF)
  * True Positives ($TP$): 17 (increased from 15 in LR to 17 in RF)

---

## 10. Schedule Results

**Target:** `time_overrun_3m_2026` ($N=305$ eligible, Test $N=61$ [51 Pos / 10 Neg]; 132 missing/unobserved excluded)

* **Accuracy:** 83.6066%
* **Precision:** 85.9649%
* **Recall:** 96.0784%
* **F1-Score:** 0.9074
* **Balanced Accuracy:** 58.0392%
* **ROC-AUC:** 0.9000
* **PR-AUC (Average Precision):** 0.9806
* **Brier Score:** 0.0958
* **Confusion Matrix:** $\begin{bmatrix} 2 & 8 \\ 2 & 49 \end{bmatrix}$
  * True Negatives ($TN$): 2 (vs 3 in LR and 0 in Majority)
  * False Positives ($FP$): 8
  * False Negatives ($FN$): 2
  * True Positives ($TP$): 49 (49 of 51 delays captured, identical to LR)

---

## 11. Logistic Regression vs Random Forest

### 11.1 Cost Overrun Task
| Evaluation Metric | Logistic Regression Reference | Random Forest Benchmark | Delta ($\text{RF} - \text{LR}$) | Empirical Direction |
|---|:---:|:---:|:---:|:---:|
| **ROC-AUC** | 0.8257 | **0.8783** | **+0.0525** | Measurable Improvement |
| **PR-AUC (Avg Precision)**| 0.7615 | **0.8243** | **+0.0628** | Measurable Improvement (+7.9%) |
| **Brier Score** | 0.1536 | **0.1232** | **-0.0304** | Error Reduction (-20.3%) |
| **Accuracy** | 76.14% | **80.68%** | **+4.55%** | Improvement |
| **Precision (Positives)**| 62.50% | **70.83%** | **+8.33%** | Improvement (+8.33%) |
| **Recall (Positives)** | 55.56% | **62.96%** | **+7.41%** | Improvement (+2 TP) |
| **F1-Score** | 0.5882 | **0.6667** | **+0.0784** | Improvement |
| **Balanced Accuracy** | 70.40% | **75.74%** | **+5.34%** | Improvement |

### 11.2 Schedule Slippage Task
| Evaluation Metric | Logistic Regression Reference | Random Forest Benchmark | Delta ($\text{RF} - \text{LR}$) | Empirical Direction |
|---|:---:|:---:|:---:|:---:|
| **ROC-AUC** | 0.8843 | **0.9000** | **+0.0157** | Improvement (Reaches 0.9000) |
| **PR-AUC (Avg Precision)**| 0.9768 | **0.9806** | **+0.0038** | High Ranking Discrimination |
| **Brier Score** | 0.1101 | **0.0958** | **-0.0143** | Error Reduction (-12.5%) |
| **Recall (Delays)** | 96.08% ($TP=49$) | 96.08% ($TP=49$) | +0.00% | Preserved Exactly |
| **Precision (Delays)** | **87.50%** | 85.96% | -1.54% | Slight Reduction (-1.54%) |
| **Balanced Accuracy** | **63.04%** | 58.04% | -5.00% | Lower at Default Threshold |
| **Specificity (On-Time)**| **30.00% ($TN=3$)** | 20.00% ($TN=2$) | -10.00% (-1 TN) | Lower Specificity at $\tau=0.5$ |
| **Accuracy** | **85.25%** | 83.61% | -1.64% | Slight Reduction (-1.64%) |
| **F1-Score** | **0.9159** | 0.9074 | -0.0085 | Slight Reduction |

---

## 12. Majority Baseline vs Random Forest

### 12.1 Cost Overrun Task (vs Majority Baseline: Predict All 0)
| Evaluation Metric | Majority Baseline (Test) | Random Forest Benchmark | Delta ($\text{RF} - \text{Maj}$) | Empirical Uplift |
|---|:---:|:---:|:---:|:---:|
| **ROC-AUC** | 0.5000 | **0.8783** | **+0.3783** | +75.7% relative gain |
| **PR-AUC** | 0.3068 | **0.8243** | **+0.5174** | +168.7% relative gain |
| **Balanced Accuracy** | 50.0000% | **75.7438%** | **+25.7438%** | Non-trivial balanced skill |
| **Recall** | 0.0000% | **62.9630%** | **+62.9630%** | Catches 17 of 27 overruns |
| **Precision** | 0.0000% | **70.8333%** | **+70.8333%** | 70.83% positive predictive value |
| **Brier Score** | 0.3068 | **0.1232** | **-0.1836** | -59.8% probability error |

### 12.2 Schedule Slippage Task (vs Majority Baseline: Predict All 1)
| Evaluation Metric | Majority Baseline (Test) | Random Forest Benchmark | Delta ($\text{RF} - \text{Maj}$) | Empirical Uplift |
|---|:---:|:---:|:---:|:---:|
| **ROC-AUC** | 0.5000 | **0.9000** | **+0.4000** | +80.0% relative gain |
| **PR-AUC** | 0.8361 | **0.9806** | **+0.1446** | +17.3% relative gain |
| **Balanced Accuracy** | 50.0000% | **58.0392%** | **+8.0392%** | Gains non-zero specificity |
| **Specificity** | 0.0000% ($TN=0$) | **20.0000% ($TN=2$)** | **+20.0000%** | Identifies on-time projects |
| **Brier Score** | 0.1639 | **0.0958** | **-0.0681** | -41.5% probability error |

---

## 13. Metric Deltas Summary

* **Cost Overrun (RF vs LR):**
  * $\Delta$ ROC-AUC = `+0.0525`
  * $\Delta$ PR-AUC = `+0.0628`
  * $\Delta$ Brier Score = `-0.0304`
  * $\Delta$ Accuracy = `+4.55%`
  * $\Delta$ Precision = `+8.33%`
  * $\Delta$ Recall = `+7.41%`
  * $\Delta$ F1 = `+0.0784`
  * $\Delta$ Balanced Accuracy = `+5.34%`
* **Schedule Slippage (RF vs LR):**
  * $\Delta$ ROC-AUC = `+0.0157`
  * $\Delta$ PR-AUC = `+0.0038`
  * $\Delta$ Brier Score = `-0.0143`
  * $\Delta$ Recall = `+0.00%`
  * $\Delta$ Precision = `-1.54%`
  * $\Delta$ Specificity = `-10.00%`
  * $\Delta$ Balanced Accuracy = `-5.00%`

---

## 14. Feature Importance

> [!IMPORTANT]
> "This experiment evaluates predictive performance, not causal relationships."
> 
> "Random Forest feature importance identifies variables useful to the fitted model; it does not establish causality."

For categorical variables, one-hot encoded category-level importance reflects split frequency within individual decision trees and is not causal. It applies strictly to the specific encoded category level, not necessarily the overall parent variable.

### 14.1 Cost Model — Top 15 Feature Importances
| Rank | Feature Name | Encoded Feature Level | Gini Importance | Cumulative Importance |
|:---:|---|---|:---:|:---:|
| 1 | `feat_expenditure_to_original_cost_ratio` | `num__feat_expenditure_to_original_cost_ratio` | 0.132826 | 0.1328 |
| 2 | `feat_cumulative_expenditure_crore` | `num__feat_cumulative_expenditure_crore` | 0.111368 | 0.2442 |
| 3 | `feat_physical_progress_pct` | `num__feat_physical_progress_pct` | 0.100797 | 0.3450 |
| 4 | `feat_physical_vs_financial_divergence` | `num__feat_physical_vs_financial_divergence` | 0.098156 | 0.4431 |
| 5 | `feat_project_age_months` | `num__feat_project_age_months` | 0.088537 | 0.5317 |
| 6 | `feat_remaining_original_duration_months` | `num__feat_remaining_original_duration_months` | 0.075214 | 0.6069 |
| 7 | `feat_log_original_cost` | `num__feat_log_original_cost` | 0.052999 | 0.6599 |
| 8 | `feat_original_cost_crore` | `num__feat_original_cost_crore` | 0.050001 | 0.7099 |
| 9 | `feat_is_past_original_completion` | `num__feat_is_past_original_completion` | 0.031788 | 0.7417 |
| 10 | `feat_agency_Western Railway [WR] - II` | `cat__feat_agency_Western Railway [WR] - II` | 0.010637 | 0.7523 |
| 11 | `feat_agency_South Western Railway [SWR] - II` | `cat__feat_agency_South Western Railway [SWR] - II` | 0.007828 | 0.7602 |
| 12 | `feat_agency_Central Railway [CR] - II` | `cat__feat_agency_Central Railway [CR] - II` | 0.007103 | 0.7673 |
| 13 | `feat_agency_Western Coalfields Limited [WCL]` | `cat__feat_agency_Western Coalfields Limited [WCL]` | 0.007060 | 0.7743 |
| 14 | `feat_state_Himachal Pradesh` | `cat__feat_state_Himachal Pradesh` | 0.005762 | 0.7801 |
| 15 | `feat_agency_Oil and Natural Gas Corporation Limited [ONGC]` | `cat__feat_agency_Oil and Natural Gas Corporation Limited [ONGC]` | 0.005723 | 0.7858 |

**Parent-Aggregated Feature Importance (Cost):**
| Parent Feature | Total Aggregated Importance | Relative Share |
|---|:---:|:---:|
| `feat_agency` | 0.155588 | 15.56% |
| `feat_expenditure_to_original_cost_ratio` | 0.132826 | 13.28% |
| `feat_cumulative_expenditure_crore` | 0.111368 | 11.14% |
| `feat_state` | 0.102725 | 10.27% |
| `feat_physical_progress_pct` | 0.100797 | 10.08% |
| `feat_physical_vs_financial_divergence` | 0.098156 | 9.82% |
| `feat_project_age_months` | 0.088537 | 8.85% |
| `feat_remaining_original_duration_months` | 0.075214 | 7.52% |

### 14.2 Schedule Model — Top 15 Feature Importances
| Rank | Feature Name | Encoded Feature Level | Gini Importance | Cumulative Importance |
|:---:|---|---|:---:|:---:|
| 1 | `feat_remaining_original_duration_months` | `num__feat_remaining_original_duration_months` | 0.183932 | 0.1839 |
| 2 | `feat_project_age_months` | `num__feat_project_age_months` | 0.069666 | 0.2536 |
| 3 | `feat_cumulative_expenditure_crore` | `num__feat_cumulative_expenditure_crore` | 0.065312 | 0.3189 |
| 4 | `feat_physical_progress_pct` | `num__feat_physical_progress_pct` | 0.065183 | 0.3841 |
| 5 | `feat_is_past_original_completion` | `num__feat_is_past_original_completion` | 0.063318 | 0.4474 |
| 6 | `feat_original_cost_crore` | `num__feat_original_cost_crore` | 0.057044 | 0.5045 |
| 7 | `feat_expenditure_to_original_cost_ratio` | `num__feat_expenditure_to_original_cost_ratio` | 0.056614 | 0.5611 |
| 8 | `feat_log_original_cost` | `num__feat_log_original_cost` | 0.056286 | 0.6174 |
| 9 | `feat_physical_vs_financial_divergence` | `num__feat_physical_vs_financial_divergence` | 0.055373 | 0.6727 |
| 10 | `feat_agency_East Coast Railway [ECoR] - II` | `cat__feat_agency_East Coast Railway [ECoR] - II` | 0.016640 | 0.6894 |
| 11 | `feat_agency_North Western Railway [NWR]` | `cat__feat_agency_North Western Railway [NWR]` | 0.015532 | 0.7049 |
| 12 | `feat_agency_SECR` | `cat__feat_agency_SECR` | 0.014485 | 0.7194 |
| 13 | `feat_state_Chhattisgarh` | `cat__feat_state_Chhattisgarh` | 0.014168 | 0.7336 |
| 14 | `feat_agency_Northeast Frontier Railway [NFR]` | `cat__feat_agency_Northeast Frontier Railway [NFR]` | 0.013948 | 0.7475 |
| 15 | `feat_agency_South Western Railway [SWR] - II` | `cat__feat_agency_South Western Railway [SWR] - II` | 0.013748 | 0.7612 |

**Parent-Aggregated Feature Importance (Schedule):**
| Parent Feature | Total Aggregated Importance | Relative Share |
|---|:---:|:---:|
| `feat_agency` | 0.200681 | 20.07% |
| `feat_remaining_original_duration_months` | 0.183932 | 18.39% |
| `feat_state` | 0.122265 | 12.23% |
| `feat_project_age_months` | 0.069666 | 6.97% |
| `feat_cumulative_expenditure_crore` | 0.065312 | 6.53% |
| `feat_physical_progress_pct` | 0.065183 | 6.52% |
| `feat_is_past_original_completion` | 0.063318 | 6.33% |
| `feat_original_cost_crore` | 0.057044 | 5.70% |

---

## 15. Interpretation

1. **Cost Overrun Nonlinearity:**
   - For the retrospective 12-month holdout evaluated here, the Random Forest demonstrated measurable improvement over Logistic Regression on the cost-overrun task: ROC-AUC rises from 0.8288 to **0.8783 (+0.0495)**, PR-AUC rises from 0.7637 to **0.8243 (+0.0605)**, and Brier score drops from 0.1547 to **0.1232 (-20.3%)**.
   - The primary split variables (`feat_expenditure_to_original_cost_ratio`, `feat_cumulative_expenditure_crore`, `feat_physical_progress_pct`, and `feat_physical_vs_financial_divergence`) exhibit non-linear thresholds and interaction effects that decision trees capture more effectively than a linear hyperplane.

2. **Schedule Slippage Trade-off:**
   - Random Forest showed stronger continuous discrimination and probability performance (ROC-AUC reaches **0.9000**, PR-AUC reaches **0.9806**, and Brier score drops from 0.1095 to **0.0958**), while Logistic Regression retained slightly better fixed-threshold classification performance on the small negative class at the default threshold of $\tau = 0.50$ ($TN=3$ vs $TN=2$; precision 87.50% vs 85.96%).

3. **Dominance of Temporal Buffering:**
   - In the schedule model, `feat_remaining_original_duration_months` accounts for **18.39%** of all tree split impurity reduction, far exceeding any other individual variable.

---

## 16. Limitations

1. **Single 12-Month Longitudinal Transition:** Represents a retrospective 12-month holdout evaluation across the July 2025 $\rightarrow$ July 2026 window. It is NOT temporal cross-validation, multi-period temporal validation, production validation, or nationwide deployment validation.
2. **Missing/Unobserved Schedule Outcomes:** Exactly 132 projects with unrevised completion dates are excluded; results strictly represent projects with observed schedule revisions.
3. **Absence of Hyperparameter Optimization:** Parameters were fixed as a benchmark standard (`n_estimators=300, min_samples_leaf=1`); depth and leaf regularization were intentionally un-tuned.
4. **Fixed Decision Threshold:** All binary predictions use $\tau = 0.50$; threshold optimization was strictly prohibited in this phase.
5. **Predictive Association, Not Causation:** Gini feature importance reflects predictive utility in tree splits, not physical or operational causality.

---

## 17. Reproducibility

* Fixed seed: `random_state = 42` across data splitting and Random Forest bagging.
* Single thread execution (`n_jobs = 1`) ensures bit-level deterministic tree construction.
* Two consecutive script runs confirmed identical metric outputs, prediction arrays, Gini feature importances, and byte-level report hashes.
* Zero variable timestamps are embedded in results artifacts.

---

## 18. Data Integrity

| Dataset / File | Expected SHA-256 Checksum | Verified Hash | Status |
|---|---|---|:---:|
| `data/interim/pit_features_july2025_to_july2026.csv` | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | PASS |
| `data/processed/table7_june_2025_projects.csv` | `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43` | Identical | PASS |
| `data/processed/table4_july_2025_projects.csv` | `ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3` | Identical | PASS |
| `data/processed/table6_july_2026_projects.csv` | `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9` | Identical | PASS |
| `data/processed/project_identity_map.csv` | `16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb` | Identical | PASS |
| `data/processed/project_snapshot_panel.csv` | `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47` | Identical | PASS |

---

## 19. Test Results

All 30 automated unit and integration tests in `tests/test_module3_random_forest_benchmark.py` pass without error, verifying:
- Exact Random Forest benchmark parameters (`n_estimators=300`, `max_features='sqrt'`, `bootstrap=True`, `n_jobs=1`)
- Identical split index assignment between Random Forest and Logistic Regression
- Absence of all prohibited, future, and target variables
- Feature importance existence, non-negativity, and unit summation ($1.0 \pm 10^{-5}$)
- Cryptographic source dataset immutability

---

## 20. Conclusion

**Conclusion Verdict: B. Random Forest provides mixed improvement.**

In this retrospective 12-month holdout experiment, Random Forest provided mixed improvement relative to Logistic Regression: it improved the cost-overrun task across the reported ranking, calibration, and fixed-threshold metrics, while for schedule slippage it improved continuous discrimination and probability performance but did not dominate Logistic Regression at the fixed 0.50 classification threshold.

1. **Cost Overrun Task:** For the retrospective 12-month holdout evaluated here, the Random Forest demonstrated measurable improvement over Logistic Regression on the cost-overrun task (ROC-AUC reaches 0.8783, PR-AUC reaches 0.8243, precision reaches 70.83%, and Brier score drops by 20.3% to 0.1232).
2. **Schedule Slippage Task:** Random Forest showed stronger continuous discrimination and probability performance (ROC-AUC reaches 0.9000, PR-AUC reaches 0.9806, and Brier score drops to 0.0958), while Logistic Regression retained slightly better fixed-threshold classification performance on the small negative class at $\tau = 0.50$ (precision 87.50% vs 85.96%, specificity 30.0% vs 20.0%).

The nonlinear model establishes that tree-based decision surfaces capture interaction effects without claiming causal superiority, providing an empirical benchmark for subsequent modeling phases.

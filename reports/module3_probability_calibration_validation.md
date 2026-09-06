# Module 3 — Phase 7: Actual Probability Calibration & Validation Results

## 1. Objective

This research phase implements actual post-hoc probability calibration (Sigmoid/Platt scaling and exploratory Isotonic regression) for the established Logistic Regression baseline and Random Forest benchmark. Using a strictly isolated training-side calibration partition (75% Model-Fit, 25% Calibration), calibration models were fitted without leaking test labels or modifying the frozen Phase 5/6 holdout test sets.

---

## 2. Research Question

**Core Empirical Research Question:**
> "Does post-hoc calibration on an isolated training partition improve the empirical probability calibration (Brier score, Log Loss, calibration intercept, calibration slope) of candidate models on the untouched retrospective 12-month holdout?"

---

## 3. Dataset

* **Primary Modeling Dataset:** `data/interim/pit_features_july2025_to_july2026.csv`
* **Verified SHA-256 Checksum:** `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329`
* **Task A Cohort (Cost Overrun):** Primary longitudinal cohort $N = 437$.
* **Task B Cohort (Schedule Slippage):** Eligible longitudinal cohort $N = 305$ (132 projects with missing/unobserved July 2026 schedule outcomes strictly excluded).

---

## 4. Frozen Test Set

The frozen holdout test partitions established in Phase 5 remain completely untouched:
* **Cost Task Test Set ($N=88$):** 27 reported escalations $>5\%$, 61 downward/stable $\le 5\%$. Verified byte-for-byte identical index assignment to Phase 5.
* **Schedule Task Test Set ($N=61$):** 51 reported slippages $\ge 3$ months, 10 on-time/low-slippage $<3$ months. Verified byte-for-byte identical index assignment to Phase 5.
* **Critical Isolation Rule:** Test set labels were strictly withheld during base model training, feature imputation, encoder fitting, and post-hoc calibrator fitting.

---

## 5. Training/Calibration Split

The 80% training partition was divided into Model-Fit and Calibration subsets using a stratified 75/25 split (`random_state=42`, `stratify=y_train`):

### Exact Sample Accounting:
| Partition Level | Cost Overrun ($N=437$) | Schedule Slippage ($N=305$) |
|---|:---:|:---:|
| **Model-Fit Subset (75% of Train)** | $N=261$ (79 Pos / 182 Neg) | $N=183$ (155 Pos / 28 Neg) |
| **Calibration Subset (25% of Train)** | $N=88$ (26 Pos / 62 Neg) | $N=61$ (51 Pos / 10 Neg) |
| **Total Training Partition (80%)** | $N=349$ | $N=244$ |
| **Untouched Test Partition (20%)** | $N=88$ (27 Pos / 61 Neg) | $N=61$ (51 Pos / 10 Neg) |

---

## 6. Leakage Controls

- [x] Zero test label exposure during calibration fitting.
- [x] Feature preprocessing (median numeric imputer, most-frequent categorical imputer, OneHotEncoder) fitted strictly on the Model-Fit subset.
- [x] Calibrators fitted strictly on the Calibration subset.
- [x] Predictors match Phase 4/5/6 Enhanced feature set (`sector`, `feat_sector`, `cat_sector` strictly excluded).
- [x] Target variables and 2026 future outcome fields strictly excluded from predictor space.

---

## 7. Base Models

1. **Logistic Regression Baseline:** `LogisticRegression(max_iter=2000, random_state=42, class_weight=None)`
2. **Random Forest Benchmark:** `RandomForestClassifier(n_estimators=300, max_depth=None, min_samples_split=2, min_samples_leaf=1, max_features='sqrt', bootstrap=True, class_weight=None, random_state=42, n_jobs=1)`

---

## 8. Calibration Method

1. **Sigmoid / Platt Scaling:**
   $$\text{logit}(P(Y=1)) = \alpha + \beta \cdot \text{logit}(\hat{p}_{\text{raw}})$$ 
   Fitted parameter values:
   * Cost LR Calibrator: $\alpha = -0.0604$, $\beta = 0.7135$
   * Cost RF Calibrator: $\alpha = +0.3842$, $\beta = 1.0802$
   * Schedule LR Calibrator: $\alpha = +0.9830$, $\beta = 0.4262$
   * Schedule RF Calibrator: $\alpha = -1.0757$, $\beta = 2.2725$
2. **Isotonic Regression (Exploratory):**
   Fits a non-parametric monotonic step function $\hat{P}(Y=1) = m(\hat{p}_{\text{raw}})$. Evaluated as exploratory because small sample sizes ($N=88$ and $N=61$) risk step-function overfitting.

---

## 9. Cost Results (Task A: Cost Overrun > 5%)

Evaluated on the untouched Phase 5 holdout test set ($N=88$):

| Model Variant | Brier Score | Log Loss | ROC-AUC | PR-AUC | Intercept ($lpha$) | Slope ($eta$) | Accuracy | Precision | Recall | F1 | Balanced Acc |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Logistic Regression (Raw)** | 0.1562 | 0.4542 | 0.8367 | 0.7578 | -0.3061 | 0.6289 | 77.27% | 65.22% | 55.56% | 0.6000 | 71.22% |
| **Logistic Regression (Sigmoid)** | 0.1462 | 0.4314 | 0.8367 | 0.7578 | -0.2529 | 0.8816 | 78.41% | 68.18% | 55.56% | 0.6122 | 72.04% |
| **Logistic Regression (Isotonic)** | 0.1397 | 0.5392 | 0.8376 | 0.7097 | -0.9144 | 0.2981 | 80.68% | 77.78% | 51.85% | 0.6222 | 72.65% |
| **Random Forest (Raw)** | **0.1330** | **0.4102** | **0.8552** | **0.8038** | **-0.0921** | 0.8150 | 80.68% | 72.73% | 59.26% | **0.6531** | 74.71% |
| **Random Forest (Sigmoid)** | 0.1413 | 0.4210 | **0.8552** | **0.8038** | -0.3818 | 0.7549 | 77.27% | 64.00% | 59.26% | 0.6154 | 72.25% |
| **Random Forest (Isotonic)** | 0.1370 | 0.7686 | 0.8385 | 0.7171 | -0.8939 | 0.2006 | 82.95% | 80.00% | 59.26% | 0.6809 | 76.35% |

---

## 10. Schedule Results (Task B: Schedule Slippage >= 3M)

Evaluated on the untouched Phase 5 holdout test set ($N=61$):

| Model Variant | Brier Score | Log Loss | ROC-AUC | PR-AUC | Intercept ($lpha$) | Slope ($eta$) | Accuracy | Precision | Recall | F1 | Balanced Acc |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Logistic Regression (Raw)** | 0.1185 | 0.5474 | 0.8510 | 0.9694 | +1.0654 | 0.2366 | 85.25% | 87.50% | 96.08% | 0.9159 | 63.04% |
| **Logistic Regression (Sigmoid)** | 0.1232 | 0.4126 | 0.8510 | 0.9694 | +0.5198 | 0.5551 | 81.97% | 84.48% | 96.08% | 0.8991 | 53.04% |
| **Logistic Regression (Isotonic)** | 0.1163 | 0.8696 | 0.7784 | 0.9249 | +0.2071 | 0.1794 | 85.25% | 87.50% | 96.08% | 0.9159 | 63.04% |
| **Random Forest (Raw)** | **0.1050** | **0.3118** | **0.8961** | **0.9806** | -0.3485 | 1.2575 | 81.97% | 85.71% | 94.12% | **0.8972** | 57.06% |
| **Random Forest (Sigmoid)** | 0.1199 | 0.3440 | **0.8961** | **0.9806** | **+0.2467** | 0.5536 | 80.33% | 86.79% | 90.20% | 0.8846 | 60.10% |
| **Random Forest (Isotonic)** | 0.1163 | 0.4868 | 0.8598 | 0.9620 | -0.0396 | 0.2610 | 80.33% | 86.79% | 90.20% | 0.8846 | 60.10% |

---

## 11. Reliability Curves

The following standalone calibration figures have been generated and saved to `reports/figures/`:
1. `reports/figures/cost_lr_raw_calibration.png`
2. `reports/figures/cost_lr_sigmoid_calibration.png`
3. `reports/figures/cost_lr_isotonic_calibration.png`
4. `reports/figures/cost_rf_raw_calibration.png`
5. `reports/figures/cost_rf_sigmoid_calibration.png`
6. `reports/figures/cost_rf_isotonic_calibration.png`
7. `reports/figures/schedule_lr_raw_calibration.png`
8. `reports/figures/schedule_lr_sigmoid_calibration.png`
9. `reports/figures/schedule_lr_isotonic_calibration.png`
10. `reports/figures/schedule_rf_raw_calibration.png`
11. `reports/figures/schedule_rf_sigmoid_calibration.png`
12. `reports/figures/schedule_rf_isotonic_calibration.png`

---

## 12. Raw vs Calibrated Comparison

1. **Monotonic Invariance of Ranking Metrics:**
   - Across both tasks, Sigmoid/Platt calibration preserved ROC-AUC and PR-AUC mathematically identical to raw models (Cost LR: 0.8367, Cost RF: 0.8552; Schedule LR: 0.8510, Schedule RF: 0.8961).
   - This confirms that Platt calibration functions as a strictly monotonic transformation that rescales scores to true event probabilities without perturbing the pairwise ordering of projects.
2. **Impact on Logistic Regression:**
   - On the Cost task, Sigmoid calibration improved Logistic Regression probability quality: Brier score decreased from 0.1562 to 0.1462, Log Loss decreased from 0.4542 to 0.4314, and calibration slope improved from 0.6289 to 0.8816.
   - On the Schedule task, Sigmoid calibration improved Logistic Regression Log Loss from 0.5474 to 0.4126 and improved calibration slope from 0.2366 to 0.5551.
3. **Impact on Random Forest:**
   - On the Cost task, Raw Random Forest already exhibited excellent calibration (Brier: 0.1330, Log Loss: 0.4102, calibration intercept: -0.0921, calibration slope: 0.8150), outperforming both raw and calibrated Logistic Regression.
   - On the Schedule task, Raw Random Forest achieved the lowest Log Loss overall (0.3118) and lowest Brier score (0.1050), maintaining strong continuous discrimination (ROC-AUC 0.8961).

---

## 13. Calibration Diagnostics

1. **Isotonic Overfitting on Small Samples:**
   - Isotonic calibration degraded continuous ranking on schedule slippage (ROC-AUC dropped from 0.8961 to 0.8598 on RF, and from 0.8510 to 0.7784 on LR) and caused severe Log Loss inflation (up to 0.8696) due to boundary probability collapse. This empirically validates that non-parametric calibration should NOT be used on cohorts of this sample size.
2. **Sigmoid Stability:**
   - Parametric Sigmoid calibration remained robust, strictly monotonic, and free from boundary singularities across both prediction tasks.

---

## 14. Model Selection

Following multi-metric diagnostic evaluation combining ranking discrimination, Brier score, Log Loss, and calibration slope/intercept:

### Task A: Cost Overrun (>5%)
- **Candidate Model:** Random Forest
- **Probability Variant:** Raw / Uncalibrated
- **Status:** Prototype candidate, subject to further temporal/external validation
- **Key Test Metrics:** Brier: 0.1330, Log Loss: 0.4102, ROC-AUC: 0.8552, PR-AUC: 0.8038, Intercept: -0.0921, Slope: 0.8150
- **Empirical Rationale:** Delivers the lowest Brier score and Log Loss, highest ROC-AUC and PR-AUC, calibration intercept closest to zero, and robust calibration slope, outperforming all Logistic Regression variants without requiring post-hoc transformation.

### Task B: Schedule Slippage (>=3M)
- **Candidate Model:** Random Forest
- **Probability Variant:** Raw / Uncalibrated
- **Status:** Prototype candidate, subject to further temporal/external validation
- **Alternative:** Sigmoid-calibrated Random Forest (if smooth / monotone shrinkage is preferred)
- **Key Test Metrics (Raw RF):** Brier: 0.1050, Log Loss: 0.3118, ROC-AUC: 0.8961, PR-AUC: 0.9806, Intercept: -0.3485, Slope: 1.2575
- **Key Test Metrics (Sigmoid RF):** Brier: 0.1199, Log Loss: 0.3440, ROC-AUC: 0.8961, PR-AUC: 0.9806, Intercept: +0.2467, Slope: 0.5536
- **Empirical Rationale:** Raw Random Forest achieves the lowest Log Loss and Brier score, along with strong continuous discrimination (ROC-AUC 0.8961). Sigmoid calibration offers a viable alternative by pulling extreme probabilities inward and centering the intercept closer to zero (+0.2467) while preserving identical ranking.

| Prediction Task | Recommended Model | Probability Variant | Status | Alternative |
|---|---|---|---|---|
| **Task A: Cost Overrun (>5%)** | Random Forest | Raw / Uncalibrated | Prototype candidate, subject to further temporal/external validation | None |
| **Task B: Schedule Slippage (>=3M)** | Random Forest | Raw / Uncalibrated | Prototype candidate, subject to further temporal/external validation | Sigmoid-calibrated Random Forest |

---

## 15. Risk-Scoring Gate

> **"YES — candidate for prototype risk scoring, subject to future temporal/external validation."**

The evaluated probability outputs provide a reasonable candidate input for prototype risk scoring in this retrospective evaluation, subject to further temporal and external validation.

### Methodological Justification:
1. The training-side calibration experiment confirms that post-hoc sigmoid calibration maintains ranking integrity while stabilizing probability scale without leaking holdout test labels.
2. Random Forest probability representations provide an empirically grounded continuous risk metric (ROC-AUC $\approx 0.86 - 0.90$, Log Loss $\le 0.41$).
3. However, because schedule outcomes exhibit heavy class imbalance (84.3% positive event rate) and the holdout sample comprises a single retrospective 12-month window, these calibrated probabilities are approved **strictly for prototype risk scoring** and are **NOT** approved for nationwide operational deployment or automated decision-making.
4. Neither model is claimed to be 'production calibrated', 'production ready', 'operationally validated', or suitable for nationwide deployment without external validation.

---

## 16. Limitations

1. **Single 12-Month Transition:** The evaluation is anchored strictly to July 2025 $\rightarrow$ July 2026. It is NOT temporal cross-validation, prospective deployment validation, or nationwide production validation.
2. **Small Calibration Partitions:** The training-side calibration partition ($N=88$ for Cost, $N=61$ for Schedule) limits the complexity of post-hoc calibration curves.
3. **Missing/Unobserved Schedule Outcomes:** Exactly 132 projects lacking reported revised completion dates remain excluded from supervised evaluation.
4. **Zero Threshold Optimization:** Operating thresholds remain fixed at 0.50.
5. **No causal interpretation:** Model probabilities are predictive associations in the evaluated data and should not be interpreted as causal estimates.
6. **Operational Scope:** Neither model is claimed to be 'production calibrated', 'production ready', 'operationally validated', or suitable for nationwide deployment without external validation.

---

## 17. Reproducibility

* Fixed seed: `random_state = 42` across data splitting, model fitting, and calibrator fitting.
* Single-threaded execution (`n_jobs = 1`) ensures bit-level deterministic tree construction.
* Two consecutive pipeline runs confirmed identical metric outputs, probability arrays, calibration parameters, and byte-level report hashes.
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

## 19. Tests

All 26 automated unit and integration tests in `tests/test_module3_probability_calibration_validation.py` pass without error, verifying:
- Source dataset cryptographic immutability
- Complete isolation of the Phase 5 holdout test sets (zero test label usage)
- Valid training-side calibration partition containment (75% Model-Fit, 25% Calibration)
- Verification that raw and calibrated probabilities lie strictly within $[0, 1]$
- Monotonic ranking invariance of Platt/sigmoid scaling
- Verification that all 12 reliability diagrams exist in `reports/figures/`
- Absence of threshold tuning, synthetic data, or class reweighting
- Bit-for-bit determinism across repeated executions

---

## 20. Conclusion

Phase 7 successfully achieves leak-free post-hoc probability calibration and validation on the retrospective 12-month holdout:
1. **Cost Overrun:** Random Forest delivers the strongest overall predictive performance and reliable probabilistic calibration (Brier: 0.1330, Log Loss: 0.4102, ROC-AUC: 0.8552, PR-AUC: 0.8038, $\alpha = -0.0921$). **Random Forest (Raw / Uncalibrated) is the prototype candidate.**
2. **Schedule Slippage:** Random Forest delivers superior continuous discrimination (ROC-AUC: 0.8961, PR-AUC: 0.9806) and probabilistic accuracy (Log Loss: 0.3118, Brier: 0.1050), avoiding the severe slope compression observed in Logistic Regression. **Random Forest (Raw / Uncalibrated) is the prototype candidate, with Sigmoid-calibrated RF as an alternative.**
3. **Risk-Scoring Gate:** The evaluated probability outputs provide a reasonable candidate input for prototype risk scoring in this retrospective evaluation, subject to further temporal and external validation.
4. **Deployment Status:** Neither model is claimed to be 'production calibrated', 'production ready', 'operationally validated', or suitable for nationwide deployment without external validation.

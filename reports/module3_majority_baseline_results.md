# Module 3 — Empirical Majority-Class Baseline Results

**Project:** SIH26103 — Web-Based Integrated Project Monitoring Platform  
**Product:** PAIMANA Predictive Risk Intelligence  
**Module:** 3 — Baseline Predictive Modeling (Phase 2: Empirical Majority-Class Baselines)  
**Report File:** `reports/module3_majority_baseline_results.md`  
**Governing Inputs:**
* `data/interim/pit_features_july2025_to_july2026.csv`
* SHA-256: `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329`
* `docs/module3_evaluation_protocol.md`  
**Status:** **BENCHMARKS ESTABLISHED — DETERMINISTIC ZERO-SKILL BASELINES VERIFIED**  

---

## 1. Executive Summary & Benchmark Role

This report documents the exact empirical performance of the naive majority-class baselines for both prospective prediction tasks.

> [!IMPORTANT]
> **The majority-class baseline is a benchmark, not a predictive model.**  
> It establishes the minimum mathematical performance floor that any future machine learning model (e.g., Logistic Regression, Random Forest, Gradient Boosted Trees) must unequivocally surpass.  
> **No machine learning model was trained in this phase.**

---

## 2. Dataset Identity & Cryptographic Lineage

| Attribute | Verified Value | Verification Status |
|---|---|:---:|
| **Dataset Path** | `data/interim/pit_features_july2025_to_july2026.csv` | PASS |
| **Cryptographic Hash (SHA-256)** | `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329` | PASS |
| **Total Record Count ($N$)** | 437 | PASS |
| **Schema Dimension** | 26 columns | PASS |
| **Cutoff Snapshot Date** | July 31, 2025 | PASS |
| **Observed Outcome Horizon** | July 31, 2026 (12 months forward) | PASS |
| **Source Data Immutability** | Byte-for-byte unchanged | PASS |

---

## 3. Target Distribution Accounting

### 3.1 Task A — Cost Overrun (`cost_overrun_5pct_2026`)
* **Total Longitudinal Projects ($N$):** 437
* **Eligible Cohort (`is_eligible_cost_target == 1`):** 437 (100.0%)
* **Missing Outcomes:** 0 (0.0%)
* **Class 0 (Cost Escalation $\le 5\%$):** 305 projects (69.79%)
* **Class 1 (Cost Escalation $> 5\%$):** 132 projects (30.21%)
* **Empirical Majority Class:** **Class 0**
* **Class Imbalance Ratio (Neg:Pos):** 2.31 : 1

### 3.2 Task B — Schedule Slippage (`time_overrun_3m_2026`)
* **Total Longitudinal Projects ($N$):** 437
* **Eligible Cohort (`is_eligible_schedule_target == 1`):** 305 (69.79%)
* **Censored / Missing Outcomes (`is_eligible_schedule_target == 0`):** 132 (30.21%)
  *(Projects with unrevised completion dates `-` in July 2026; strictly excluded from supervised evaluation)*
* **Class 0 (Slippage $< 3.0$ months):** 48 projects (15.74% of eligible)
* **Class 1 (Slippage $\ge 3.0$ months):** 257 projects (84.26% of eligible)
* **Empirical Majority Class:** **Class 1**
* **Class Imbalance Ratio (Pos:Neg):** 5.35 : 1

---

## 4. Empirical Benchmark Performance

### 4.1 Cost Majority Baseline Results (Always Predict Class 0)
* **Decision Rule:** Predict $\hat{y} = 0$ and $P(\text{class}=1) = 0.0$ for all 437 projects.
* **Confusion Matrix:**
  $$\begin{bmatrix} TN & FP \\ FN & TP \end{bmatrix} = \begin{bmatrix} 305 & 0 \\ 132 & 0 \end{bmatrix}$$
  * True Negatives ($TN$): **305**
  * False Positives ($FP$): **0**
  * False Negatives ($FN$): **132**
  * True Positives ($TP$): **0**

| Metric | Empirical Value | Exact Formula / Note |
|---|:---:|---|
| **Accuracy** | **69.7941%** | $\frac{305}{437}$ |
| **Precision** | **0.0000%** | $\frac{0}{0}$ (Zero division handled as 0.0) |
| **Recall (Sensitivity)** | **0.0000%** | $\frac{0}{132}$ (Fails to detect any overrun) |
| **Specificity** | **100.0000%** | $\frac{305}{305}$ |
| **F1-Score** | **0.0000** | Harmonic mean of 0 precision and 0 recall |
| **Balanced Accuracy** | **50.0000%** | $\frac{0.0 + 1.0}{2}$ (Equivalent to pure chance) |
| **ROC-AUC** | **0.5000** | Non-discriminative reference (constant probability score) |
| **PR-AUC (Average Precision)**| **0.3021** | Equals empirical positive base rate ($\frac{132}{437}$) |
| **Brier Score** | **0.3021** | Mean squared probability error $\frac{1}{437}\sum(0 - y_i)^2 = \frac{132}{437}$ |

---

### 4.2 Schedule Majority Baseline Results (Always Predict Class 1 on Eligible Cohort)
* **Decision Rule:** Predict $\hat{y} = 1$ and $P(\text{class}=1) = 1.0$ for all 305 eligible projects.
* **Confusion Matrix:**
  $$\begin{bmatrix} TN & FP \\ FN & TP \end{bmatrix} = \begin{bmatrix} 0 & 48 \\ 0 & 257 \end{bmatrix}$$
  * True Negatives ($TN$): **0**
  * False Positives ($FP$): **48**
  * False Negatives ($FN$): **0**
  * True Positives ($TP$): **257**

| Metric | Empirical Value | Exact Formula / Note |
|---|:---:|---|
| **Accuracy** | **84.2623%** | $\frac{257}{305}$ |
| **Precision** | **84.2623%** | $\frac{257}{257 + 48} = \frac{257}{305}$ |
| **Recall (Sensitivity)** | **100.0000%** | $\frac{257}{257}$ (Trivially flags all delayed projects) |
| **Specificity** | **0.0000%** | $\frac{0}{48}$ (Fails to identify any on-time project) |
| **F1-Score** | **0.9146** | $\frac{2 \times (257/305) \times 1.0}{(257/305) + 1.0} = \frac{514}{562} = \frac{257}{281} \approx 0.914591$ |
| **Balanced Accuracy** | **50.0000%** | $\frac{1.0 + 0.0}{2}$ (Equivalent to pure chance) |
| **ROC-AUC** | **0.5000** | Non-discriminative reference (constant probability score) |
| **PR-AUC (Average Precision)**| **0.8426** | Equals empirical positive base rate ($\frac{257}{305}$) |
| **Brier Score** | **0.1574** | Mean squared probability error $\frac{1}{305}\sum(1 - y_i)^2 = \frac{48}{305}$ |

---

## 5. Metric Interpretation & Why Accuracy Is Insufficient

The empirical baseline results provide definitive mathematical proof for the governing evaluation principles established in Module 3 Phase 1:

1. **The Illusion of Accuracy in Imbalanced Regimes:**
   "The schedule majority baseline achieves 84.26% accuracy while providing no discriminatory capability. Therefore future schedule models must be evaluated primarily using PR-AUC, recall, precision, F1, balanced accuracy and confusion matrices rather than accuracy alone."

2. **Complete Specificity Blindness:**
   A majority predictor for schedule achieves $100\%$ recall and $84.26\%$ accuracy while misclassifying every single on-time project ($Specificity = 0\%$, $TN = 0$). For infrastructure project oversight, such a model is functionally useless because it generates false alarms on every well-performing project and provides no prioritization signal.

3. **Balanced Accuracy Penalizes Trivial Heuristics:**
   For both tasks, Balanced Accuracy is exactly **$50.00\%$** ($\frac{0\% + 100\%}{2}$), directly exposing that the majority predictor possesses zero skill beyond random assignment.

4. **Reference Floor for Discriminatory Metrics:**
   - **ROC-AUC = 0.5000**: Any predictive model with $\text{ROC-AUC} \le 0.50$ performs no better than a coin flip or constant predictor.
   - **PR-AUC = Base Rate**: A machine learning model must achieve $\text{PR-AUC} > 0.3021$ on cost and $\text{PR-AUC} > 0.8426$ on schedule to demonstrate non-trivial precision-recall trade-offs.

---

## 6. Benchmark Requirements for Future ML Models

Future predictive models (beginning with Regularized Logistic Regression in subsequent phases) must satisfy the following minimum hurdle requirements:

| Target Task | Evaluation Metric | Majority Benchmark Floor | Future Model Hurdle Requirement |
|---|---|:---:|:---:|
| **Cost Overrun** | **ROC-AUC** | 0.5000 | **$\ge 0.6500$** |
| | **PR-AUC** | 0.3021 | **$> 0.4000$** |
| | **Balanced Accuracy** | 0.5000 | **$> 0.6000$** |
| | **Recall (Positives)** | 0.0000 | **$> 0.4000$** |
| **Schedule Slippage**| **Balanced Accuracy** | 0.5000 | **$> 0.6000$** |
| | **PR-AUC** | 0.8426 | **$> 0.8800$** |
| | **Specificity (On-Time)**| 0.0000 | **$> 0.3000$** |
| | **Confusion Matrix** | $TN = 0$ | **$TN \ge 15$** (Demonstrable non-zero specificity) |

---

## 7. Operational Integrity & Verification Sign-Off

- [x] Input dataset path and SHA-256 confirmed.
- [x] Cost target distribution confirmed ($N=437$, 132 positive, 305 negative).
- [x] Schedule target eligibility confirmed ($N=437$, 305 eligible, 132 censored/missing, 257 positive, 48 negative).
- [x] Exact confusion matrices verified: Cost `[[305, 0], [132, 0]]`, Schedule `[[0, 48], [0, 257]]`.
- [x] All benchmark formulas verified without rounding discrepancies.
- [x] Verified zero modifications to source datasets.
- [x] Verified zero machine learning models trained; zero predictions generated; zero splits committed.

**Final Phase 2 Status:** **BENCHMARKS FROZEN AND APPROVED FOR COMPARATIVE MODELING**
